// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Animation/AnimEnums.h"
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
    GettingUp is a montage over the normal graph. WindUp (last, so the others keep their
    values) is the lead-in before the dive proper: a montage, still on the ground. */
UENUM(BlueprintType)
enum class EShootdodgePhase : uint8
{
	None, Start, Loop, Land, Prone, GettingUp, WindUp
};

/**
 *  The Max Payne dive: leave the ground on the press in one of eight directions relative to
 *  the camera, keep facing the aim while flying (the blend spaces turn the dive to match),
 *  land prone, stay down until the player moves. Costs Focus. Animated for pistols and
 *  duals; long guns use the same dive with their own arm hold.
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

	/** The lead-in before the dive, until its animation has fully blended out (into the start
	    of the flight): committed to it — no firing, reloading, switching or jumping. */
	UFUNCTION(BlueprintPure, Category = "Shootdodge")
	bool IsWindingUp() const { return Phase == EShootdodgePhase::WindUp || WindUpMontage != nullptr; }

	/** Starts getting up, if lying prone. bThenReload queues a reload for when the body is
	    back on its feet (the reload key asks for that; movement doesn't). */
	void RequestGetUp(bool bThenReload = false);

	/** The character died: drops the dive on the spot, whatever phase it's in. Montages
	    stop, the slow motion ends, and nothing is restored — the ragdoll takes it from here. */
	void CancelForDeath();

	EShootdodgePhase GetPhase() const { return Phase; }

	/** The body is flying, landing or lying flat — the times GetBodyShape describes it. */
	UFUNCTION(BlueprintPure, Category = "Shootdodge")
	bool IsBodyDown() const
	{
		return Phase == EShootdodgePhase::Start || Phase == EShootdodgePhase::Loop
			|| Phase == EShootdodgePhase::Land || Phase == EShootdodgePhase::Prone;
	}

	/** The flying/lying body as a capsule, laid flat along the dive's direction: for other
	    systems to query against (explosions, melee, AI checks) while IsBodyDown, instead of
	    the standing-height main capsule. A shape only — run your own query with it. */
	UFUNCTION(BlueprintPure, Category = "Shootdodge")
	void GetBodyShape(FVector& OutCentre, FQuat& OutRotation, float& OutRadius, float& OutHalfHeight) const;

	/** The dive's direction relative to where the body faces, −180..180 (0 forward, 90 right):
	    what the Start/Loop/Land blend spaces are keyed on. */
	float GetDirectionAngle() const;

	/** The Forward clip's push-off point (normalised): the Start blend space's start position
	    before any dive. Available from construction, so the AnimBP can read it at its own start. */
	float GetRestStartPosition() const;

	/** Play rate for the current phase's blend space. */
	float GetPhasePlayRate() const;

	/** Where the current phase's blend space starts, normalised 0..1 — the clip offset. */
	float GetPhaseStartPosition() const { return PhaseStartPosition; }

protected:

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	TMap<EShootdodgeDirection, FShootdodgeAnims> Animations;

	/** Only pistols and duals can dive (the dive's own animations). Off lets long guns dive
	    too, holding the gun in their own arm pose over the pistol dive. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	bool bPistolsOnly = false;

	/** A short lead-in before the dive (Max Payne 3's step into the leap): the first
	    WindUpLength seconds of a Lyra dash, on the ground. Nothing of the dive happens until it
	    ends — no Focus spent, no slow motion, no launch. Only when diving from a held aim;
	    otherwise, or with this off, the dive goes on the press. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up")
	bool bWindUp = true;

	/** Wind-up clips by direction. Forward and its diagonals use WindUpForward; Right and
	    Backward-Right use WindUpRight, Left and Backward-Left WindUpLeft; only straight back
	    uses WindUpBackward. A direction whose clip is missing dives straight away. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up", meta = (EditCondition = "bWindUp"))
	TObjectPtr<UAnimSequenceBase> WindUpForward;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up", meta = (EditCondition = "bWindUp"))
	TObjectPtr<UAnimSequenceBase> WindUpBackward;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up", meta = (EditCondition = "bWindUp"))
	TObjectPtr<UAnimSequenceBase> WindUpLeft;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up", meta = (EditCondition = "bWindUp"))
	TObjectPtr<UAnimSequenceBase> WindUpRight;

	/** Seconds of the wind-up clip to play (clip time) before the dive starts. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up", meta = (ClampMin = "0.0", EditCondition = "bWindUp"))
	float WindUpLength = 0.2f;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up", meta = (ClampMin = "0.01", EditCondition = "bWindUp"))
	float WindUpPlayRate = 1.0f;

	/** How fast a run slows during the wind-up (cm/s²): it carries on and bleeds off
	    gradually instead of stopping dead. 0 keeps the full speed; a 500 cm/s run loses
	    about a third of it over a 0.2 s wind-up at the default. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up", meta = (ClampMin = "0.0", EditCondition = "bWindUp"))
	float WindUpDeceleration = 800.0f;

	/** Seconds (game time) the wind-up blends out over the start of the flight. Slow motion
	    starts with the flight, so this runs about three times longer in real time; firing
	    waits until it's done. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Wind-up", meta = (ClampMin = "0.0", EditCondition = "bWindUp"))
	float WindUpBlendOutTime = 0.08f;

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

	/** Capsule half-height from take-off until getting up (cm; standing is the capsule's own).
	    The body flies and lies flat, so a standing capsule would catch on what it clears. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge", meta = (ClampMin = "1.0"))
	float DiveCapsuleHalfHeight = 35.0f;

	/** Keeps the lying/flying body out of walls: a capsule shape laid flat along the dive's
	    direction (the body never turns from it) is swept ahead each frame, and the velocity
	    into a wall comes off, so the body slides along it. Queries only. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Body Collision")
	bool bBodyCollision = true;

	UPROPERTY(EditAnywhere, Category = "Shootdodge|Body Collision", meta = (ClampMin = "1.0", EditCondition = "bBodyCollision"))
	float BodyCapsuleRadius = 18.0f;

	/** Half the body shape's length, end to end (cm) — about half the character's height. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Body Collision", meta = (ClampMin = "1.0", EditCondition = "bBodyCollision"))
	float BodyCapsuleHalfLength = 90.0f;

	/** Most the body is pushed back out of a wall it's already in, per frame (cm) — eases out
	    rather than popping. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Body Collision", meta = (ClampMin = "0.0", EditCondition = "bBodyCollision"))
	float BodyPushOutPerFrame = 10.0f;

	/** On landing the legs go onto physics, motors holding them to the animation, so the floor
	    keeps a landing clip from sinking them into it. Back to the animation on lying prone. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Landing Legs")
	bool bLandingLegPhysics = true;

	/** Landing leg motor strength. Higher keeps the legs closer to the clip; lower lets the
	    floor (and the slide) move them more. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Landing Legs", meta = (ClampMin = "0.0", EditCondition = "bLandingLegPhysics"))
	float LandingLegHoldStrength = 2000.0f;

	/** Seconds the legs take to blend from physics back to the animation once prone. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Landing Legs", meta = (ClampMin = "0.0", EditCondition = "bLandingLegPhysics"))
	float LandingLegBlendOutTime = 0.25f;

	/** Through the flight (the Loop — the push-off plays as authored), the legs are on physics
	    with a light hold: they follow the dive but lag and swing with the body's momentum. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Flight Legs")
	bool bFlightLegPhysics = true;

	/** Flight leg motor strength. Lower: looser, more swing; higher: closer to the clip. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Flight Legs", meta = (ClampMin = "0.0", EditCondition = "bFlightLegPhysics"))
	float FlightLegHoldStrength = 800.0f;

	/** Slow motion for the flight: on at take-off, off on landing. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Focus")
	bool bSlowMotion = true;

	/** Focus needed to dive at all. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Focus", meta = (ClampMin = "0.0"))
	float MinFocusToDive = 25.0f;

	/** Focus drained per real second while the dive's slow motion runs (take-off to landing).
	    Running dry mid-dive doesn't end it. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge|Focus", meta = (ClampMin = "0.0"))
	float FocusDrainPerSecond = 5.0f;

	/** Full-body AnimGraph slot the get-up plays in. */
	UPROPERTY(EditAnywhere, Category = "Shootdodge")
	FName SlotName = TEXT("DeathSlot");

private:

	/** The eight-way direction the movement input points, relative to the camera. */
	EShootdodgeDirection PickDirection() const;

	/** Rounds an angle (0 forward, +90 right) to the nearest of the eight directions. */
	static EShootdodgeDirection OctantOf(float Angle);

	/** The wind-up clip for a dive direction (nearest of the four), or null. */
	UAnimSequenceBase* PickWindUp(EShootdodgeDirection Direction) const;

	/** Plays the wind-up; Launch follows when it ends. False if there's nothing to play. */
	bool BeginWindUp(EShootdodgeDirection Direction);

	/** The dive proper: spends the Focus, sets the flight direction off the camera, takes off. */
	void Launch(EShootdodgeDirection Direction);

	void TakeOff();

	/** Down to DiveCapsuleHalfHeight, bottom kept where it is. */
	void ShrinkCapsule();

	/** Back to standing height, if there's room for it where the body lies. False if not. */
	bool RestoreCapsule();

	/** Trims the velocity into any wall the body shape would run into this frame. */
	void KeepBodyOutOfWalls(float DeltaTime);
	void EnterProne();

	/** Slid off an edge while landing or prone: back to the in-air Loop, to land again. */
	void FallOffEdge();
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

	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> WindUpMontage;

	/** The direction picked on the press, dived in once the wind-up ends. */
	EShootdodgeDirection WindUpDirection = EShootdodgeDirection::Forward;

	/** The anim instance's root motion mode before the wind-up (which ignores it). */
	TEnumAsByte<ERootMotionMode::Type> SavedRootMotionMode = ERootMotionMode::RootMotionFromMontagesOnly;

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

	/** The capsule is short for the dive; its standing half-height to go back to. */
	bool bCapsuleShrunk = false;
	float SavedCapsuleHalfHeight = 0.0f;
};
