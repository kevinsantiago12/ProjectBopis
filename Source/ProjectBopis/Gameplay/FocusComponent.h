// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "FocusComponent.generated.h"

class UPostProcessComponent;
class USoundBase;
class UAudioComponent;

/**
 *  Focus: Max Payne style slow motion (not called "bullet time" — that name is
 *  trademarked). A toggle slows the whole world — the player included — to
 *  WorldTimeDilation; aiming stays responsive because look input isn't time-scaled.
 *  Runs on a meter that drains in real seconds and refills on kills (AddMeter), with
 *  optional passive regen and an infinite mode for testing.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class PROJECTBOPIS_API UFocusComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UFocusComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Turns Focus on if it's off (and the meter allows), off if it's on. */
	UFUNCTION(BlueprintCallable, Category = "Focus")
	void Toggle();

	UFUNCTION(BlueprintCallable, Category = "Focus")
	void StopFocus();

	/** Refills the meter — call on kills (KillRefill is the usual amount). */
	UFUNCTION(BlueprintCallable, Category = "Focus")
	void AddMeter(float Amount);

	UFUNCTION(BlueprintPure, Category = "Focus")
	bool IsFocusActive() const { return bActive; }

	/** 0..1, for the HUD. */
	UFUNCTION(BlueprintPure, Category = "Focus")
	float GetMeterFraction() const { return MaxMeter > 0.0f ? Meter / MaxMeter : 0.0f; }

	/** Meter refill for one kill. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus")
	float KillRefill = 20.0f;

protected:

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** World speed while active. The player is slowed with it; aiming is not. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float WorldTimeDilation = 0.3f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus", meta = (ClampMin = "1.0"))
	float MaxMeter = 100.0f;

	/** Meter spent per real second while active (100 / 15 ≈ 6.7 s of Focus). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus", meta = (ClampMin = "0.0"))
	float DrainPerSecond = 15.0f;

	/** Can't start with less than this, so an empty meter doesn't flicker on and off. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus", meta = (ClampMin = "0.0"))
	float MinMeterToActivate = 10.0f;

	/** Refill slowly while inactive. On until enemies exist to refill it on kills. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus")
	bool bPassiveRegen = true;

	/** Meter per real second while regenerating. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus", meta = (ClampMin = "0.0", EditCondition = "bPassiveRegen"))
	float PassiveRegenPerSecond = 5.0f;

	/** Never drains — for testing and accessibility. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus")
	bool bInfinite = false;

	// ---- Feedback ----

	/** Real seconds to fade the screen effect and pitch in and out. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus|Feedback", meta = (ClampMin = "0.0"))
	float FeedbackFadeTime = 0.25f;

	/** Global audio pitch while active — gunfire and the world sound slowed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus|Feedback", meta = (ClampMin = "0.1", ClampMax = "1.0"))
	float FocusPitch = 0.6f;

	/** Optional one-shots on entering / leaving, and a loop (heartbeat) while active. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus|Feedback")
	TObjectPtr<USoundBase> EnterSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus|Feedback")
	TObjectPtr<USoundBase> ExitSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Focus|Feedback")
	TObjectPtr<USoundBase> LoopSound;

private:

	void StartFocus();
	void ApplyTimeDilation(float Dilation);
	void UpdateFeedback(float RealDelta);

	/** The owner's post-process component (the Focus look), found in BeginPlay. */
	UPROPERTY(Transient)
	TObjectPtr<UPostProcessComponent> PostProcess;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> LoopAudio;

	/** 0..1, eased in real time — the screen effect's weight. */
	float FeedbackAlpha = 0.0f;

	float Meter = 0.0f;
	bool bActive = false;
};
