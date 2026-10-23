#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Chaos/ChaosEngineInterface.h"
#include "FootstepEffectsData.generated.h"

class UNiagaraSystem;
class USoundBase;

/** What a foot planting on one kind of surface plays. */
USTRUCT(BlueprintType)
struct FFootstepEffect
{
	GENERATED_BODY()

	/** Variations, one picked at random — never the same one twice running. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep")
	TArray<TObjectPtr<USoundBase>> Sounds;

	/** Optional puff at the foot (dust, splash). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep")
	TObjectPtr<UNiagaraSystem> Dust;

	/** This surface's loudness, on top of the gait's. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep", meta = (ClampMin = "0.0"))
	float Volume = 1.0f;
};

/**
 *  Footstep sounds by physical surface, the way UImpactEffectsData does bullet hits: the
 *  step traces down from the foot, and whatever physical material it lands on picks the set.
 *  Surface types are named in Project Settings → Physics (see DefaultEngine.ini).
 */
UCLASS(BlueprintType)
class PROJECTBOPIS_API UFootstepEffectsData : public UDataAsset
{
	GENERATED_BODY()

public:

	/** Plays a step for the surface the trace hit (or Default) at the hit point. LastPlayed
	    is the caller's previous step, so this one differs from it; returns what played. */
	USoundBase* PlayFootstep(const UObject* WorldContext, const FHitResult& Hit, float GaitVolume,
		const USoundBase* LastPlayed) const;

	/** Loudness for the gait: WalkVolume at or below WalkSpeed, JogVolume at or above JogSpeed,
	    blended between; crouched steps use CrouchVolume. */
	float GaitVolume(float Speed, bool bCrouched) const;

	/** Heavier than a step: the body (a dive landing, a roll's tumble — bBody layers BodyThud
	    under it) or the feet (a fall) hitting the ground. The surface's step at Volume. */
	USoundBase* PlayThud(const UObject* WorldContext, const FHitResult& Hit, float Volume,
		const USoundBase* LastPlayed, bool bBody) const;

	float GetDiveLandingVolume() const { return DiveLandingVolume; }
	float GetRollVolume() const { return RollVolume; }

	/** A fall onto the feet: nothing below FallLandingMinSpeed, half FallLandingVolume there,
	    all of it at FallLandingFullSpeed and above (cm/s). */
	float FallVolume(float FallSpeed) const;

protected:

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep")
	TMap<TEnumAsByte<EPhysicalSurface>, FFootstepEffect> Surfaces;

	/** Used for unlisted surfaces, and ground with no physical material at all. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep")
	FFootstepEffect Default;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Gait", meta = (ClampMin = "0.0"))
	float WalkVolume = 0.6f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Gait", meta = (ClampMin = "0.0"))
	float JogVolume = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Gait", meta = (ClampMin = "0.0"))
	float CrouchVolume = 0.4f;

	/** Speeds (cm/s) bounding the walk → jog blend. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Gait", meta = (ClampMin = "0.0"))
	float WalkSpeed = 250.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Gait", meta = (ClampMin = "1.0"))
	float JogSpeed = 500.0f;

	/** Multiplies every step — the one knob for "louder everywhere". */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep", meta = (ClampMin = "0.0"))
	float VolumeScale = 1.0f;

	/** A body hitting the ground, layered under the surface's step for the dive landing and
	    the roll. Empty: the step alone. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Thuds")
	TObjectPtr<USoundBase> BodyThud;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Thuds", meta = (ClampMin = "0.0"))
	float DiveLandingVolume = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Thuds", meta = (ClampMin = "0.0"))
	float RollVolume = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Thuds", meta = (ClampMin = "0.0"))
	float FallLandingVolume = 1.2f;

	/** Fall speeds (cm/s) below which a landing is silent, and at which it's full. A normal
	    jump lands at roughly 600–900. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Thuds", meta = (ClampMin = "0.0"))
	float FallLandingMinSpeed = 300.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Footstep|Thuds", meta = (ClampMin = "1.0"))
	float FallLandingFullSpeed = 1000.0f;
};
