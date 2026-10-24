#include "Gameplay/EncounterEvent.h"
#include "Gameplay/EncounterTrigger.h"
#include "Enemies/BarkSubsystem.h"
#include "Enemies/EnemyBase.h"
#include "ProjectBopisCharacter.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/AudioComponent.h"
#include "Components/BillboardComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "DrawDebugHelpers.h"
#include "EngineUtils.h"
#include "Engine/Texture2D.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

AEncounterEvent::AEncounterEvent()
{
	// Ticks in the editor for its link lines, and in play only while it runs.
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(Root);
	Label->SetRelativeLocation(FVector(0.0f, 0.0f, 80.0f));
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(24.0f);
	Label->SetTextRenderColor(FColor(220, 80, 255));
	Label->SetHiddenInGame(true);
	Label->bIsEditorOnly = true;

#if WITH_EDITORONLY_DATA
	Icon = CreateEditorOnlyDefaultSubobject<UBillboardComponent>(TEXT("Icon"));
	if (Icon)
	{
		static ConstructorHelpers::FObjectFinderOptional<UTexture2D> NoteSprite(TEXT("/Engine/EditorResources/S_Note"));
		Icon->Sprite = NoteSprite.Get();
		Icon->SetupAttachment(Root);
	}
#endif
}

void AEncounterEvent::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

#if WITH_EDITOR
	int32 Lines = 0;
	for (const FEncounterEventStep& Step : Steps)
	{
		Lines += Step.Type == EEncounterStepType::SayLine ? 1 : 0;
	}
	Label->SetText(FText::FromString(FString::Printf(TEXT("EVENT\n%s\n%d steps, %d lines"),
		*GetActorLabel(), Steps.Num(), Lines)));
#endif
}

void AEncounterEvent::BeginPlay()
{
	Super::BeginPlay();

	SetActorTickEnabled(false);
	if (bStartOnBeginPlay)
	{
		StartEvent();
	}
}

bool AEncounterEvent::HasSpeaker(EEncounterStepType Type)
{
	return Type == EEncounterStepType::SayLine || Type == EEncounterStepType::PlayAnim
		|| Type == EEncounterStepType::MoveTo || Type == EEncounterStepType::FaceTo;
}

void AEncounterEvent::StartEvent()
{
	if (bRunning || bDone)
	{
		return;
	}

	// Everyone it can find now; spawned speakers that come later join as their steps come up.
	Speakers.Reset();
	for (const FEncounterEventStep& Step : Steps)
	{
		if (HasSpeaker(Step.Type))
		{
			if (AEnemyBase* Speaker = FindSpeaker(Step))
			{
				Speakers.AddUnique(Speaker);
			}
		}
	}

	bRunning = true;
	bSetOff = false;
	StepIndex = -1;
	SetActorTickEnabled(true);
	RunNextStep();
}

void AEncounterEvent::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const UWorld* World = GetWorld();
#if WITH_EDITOR
	if (World && World->WorldType == EWorldType::Editor)
	{
		if (bDrawLinks)
		{
			DrawLinks();
		}
		return;
	}
#endif

	if (!bRunning)
	{
		return;
	}

	// Anyone in it noticing the player (or being shot, or killed) ends it on the spot — unless
	// it set the fight off itself, in which case that's how it was meant to end.
	for (const TWeakObjectPtr<AEnemyBase>& Speaker : Speakers)
	{
		if (Speaker.IsValid() && (Speaker->IsDead() || Speaker->IsAlerted()))
		{
			if (bSetOff)
			{
				Finish();
			}
			else
			{
				Interrupt(Speaker->IsDead() ? nullptr : Speaker.Get());
			}
			return;
		}
	}

	// Waiting on a walk: the clock starts when he gets there.
	if (MovingSpeaker.IsValid())
	{
		if (!MovingSpeaker->IsScriptedMoveDone())
		{
			return;
		}
		MovingSpeaker.Reset();
		StepTimeLeft = MovePauseAfter;
	}

	StepTimeLeft -= DeltaSeconds;
	if (StepTimeLeft <= 0.0f)
	{
		RunNextStep();
	}
}

void AEncounterEvent::RunNextStep()
{
	// The last line's animation ends with it.
	StopLineAnim();

	// Skipped steps (a dead speaker) and instant ones (facing, starting things) fall straight
	// through to the next.
	while (++StepIndex < Steps.Num())
	{
		const FEncounterEventStep& Step = Steps[StepIndex];
		switch (Step.Type)
		{
		case EEncounterStepType::Wait:
			StepTimeLeft = Step.Duration;
			return;

		case EEncounterStepType::SetOffEncounter:
			if (Step.Encounter)
			{
				bSetOff = true;
				Step.Encounter->Fire();
			}
			continue;

		case EEncounterStepType::StartEvent:
			if (Step.Event && Step.Event != this)
			{
				Step.Event->StartEvent();
			}
			continue;

		default:
			break;
		}

		AEnemyBase* Speaker = FindSpeaker(Step);
		if (!Speaker || Speaker->IsDead())
		{
			continue;
		}
		Speakers.AddUnique(Speaker);

		if (Step.Type == EEncounterStepType::FaceTo)
		{
			// Turns while whatever's next plays out.
			AActor* Face = Step.Target ? Step.Target.Get() : FindTagged(Step.TargetTag);
			Speaker->SetFaceTarget(Face != Speaker ? Face : nullptr);
			continue;
		}

		if (Step.Type == EEncounterStepType::MoveTo)
		{
			if (!Speaker->ScriptedMoveTo(Step.Target, Step.bRun, Step.AcceptanceRadius) || !Step.bWaitForArrival)
			{
				continue;
			}
			MovingSpeaker = Speaker;
			MovePauseAfter = Step.PauseAfter;
			return;
		}

		if (Step.Type == EEncounterStepType::PlayAnim)
		{
			// Not waited on: runs alongside whatever comes next. A set Duration loops it that long.
			const bool bLoop = Step.bWaitForAnim && Step.Duration > 0.0f;
			const float Length = Step.Animation ? PlayStepAnim(Speaker, Step.Animation, bLoop) : 0.0f;
			if (!Step.bWaitForAnim)
			{
				continue;
			}
			StepTimeLeft = (Step.Duration > 0.0f ? Step.Duration : Length) + Step.PauseAfter;
			return;
		}

		// How long it takes: as set, else the voice's length, else a reading time.
		float Seconds = Step.Duration;
		if (Seconds <= 0.0f)
		{
			Seconds = Step.Sound ? Step.Sound->GetDuration()
				: 1.0f + 0.06f * Step.Subtitle.ToString().Len();
		}
		Say(Speaker, Step.Sound, Step.SpeakerName, Step.Subtitle, Seconds);
		if (Step.Animation)
		{
			PlayStepAnim(Speaker, Step.Animation, true);
		}
		StepTimeLeft = Seconds + Step.PauseAfter;
		return;
	}

	// Ran to the end.
	Finish();
}

void AEncounterEvent::Finish()
{
	EndRun();
	for (AEncounterEvent* Next : EventsOnFinished)
	{
		if (Next && Next != this)
		{
			Next->StartEvent();
		}
	}
}

void AEncounterEvent::Interrupt(AEnemyBase* Noticed)
{
	EndRun();

	if (CurrentVoice)
	{
		CurrentVoice->FadeOut(0.1f, 0.0f);
		CurrentVoice = nullptr;
	}
	if (AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(UGameplayStatics::GetPlayerPawn(this, 0)))
	{
		Player->ShowSubtitle(FText::GetEmpty(), 0.0f);
	}

	// The one who noticed reacts: the event's own line, else his Spotted bark.
	if (Noticed)
	{
		if (InterruptSound || !InterruptSubtitle.IsEmpty())
		{
			const float Seconds = InterruptSound ? InterruptSound->GetDuration()
				: 1.0f + 0.06f * InterruptSubtitle.ToString().Len();
			Say(Noticed, InterruptSound, FText::GetEmpty(), InterruptSubtitle, Seconds);
		}
		else
		{
			Noticed->Bark(EBarkType::Spotted);
		}
	}

	for (AEncounterEvent* Next : EventsOnInterrupted)
	{
		if (Next && Next != this)
		{
			Next->StartEvent();
		}
	}
}

void AEncounterEvent::EndRun()
{
	bRunning = false;
	bDone = true;
	SetActorTickEnabled(false);
	MovingSpeaker.Reset();

	// Whatever anyone was acting out stops, and they go back to their own business (patrol, or
	// the fight).
	StopLineAnim();
	for (const TWeakObjectPtr<AEnemyBase>& Speaker : Speakers)
	{
		if (Speaker.IsValid() && !Speaker->IsDead())
		{
			for (const FEncounterEventStep& Step : Steps)
			{
				if (Step.Animation)
				{
					Speaker->StopAnimMontage(Step.Animation);
				}
			}
			Speaker->EndScripted();
		}
	}
}

void AEncounterEvent::Say(AEnemyBase* Speaker, USoundBase* Sound, const FText& SpeakerName, const FText& Line, float Seconds)
{
	if (CurrentVoice)
	{
		CurrentVoice->Stop();
		CurrentVoice = nullptr;
	}

	// From the speaker's head, in 3D: full within VoiceFullRange, gone VoiceFalloff further out —
	// so it carries down a corridor and grows as the player comes closer.
	if (Sound)
	{
		CurrentVoice = UBarkSubsystem::PlayVoice(Speaker, Sound, VoiceFullRange, VoiceFalloff,
			Speaker ? Speaker->GetVoicePitch() : 1.0f);
	}

	// The subtitle, if the player's close enough to be hearing it.
	AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (Player && !Line.IsEmpty()
		&& (SubtitleRange <= 0.0f || FVector::Dist(Player->GetActorLocation(), Speaker->GetActorLocation()) <= SubtitleRange))
	{
		const FText Shown = SpeakerName.IsEmpty() ? Line
			: FText::Format(NSLOCTEXT("Encounter", "SubtitleWithName", "{0}: {1}"), SpeakerName, Line);
		Player->ShowSubtitle(Shown, Seconds);
	}
}

float AEncounterEvent::PlayStepAnim(AEnemyBase* Speaker, UAnimMontage* Anim, bool bLoop)
{
	const float Length = Speaker->PlayAnimMontage(Anim);
	if (Length <= 0.0f || !bLoop)
	{
		return Length;
	}

	// Its last section runs into itself, over and over, until the step ends (StopLineAnim).
	UAnimInstance* AnimInstance = Speaker->GetMesh() ? Speaker->GetMesh()->GetAnimInstance() : nullptr;
	const int32 LastIndex = Anim->CompositeSections.Num() - 1;
	if (AnimInstance && LastIndex >= 0)
	{
		const FName Last = Anim->GetSectionName(LastIndex);
		AnimInstance->Montage_SetNextSection(Last, Last, Anim);
	}
	LineSpeaker = Speaker;
	LineAnim = Anim;
	return Length;
}

void AEncounterEvent::StopLineAnim()
{
	if (LineSpeaker.IsValid() && LineAnim)
	{
		LineSpeaker->StopAnimMontage(LineAnim);
	}
	LineSpeaker.Reset();
	LineAnim = nullptr;
}

AEnemyBase* AEncounterEvent::FindSpeaker(const FEncounterEventStep& Step) const
{
	return Step.Speaker ? Step.Speaker.Get() : FindTagged(Step.SpeakerTag);
}

AEnemyBase* AEncounterEvent::FindTagged(FName Tag) const
{
	if (Tag.IsNone())
	{
		return nullptr;
	}
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		if (!It->IsDead() && It->ActorHasTag(Tag))
		{
			return *It;
		}
	}
	return nullptr;
}

void AEncounterEvent::DrawLinks() const
{
	const UWorld* World = GetWorld();
	const FVector From = GetActorLocation();
	const FColor SpeakerColor(220, 80, 255);
	const FColor TargetColor(40, 220, 80);
	const FColor EncounterColor(255, 140, 0);
	const FColor EventColor(255, 255, 255);

	auto Arrow = [World, &From](const FVector& To, const FColor& Color)
	{
		DrawDebugDirectionalArrow(World, From, To, 60.0f, Color, false, -1.0f, SDPG_World, 2.0f);
	};

	for (const FEncounterEventStep& Step : Steps)
	{
		if (HasSpeaker(Step.Type) && Step.Speaker)
		{
			DrawDebugLine(World, From, Step.Speaker->GetActorLocation(), SpeakerColor, false, -1.0f, SDPG_World, 2.0f);

			// Where he walks to, or what he turns to face.
			if (Step.Target)
			{
				DrawDebugDirectionalArrow(World, Step.Speaker->GetActorLocation(), Step.Target->GetActorLocation(),
					40.0f, TargetColor, false, -1.0f, SDPG_World, 2.0f);
			}
		}
		if (Step.Type == EEncounterStepType::SetOffEncounter && Step.Encounter)
		{
			Arrow(Step.Encounter->GetActorLocation(), EncounterColor);
		}
		if (Step.Type == EEncounterStepType::StartEvent && Step.Event)
		{
			Arrow(Step.Event->GetActorLocation(), EventColor);
		}
	}

	for (const AEncounterEvent* Next : EventsOnFinished)
	{
		if (Next)
		{
			Arrow(Next->GetActorLocation(), EventColor);
		}
	}
	for (const AEncounterEvent* Next : EventsOnInterrupted)
	{
		if (Next)
		{
			Arrow(Next->GetActorLocation(), FColor::Red);
		}
	}
}
