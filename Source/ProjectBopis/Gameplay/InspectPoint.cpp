#include "Gameplay/InspectPoint.h"
#include "Gameplay/InteractSubsystem.h"
#include "Gameplay/InteractComponent.h"
#include "Gameplay/FocusComponent.h"
#include "ProjectBopisCharacter.h"
#include "ProjectBopis.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "Components/SphereComponent.h"
#include "Components/ArrowComponent.h"
#include "GameFramework/PlayerController.h"
#include "EnhancedInputComponent.h"
#include "LevelSequence.h"
#include "LevelSequenceActor.h"
#include "LevelSequencePlayer.h"
#include "GameFramework/Character.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"

AInspectPoint::AInspectPoint()
{
	// Ticks only during the cutscene, following the double.
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	// Only a marker: nothing collides with it, traces pass through it, and it isn't drawn in game.
	Area = CreateDefaultSubobject<USphereComponent>(TEXT("Area"));
	Area->InitSphereRadius(200.0f);
	Area->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Area->SetGenerateOverlapEvents(false);
	Area->SetCanEverAffectNavigation(false);
	Area->SetHiddenInGame(true);
	Area->ShapeColor = FColor(255, 200, 60);
	RootComponent = Area;

	// To start with, 1.2 m short of the thing, facing it.
	Mark = CreateDefaultSubobject<UArrowComponent>(TEXT("Mark"));
	Mark->SetupAttachment(Area);
	Mark->SetRelativeLocation(FVector(-120.0f, 0.0f, 0.0f));
	Mark->ArrowColor = FColor(255, 200, 60);
	Mark->SetHiddenInGame(true);

	// The player's double, by default. Only its path: nothing loads until BeginPlay.
	DoubleClass = TSoftClassPtr<AActor>(FSoftObjectPath(TEXT("/Game/ThirdPerson/Blueprints/CC/BP_Player_Cutscene.BP_Player_Cutscene_C")));
}

float AInspectPoint::GetInteractRange() const
{
	return Area->GetScaledSphereRadius();
}

void AInspectPoint::BeginPlay()
{
	Super::BeginPlay();
	if (UInteractSubsystem* Interactables = GetWorld()->GetSubsystem<UInteractSubsystem>())
	{
		Interactables->Register(this);
	}
	if (Cutscene && !DoubleClass.IsNull())
	{
		PrepareDouble();
	}
}

void AInspectPoint::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UInteractSubsystem* Interactables = GetWorld()->GetSubsystem<UInteractSubsystem>())
	{
		Interactables->Unregister(this);
	}
	Super::EndPlay(EndPlayReason);
}

void AInspectPoint::Interact(AProjectBopisCharacter* Player)
{
	if (!Player)
	{
		return;
	}
	bDone = true;
	InspectingPlayer = Player;
	UE_LOG(LogProjectBopis, Log, TEXT("%s inspected"), *GetName());

	if (!StartCutscene(Player))
	{
		EndCutscene();
	}
}

bool AInspectPoint::StartCutscene(AProjectBopisCharacter* Player)
{
	if (!Cutscene)
	{
		return false;
	}
	const TArray<FMovieSceneObjectBindingID>& Doubles = Cutscene->FindBindingsByTag(PlayerTag);
	bHasDouble = Doubles.Num() > 0;
	if (bHasDouble)
	{
		DoubleBinding = Doubles[0];
	}
	else
	{
		UE_LOG(LogProjectBopis, Warning, TEXT("%s: %s has no binding tagged %s, so the player comes back on the Mark."),
			*GetName(), *Cutscene->GetName(), *PlayerTag.ToString());
	}

	ALevelSequenceActor* Actor = nullptr;
	SequencePlayer = ULevelSequencePlayer::CreateLevelSequencePlayer(GetWorld(), Cutscene,
		FMovieSceneSequencePlaybackSettings(), Actor);
	SequenceActor = Actor;
	if (!SequencePlayer || !SequenceActor)
	{
		return false;
	}

	// The real player sits it out, hidden and out of play; the cutscene has its own double.
	bTookPlayer = true;
	if (APlayerController* Controller = Cast<APlayerController>(Player->GetController()))
	{
		Player->DisableInput(Controller);

		// Interact skips: this actor takes the button while the player's input is off.
		EnableInput(Controller);
		UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent);
		if (Input && Player->GetInteractAction())
		{
			Input->BindAction(Player->GetInteractAction(), ETriggerEvent::Started, this, &AInspectPoint::Skip);
		}
	}
	if (UFocusComponent* Focus = Player->GetFocus())
	{
		Focus->StopFocus();
	}
	if (UInteractComponent* Interaction = Player->GetInteraction())
	{
		Interaction->SetComponentTickEnabled(false);
	}
	bDamageableBefore = Player->CanBeDamaged();
	Player->SetCanBeDamaged(false);
	SetPlayerHidden(Player, true);

	// The double built at the start takes the place of the sequence's own, already drawn-ready.
	if (Double)
	{
		SetDoubleActive(true);
		TArray<AActor*> Ready;
		Ready.Add(Double);
		SequenceActor->SetBindingByTag(PlayerTag, Ready);
	}

	SequencePlayer->OnFinished.AddDynamic(this, &AInspectPoint::EndCutscene);
	SequencePlayer->OnStop.AddDynamic(this, &AInspectPoint::EndCutscene);
	SequencePlayer->Play();

	// Following the double, so the player comes back where it finishes.
	SetActorTickEnabled(true);
	return true;
}

void AInspectPoint::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// In the cutscene: following the double. Before it: keeping the waiting double out of sight.
	if (SequencePlayer)
	{
		RecordDouble();
	}
	else
	{
		WatchDouble(DeltaSeconds);
	}
}

void AInspectPoint::WatchDouble(float DeltaSeconds)
{
	DoubleWatchTime += DeltaSeconds;
	if (Double && !Double->IsHidden())
	{
		// Its clothes and hair are in: back out of sight, and no more watching.
		SetDoubleActive(false);
		SetActorTickEnabled(false);
		return;
	}
	if (DoubleWatchTime > 30.0f)
	{
		SetActorTickEnabled(false);
	}
}

void AInspectPoint::RecordDouble()
{
	if (!bHasDouble || !SequencePlayer)
	{
		return;
	}
	for (UObject* Bound : SequencePlayer->GetBoundObjects(DoubleBinding))
	{
		if (const AActor* BoundActor = Cast<AActor>(Bound))
		{
			DoubleEnd = BoundActor->GetActorTransform();
			bHasDoubleEnd = true;
			return;
		}
	}
}

void AInspectPoint::Skip()
{
	if (!SequencePlayer || !SequencePlayer->IsPlaying())
	{
		return;
	}
	// To its last frame first, so the double stands where the cutscene would have left it.
	const FQualifiedFrameTime End = SequencePlayer->GetEndTime();
	SequencePlayer->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(
		FFrameTime(End.Time.FrameNumber - 1), EUpdatePositionMethod::Jump));
	RecordDouble();
	SequencePlayer->Stop();
}

void AInspectPoint::EndCutscene()
{
	// Finishing and stopping can both report in; once is enough.
	if (bEnded)
	{
		return;
	}
	bEnded = true;
	SetActorTickEnabled(false);

	if (SequenceActor)
	{
		// Not destroyed from inside its own player's callback: it goes a moment later.
		SequenceActor->SetLifeSpan(0.5f);
	}

	// Its part is over.
	if (Double)
	{
		SetDoubleActive(false);
		Double->SetLifeSpan(0.5f);
	}

	AProjectBopisCharacter* Player = InspectingPlayer.Get();
	if (Player && bTookPlayer)
	{
		// Back where the double finished (or on the Mark, without one), facing the same way.
		FVector Where = Mark->GetComponentLocation();
		Where.Z = Player->GetActorLocation().Z;
		float Yaw = Mark->GetComponentRotation().Yaw;
		if (bHasDoubleEnd)
		{
			Where = DoubleEnd.GetLocation();
			Yaw = DoubleEnd.Rotator().Yaw;
		}
		Player->SetActorLocationAndRotation(Where, FRotator(0.0f, Yaw, 0.0f), false, nullptr, ETeleportType::TeleportPhysics);

		SetPlayerHidden(Player, false);
		Player->SetCanBeDamaged(bDamageableBefore);
		if (UInteractComponent* Interaction = Player->GetInteraction())
		{
			Interaction->SetComponentTickEnabled(true);
		}
		if (APlayerController* Controller = Cast<APlayerController>(Player->GetController()))
		{
			DisableInput(Controller);
			// The camera comes back behind him.
			Controller->SetControlRotation(FRotator(0.0f, Yaw, 0.0f));
			Player->EnableInput(Controller);
		}
	}
	OnInspected(Player);
}

void AInspectPoint::PrepareDouble()
{
	// Loads here, with the level, not with the game module (see DoubleClass).
	UClass* LoadedClass = DoubleClass.LoadSynchronous();
	if (!LoadedClass)
	{
		return;
	}

	FActorSpawnParameters Params;
	Params.Owner = this;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Double = GetWorld()->SpawnActor<AActor>(LoadedClass, Mark->GetComponentLocation(),
		FRotator(0.0f, Mark->GetComponentRotation().Yaw, 0.0f), Params);
	if (!Double)
	{
		return;
	}

	// Standing on the floor under the Mark, as the cutscene's own would.
	const FVector From = Mark->GetComponentLocation() + FVector(0.0f, 0.0f, 100.0f);
	FHitResult Floor;
	FCollisionQueryParams Query(SCENE_QUERY_STAT(InspectDoubleFloor), false, this);
	Query.AddIgnoredActor(Double);
	if (GetWorld()->LineTraceSingleByChannel(Floor, From, From - FVector(0.0f, 0.0f, 800.0f), ECC_Visibility, Query))
	{
		const ACharacter* AsCharacter = Cast<ACharacter>(Double);
		const float HalfHeight = AsCharacter ? AsCharacter->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 0.0f;
		Double->SetActorLocation(Floor.ImpactPoint + FVector(0.0f, 0.0f, HalfHeight));
	}
	SetDoubleActive(false);

	// Watch it until the Character Customizer has finished with it (see WatchDouble).
	SetActorTickEnabled(true);
}

void AInspectPoint::SetDoubleActive(bool bActive) const
{
	Double->SetActorHiddenInGame(!bActive);
	Double->SetActorTickEnabled(bActive);
	TArray<USkeletalMeshComponent*> Meshes;
	Double->GetComponents(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		Mesh->SetComponentTickEnabled(bActive);
	}
}

void AInspectPoint::SetPlayerHidden(AProjectBopisCharacter* Player, bool bHide) const
{
	Player->SetActorHiddenInGame(bHide);
	const UWeaponHolderComponent* Holder = Player->GetWeaponHolder();
	if (AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr)
	{
		Weapon->SetActorHiddenInGame(bHide);
	}
}
