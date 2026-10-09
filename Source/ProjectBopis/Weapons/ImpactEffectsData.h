// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Chaos/ChaosEngineInterface.h"
#include "ImpactEffectsData.generated.h"

class UNiagaraSystem;
class UMaterialInterface;
class USoundBase;

/** What a hit on one kind of surface spawns. Any part may be left empty. */
USTRUCT(BlueprintType)
struct FImpactEffect
{
	GENERATED_BODY()

	/** The main burst. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	TObjectPtr<UNiagaraSystem> System;

	/** Extra bursts layered on the main one — sparks, a dust plume, debris. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	TArray<TObjectPtr<UNiagaraSystem>> ExtraSystems;

	/** Scale for every burst on this surface, on top of the asset-wide EffectScale. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact", meta = (ClampMin = "0.01"))
	float Scale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	TObjectPtr<UMaterialInterface> Decal;

	/** More bullet holes to pick from at random, alongside Decal. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	TArray<TObjectPtr<UMaterialInterface>> DecalVariants;

	/** Decal box size; X is the projection depth. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	FVector DecalSize = FVector(5.0f, 5.0f, 5.0f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	TObjectPtr<USoundBase> Sound;
};

/**
 *  Impact effects by physical surface: the burst and the bullet hole for each kind of
 *  material a shot can hit. Shared by hitscan and projectile hits via SpawnImpact.
 *  Surface types are named in Project Settings → Physics (see DefaultEngine.ini).
 */
UCLASS(BlueprintType)
class PROJECTBOPIS_API UImpactEffectsData : public UDataAsset
{
	GENERATED_BODY()

public:

	/** Spawns the effect for whatever surface the hit reports, or Default. */
	void SpawnImpact(const UObject* WorldContext, const FHitResult& Hit) const;

protected:

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	TMap<TEnumAsByte<EPhysicalSurface>, FImpactEffect> Surfaces;

	/** Used for unlisted surfaces, and hits with no physical material at all. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	FImpactEffect Default;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact", meta = (ClampMin = "0.0"))
	float DecalLifeSpan = 10.0f;

	/** Multiplies every burst's scale — the one knob for "bigger everywhere". */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact", meta = (ClampMin = "0.01"))
	float EffectScale = 1.0f;
};
