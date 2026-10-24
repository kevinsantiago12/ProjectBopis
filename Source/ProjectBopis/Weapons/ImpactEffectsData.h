// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Chaos/ChaosEngineInterface.h"
#include "ImpactEffectsData.generated.h"

class UNiagaraSystem;
class UMaterialInterface;
class USoundBase;
class USoundAttenuation;

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

	/** More hit sounds to pick from at random, alongside Sound. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact")
	TArray<TObjectPtr<USoundBase>> SoundVariants;
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

	/** A round that went past the player without hitting him: the crack of it going by, at the
	    point of its path nearest his head, if that's within NearMissRadius. Rounds the player
	    fires himself, or that stop short of him, make none. */
	void PlayNearMiss(const UObject* WorldContext, const FVector& From, const FVector& To,
		const AActor* Shooter, const AActor* HitActor) const;

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

	/** A hit on a character's head plays one of these instead of its surface's sound. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact|Sound")
	TArray<TObjectPtr<USoundBase>> HeadshotSounds;

	/** The bones that count as the head for HeadshotSounds. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact|Sound")
	TArray<FName> HeadBones = { TEXT("head") };

	/** How far hit and near-miss sounds carry, and where they pan from. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact|Sound")
	TObjectPtr<USoundAttenuation> SoundAttenuation;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Impact|Sound", meta = (ClampMin = "0.0"))
	float SoundVolume = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Near Miss")
	TArray<TObjectPtr<USoundBase>> NearMissSounds;

	/** How close (cm) to the player's head a round must pass to be heard going by. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Near Miss", meta = (ClampMin = "0.0"))
	float NearMissRadius = 250.0f;

	/** At most one near miss per this many seconds, so a burst or a shotgun's pellets don't stack. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Near Miss", meta = (ClampMin = "0.0"))
	float NearMissMinInterval = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Near Miss", meta = (ClampMin = "0.0"))
	float NearMissVolume = 1.0f;

private:
	/** One clip from First and Variants, at random; null when both are empty. */
	static USoundBase* PickSound(USoundBase* First, const TArray<TObjectPtr<USoundBase>>& Variants);

	/** When the last near miss played (platform seconds), across every weapon using this asset. */
	mutable double LastNearMissTime = 0.0;
};
