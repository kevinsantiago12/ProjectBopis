#include "Enemies/BarkSubsystem.h"
#include "Components/AudioComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

bool UBarkSubsystem::TryBark(AActor* Speaker, const UBarkVoice* Voice, EBarkType Type)
{
	UWorld* World = GetWorld();
	const UBarkSet* Set = Voice ? Voice->GetSet(Language) : nullptr;
	const FBarkLines* Lines = Set ? Set->Lines.Find(Type) : nullptr;
	if (!World || !Speaker || !Lines || Lines->Sounds.IsEmpty())
	{
		return false;
	}

	// Out of earshot: nobody to hear it, so it doesn't use up the cooldown either.
	const APawn* Player = UGameplayStatics::GetPlayerPawn(World, 0);
	if (!Player || FVector::Dist(Player->GetActorLocation(), Speaker->GetActorLocation()) > HearingRange)
	{
		return false;
	}

	const double Now = World->GetTimeSeconds();
	const double* Next = NextAllowed.Find(Type);
	if ((Next && Now < *Next) || FMath::FRand() > Lines->Chance)
	{
		return false;
	}

	// One line per speaker; dying cuts off whatever he was saying.
	const bool bDeath = Type == EBarkType::Death;
	auto Finished = [](const UAudioComponent* Comp) { return !IsValid(Comp) || !Comp->IsPlaying(); };
	Playing.RemoveAll(Finished);
	for (UAudioComponent* Comp : Playing)
	{
		if (Comp->GetOwner() == Speaker)
		{
			if (!bDeath)
			{
				return false;
			}
			Comp->Stop();
		}
	}
	Playing.RemoveAll(Finished);

	// The cap, so a room doesn't talk over itself. A death grunt always gets through.
	if (!bDeath && Playing.Num() >= MaxConcurrent)
	{
		return false;
	}

	// A different line from last time, when there's a choice.
	const TWeakObjectPtr<USoundBase>* Last = LastPlayed.Find(Type);
	TArray<USoundBase*> Choices;
	for (USoundBase* Sound : Lines->Sounds)
	{
		if (Sound && (Lines->Sounds.Num() == 1 || !Last || Last->Get() != Sound))
		{
			Choices.Add(Sound);
		}
	}
	if (Choices.IsEmpty())
	{
		return false;
	}
	USoundBase* Sound = Choices[FMath::RandRange(0, Choices.Num() - 1)];

	Playing.Add(PlayVoice(Speaker, Sound, VoiceFullRange, VoiceFalloff));
	NextAllowed.Add(Type, Now + Lines->Cooldown);
	LastPlayed.Add(Type, Sound);
	return true;
}

UAudioComponent* UBarkSubsystem::PlayVoice(AActor* Speaker, USoundBase* Sound, float FullRange, float Falloff)
{
	UAudioComponent* Voice = NewObject<UAudioComponent>(Speaker);
	Voice->SetSound(Sound);
	Voice->bAutoDestroy = true;
	Voice->bOverrideAttenuation = true;
	Voice->AttenuationOverrides.bAttenuate = true;
	Voice->AttenuationOverrides.bSpatialize = true;
	Voice->AttenuationOverrides.AttenuationShape = EAttenuationShape::Sphere;
	Voice->AttenuationOverrides.AttenuationShapeExtents = FVector(FullRange, 0.0f, 0.0f);
	Voice->AttenuationOverrides.FalloffDistance = Falloff;

	const ACharacter* Character = Cast<ACharacter>(Speaker);
	USkeletalMeshComponent* Body = Character ? Character->GetMesh() : nullptr;
	if (Body && Body->DoesSocketExist(TEXT("head")))
	{
		Voice->SetupAttachment(Body, TEXT("head"));
	}
	else
	{
		Voice->SetupAttachment(Speaker->GetRootComponent());
	}
	Voice->RegisterComponent();
	Voice->Play();
	return Voice;
}
