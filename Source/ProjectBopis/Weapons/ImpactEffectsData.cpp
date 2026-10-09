// Copyright Epic Games, Inc. All Rights Reserved.

#include "Weapons/ImpactEffectsData.h"
#include "NiagaraFunctionLibrary.h"
#include "Kismet/GameplayStatics.h"
#include "Components/DecalComponent.h"
#include "Sound/SoundBase.h"

void UImpactEffectsData::SpawnImpact(const UObject* WorldContext, const FHitResult& Hit) const
{
	// Needs the hit's physical material — only filled in when the trace/sweep asked for it.
	const EPhysicalSurface Surface = UGameplayStatics::GetSurfaceType(Hit);
	const FImpactEffect* Found = Surfaces.Find(Surface);
	const FImpactEffect& Effect = Found ? *Found : Default;

	const FRotator SurfaceRotation = Hit.ImpactNormal.Rotation();
	const FVector BurstScale(Effect.Scale * EffectScale);

	// The main burst and every layer go off at the same point and scale.
	// Pooled: full-auto fire reuses components instead of creating one per hit.
	auto SpawnBurst = [&](UNiagaraSystem* System)
	{
		if (System)
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(WorldContext, System, Hit.ImpactPoint,
				SurfaceRotation, BurstScale, true, true, ENCPoolMethod::AutoRelease);
		}
	};

	SpawnBurst(Effect.System);
	for (UNiagaraSystem* Extra : Effect.ExtraSystems)
	{
		SpawnBurst(Extra);
	}

	if (Effect.Sound)
	{
		UGameplayStatics::PlaySoundAtLocation(WorldContext, Effect.Sound, Hit.ImpactPoint);
	}

	// Decal and its variants form one pool; pick one at random. Empty entries are skipped.
	TArray<UMaterialInterface*, TInlineAllocator<8>> DecalPool;
	if (Effect.Decal)
	{
		DecalPool.Add(Effect.Decal);
	}
	for (UMaterialInterface* Variant : Effect.DecalVariants)
	{
		if (Variant)
		{
			DecalPool.Add(Variant);
		}
	}

	if (DecalPool.Num() > 0)
	{
		// A decal projects along its X axis, so roll spins it around the surface
		// normal — repeated holes don't all line up the same way.
		FRotator DecalRotation = SurfaceRotation;
		DecalRotation.Roll = FMath::FRandRange(0.0f, 360.0f);

		UMaterialInterface* Chosen = DecalPool[FMath::RandRange(0, DecalPool.Num() - 1)];
		if (UDecalComponent* SpawnedDecal = UGameplayStatics::SpawnDecalAtLocation(WorldContext, Chosen,
			Effect.DecalSize, Hit.ImpactPoint, DecalRotation, DecalLifeSpan))
		{
			SpawnedDecal->SetFadeScreenSize(0.0f);
		}
	}
}
