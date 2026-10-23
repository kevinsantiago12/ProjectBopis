#include "Gameplay/FootstepEffectsData.h"
#include "NiagaraFunctionLibrary.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

USoundBase* UFootstepEffectsData::PlayFootstep(const UObject* WorldContext, const FHitResult& Hit, float GaitVolume,
	const USoundBase* LastPlayed) const
{
	// Needs the hit's physical material — only filled in when the trace asked for it.
	const EPhysicalSurface Surface = UGameplayStatics::GetSurfaceType(Hit);
	const FFootstepEffect* Found = Surfaces.Find(Surface);
	const FFootstepEffect& Effect = Found ? *Found : Default;

	if (Effect.Dust)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(WorldContext, Effect.Dust, Hit.ImpactPoint,
			Hit.ImpactNormal.Rotation(), FVector::OneVector, true, true, ENCPoolMethod::AutoRelease);
	}

	// Any variation but the last one, so two steps in a row never sound identical.
	TArray<USoundBase*, TInlineAllocator<16>> Choices;
	for (USoundBase* Sound : Effect.Sounds)
	{
		if (Sound && (Sound != LastPlayed || Effect.Sounds.Num() == 1))
		{
			Choices.Add(Sound);
		}
	}
	if (Choices.Num() == 0)
	{
		return nullptr;
	}

	// Owned by the character (the context), so a cue's per-owner voice limit counts per pair
	// of feet rather than across everyone walking.
	USoundBase* Chosen = Choices[FMath::RandRange(0, Choices.Num() - 1)];
	UGameplayStatics::PlaySoundAtLocation(WorldContext, Chosen, Hit.ImpactPoint, FRotator::ZeroRotator,
		GaitVolume * Effect.Volume * VolumeScale, 1.0f, 0.0f, nullptr, nullptr, Cast<AActor>(WorldContext));
	return Chosen;
}

USoundBase* UFootstepEffectsData::PlayThud(const UObject* WorldContext, const FHitResult& Hit, float Volume,
	const USoundBase* LastPlayed, bool bBody) const
{
	USoundBase* Step = PlayFootstep(WorldContext, Hit, Volume, LastPlayed);
	if (bBody && BodyThud)
	{
		UGameplayStatics::PlaySoundAtLocation(WorldContext, BodyThud, Hit.ImpactPoint, FRotator::ZeroRotator,
			Volume * VolumeScale, 1.0f, 0.0f, nullptr, nullptr, Cast<AActor>(WorldContext));
	}
	return Step;
}

float UFootstepEffectsData::FallVolume(float FallSpeed) const
{
	if (FallSpeed < FallLandingMinSpeed)
	{
		return 0.0f;
	}
	const float Alpha = FMath::Clamp((FallSpeed - FallLandingMinSpeed)
		/ FMath::Max(FallLandingFullSpeed - FallLandingMinSpeed, 1.0f), 0.0f, 1.0f);
	return FMath::Lerp(FallLandingVolume * 0.5f, FallLandingVolume, Alpha);
}

float UFootstepEffectsData::GaitVolume(float Speed, bool bCrouched) const
{
	if (bCrouched)
	{
		return CrouchVolume;
	}
	const float Alpha = FMath::Clamp((Speed - WalkSpeed) / FMath::Max(JogSpeed - WalkSpeed, 1.0f), 0.0f, 1.0f);
	return FMath::Lerp(WalkVolume, JogVolume, Alpha);
}
