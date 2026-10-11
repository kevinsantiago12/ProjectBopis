// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShootdodgeComponent.generated.h"

class AProjectBopisCharacter;
class UAnimSequenceBase;
class UAnimMontage;

/** The eight dive directions, relative to the body. Declaration order is the octant order. */
UENUM(BlueprintType)
enum class EShootdodgeDirection : uint8
{
	Forward, ForwardRight, Right, BackwardRight, Backward, BackwardLeft, Left, ForwardLeft
};

/** One direction's clips. The blend spaces hold Start/Loop/Land for animation; these are
    read here for timing (lengths) and for the get-up, which plays as a one-shot. */
USTRUCT(BlueprintType)
struct FShootdodgeAnims
{
	GENERATED_BODY()

	/** Push-off. Its length (minus the offset) times the Start phase. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Start;

	/** Seconds into Start to begin. Below 0 uses the component's StartClipOffset. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	float StartOffset = -1.0f;

	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Loop;

	/** The landing. Its length (minus the offset) times the Land phase. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Land;

	/** Seconds into Land to begin (the impact frame). Below 0 uses LandClipOffset. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	float LandOffset = -1.0f;

	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Prone;

	/** Plays as a one-shot in SlotName, for the direction the body landed in. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TObjectPtr<UAnimSequenceBase> Getup;
};

/** Where the dive is. Start, Loop, Land and Prone are AnimBP states (blend spaces);
    GettingUp is a montage over the normal graph. */
UENUM(BlueprintType)
enum class EShootdodgePhase : uint8
{
	None, Start, Loop, Land, Prone, GettingUp
};

/**
 *  The Max Payne dive: leave the ground on the press in one of eight directions relative to
 *  the camera, keep facing the aim while flying (the blend spaces turn the dive to match),
 *  land prone, stay down until the player moves. Costs Focus. Pistols and duals only.
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

	UFUNCTION(BlueprintPure, Category = "Shootdodge")
	bool IsAirborne() const { return Phase == EShootdodgePhase::Start || Phase == EShootdodgePhase::Loop; }

	/** Scrambling to the feet after a dive — the vulnerable moment: no firing or reloading. */
	UFUNCTION(BlueprintPure, Category = "Shootdodge")
	bool IsGettingUp() const { return Phase == EShootdodgePhase::GettingUp; }

	/** Starts getting up, if lying prone. bThenReload queues a reload for when the body is
	    back on its feet (the reload key asks for that; movement doesn't). */
	void RequestGetUp(bool bThenReload = false);

	EShootdodgePhase GetPhase() const { return Phase; }

	/** The dive's direction relative to where the body faces, −180..180 (0 forward, 90 right):
	    what the Start/Loop/Land blend spaces are keyed on. */
	float GetDirectionAngle() const;

	/** Play rate for the current phase's blend space. */
	float GetPhasePlayRate() const;

	/** Where the current phase's blend space starts, normalised 0..1 — the clip offset. */
	float GetPhaseStartPosition() const { return PhaseStartPosition; }

protected:

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TMap<EShootdodgeDirection, FShootdodgeAnims> Animations;

	/** Default seconds into each Start clip to begin — the push-off frame. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float StartClipOffset = 0.4f;

	/** Default seconds into each Land clip to begin — skips its airborne lead-in. */
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

	/** How fast the body turns to face the aim during the dive and while prone (interp speed;
	    higher is snappier, 0 snaps instantly). The flight path doesn't turn with it. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float FaceAimSpeed = 10.0f;

	/** Horizontal launch speed, in cm/s. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float DiveSpeed = 650.0f;

	/** Upward launch speed, in cm/s. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float DiveLift = 450.0f;

	/** Gravity multiplier while airborne. Restored on landing. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.05"))
	float DiveGravityScale = 0.6f;

	/** Horizontal braking while airborne, in cm/s². 0 keeps the full launch speed. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float DiveAirBraking = 0.0f;

	/** On landing, the speed bleeds off at this rate (cm/s²) — a slide along the floor. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float LandSlideDeceleration = 800.0f;

	/** Slow motion for the flight: on at take-off, off on landing. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Focus")
	bool bSlowMotion = true;

	/** Focus needed to dive at all. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Focus", meta = (ClampMin = "0.0"))
	float MinFocusToDive = 25.0f;

	/** Focus spent per dive. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Focus", meta = (ClampMin = "0.0"))
	float FocusCost = 25.0f;

	/** Full-body AnimGraph slot the get-up plays in. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	FName SlotName = TEXT("DeathSlot");

private:

	/** The eight-way direction the movement input points, relative to the camera. */
	EShootdodgeDirection PickDirection() const;

	/** Rounds an angle (0 forward, +90 right) to the nearest of the eight directions. */
	static EShootdodgeDirection OctantOf(float Angle);

	void TakeOff();
	void EnterProne();
	void Finish();
	void EndSlowMotion();

	/** Seconds a clip plays from Offset at PlayRate; 0 if there's no clip. */
	static float PhaseLength(const UAnimSequenceBase* Clip, float Offset, float PlayRate);

	/** The get-up montage has played out (or was never playing). */
	bool HasFinished(const UAnimMontage* Montage) const;

	UPROPERTY(Transient)
	TObjectPtr<AProjectBopisCharacter> Character;

	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> GetupMontage;

	EShootdodgePhase Phase = EShootdodgePhase::None;

	/** The flight's world yaw, fixed at take-off. The body turns; the path doesn't. */
	float DiveYaw = 0.0f;

	/** The direction the body landed in, relative to itself — picks the get-up. */
	EShootdodgeDirection LandDirection = EShootdodgeDirection::Forward;

	float PhaseTime = 0.0f;
	float PhaseDuration = 0.0f;
	float PhaseStartPosition = 0.0f;

	bool bOwnsSlowMotion = false;

	/** Reload asked for while prone — runs as soon as the get-up finishes. */
	bool bReloadQueued = false;

	float SavedGravityScale = 1.0f;
	float SavedAirBraking = 0.0f;
	float SavedWalkingBraking = 0.0f;
	bool bSavedSeparateBrakingFriction = false;
	float SavedBrakingFriction = 0.0f;
};
