// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShootdodgeComponent.generated.h"

class AProjectBopisCharacter;
class UAnimSequenceBase;
class UAnimMontage;

/** The eight dive directions, relative to the camera. */
UENUM(BlueprintType)
enum class EShootdodgeDirection : uint8
{
	Forward, ForwardRight, Right, BackwardRight, Backward, BackwardLeft, Left, ForwardLeft
};

/** The clips for one dive direction, played in order. */
USTRUCT(BlueprintType)
struct FShootdodgeAnims
{
	GENERATED_BODY()

	/** Push-off. Plays from StartOffset (where the feet leave the ground), then Loop takes
	    over. The character is already in the air from the first frame. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Start;

	/** Seconds into Start to begin. Below 0 uses the component's StartClipOffset. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	float StartOffset = -1.0f;

	/** Loops while airborne. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Loop;

	/** The landing. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Land;

	/** Seconds into Land to begin (the impact frame). Below 0 uses LandClipOffset. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	float LandOffset = -1.0f;

	/** Held while lying there. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Prone;

	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Getup;
};

UENUM()
enum class EShootdodgePhase : uint8
{
	None, Airborne, Landing, Prone, GettingUp
};

/**
 *  The Max Payne dive: leave the ground on the press in one of eight directions relative to
 *  the camera, land prone, stay down until the player moves. Costs Focus. Pistols and duals
 *  only. The clips play in place (root locked); the arc is the launch plus lighter gravity.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class PROJECTBOPIS_API UShootdodgeComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UShootdodgeComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Starts a dive if allowed: on the ground, a pistol or duals, enough Focus. */
	bool TryStart();

	/** The character touched down. Ends the flight. */
	void NotifyLanded();

	/** Movement input arrived. While prone, it means "get up". */
	void NotifyMoveInput();

	/** In any part of a dive — movement and rotation belong to it. */
	UFUNCTION(BlueprintPure, Category = "Shootdodge")
	bool IsDodging() const { return Phase != EShootdodgePhase::None; }

	UFUNCTION(BlueprintPure, Category = "Shootdodge")
	bool IsProne() const { return Phase == EShootdodgePhase::Prone; }

protected:

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TMap<EShootdodgeDirection, FShootdodgeAnims> Animations;

	/** Default seconds into each Start clip to begin — the push-off frame. A direction's
	    own StartOffset overrides it. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float StartClipOffset = 0.4f;

	/** Default seconds into each Land clip to begin — skips its airborne lead-in so the
	    impact plays the moment the capsule touches down. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float LandClipOffset = 0.5f;

	/** Play rate of each part of the dive, for all directions. 1 is as authored. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Play Rate", meta = (ClampMin = "0.01"))
	float StartPlayRate = 2.0f;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Play Rate", meta = (ClampMin = "0.01"))
	float LoopPlayRate = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Play Rate", meta = (ClampMin = "0.01"))
	float LandPlayRate = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Play Rate", meta = (ClampMin = "0.01"))
	float PronePlayRate = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Play Rate", meta = (ClampMin = "0.01"))
	float GetupPlayRate = 1.0f;

	/** Horizontal launch speed, in cm/s. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float DiveSpeed = 650.0f;

	/** Upward launch speed, in cm/s. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float DiveLift = 450.0f;

	/** Gravity multiplier while airborne: below 1 hangs the body in the air longer without
	    a higher jump. Restored on landing. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.05"))
	float DiveGravityScale = 0.6f;

	/** Horizontal braking while airborne, in cm/s². 0 keeps the full launch speed until
	    landing; the player's normal air braking would otherwise stop the dive mid-flight. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float DiveAirBraking = 0.0f;

	/** On landing, the dive's speed bleeds off at this rate (cm/s²) instead of stopping dead —
	    a slide along the floor. Higher stops sooner. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float LandSlideDeceleration = 800.0f;

	/** Focus needed to dive at all. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Focus", meta = (ClampMin = "0.0"))
	float MinFocusToDive = 25.0f;

	/** Focus spent per dive. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Focus", meta = (ClampMin = "0.0"))
	float FocusCost = 25.0f;

	/** Full-body AnimGraph slot the dive plays in. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	FName SlotName = TEXT("DeathSlot");

private:

	/** The eight-way direction the movement input points, relative to the camera. */
	EShootdodgeDirection PickDirection() const;

	void TakeOff();
	void EnterProne();
	void Finish();

	/** Plays a clip in SlotName at PlayRate from StartTime, looping LoopCount times. */
	UAnimMontage* Play(UAnimSequenceBase* Clip, float PlayRate, int32 LoopCount = 1, float StartTime = 0.0f);

	/** The montage has played out (or was never playing). */
	bool HasFinished(const UAnimMontage* Montage) const;

	UPROPERTY(Transient)
	TObjectPtr<AProjectBopisCharacter> Character;

	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> ActiveMontage;

	EShootdodgePhase Phase = EShootdodgePhase::None;
	EShootdodgeDirection Direction = EShootdodgeDirection::Forward;

	/** Airborne and past the Start clip, on the looping flight pose. */
	bool bLooping = false;

	/** The movement component's gravity scale before the dive, put back on landing. */
	float SavedGravityScale = 1.0f;

	/** The movement component's air braking before the dive, put back on landing. */
	float SavedAirBraking = 0.0f;

	/** The movement component's ground braking before the slide, put back on getting up. */
	float SavedWalkingBraking = 0.0f;
	bool bSavedSeparateBrakingFriction = false;
	float SavedBrakingFriction = 0.0f;
};
