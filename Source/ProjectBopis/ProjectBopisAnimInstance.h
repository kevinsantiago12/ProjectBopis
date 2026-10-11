// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Kismet/KismetMathLibrary.h"
#include "Weapons/WeaponBase.h"
#include "Gameplay/ShootdodgeComponent.h"
#include "ProjectBopisAnimInstance.generated.h"

class ABopisCharacterBase;
class UAnimMontage;

/**
 *  Native parent of the character's AnimBP. Computes every value the AnimGraph reads,
 *  once per frame, so the AnimBP holds only the graph and no Event Graph logic.
 *  Property names match what the AnimGraph's getters expect — don't rename them
 *  without re-pointing those nodes. The AnimGraph-facing reals are double, not float,
 *  because Blueprint "Float" is double in UE5: on reparenting, a Blueprint variable
 *  only merges into a same-named native property of exactly the same type. A float
 *  here made the editor rename the Blueprint copies instead (Speed_0 etc.).
 */
UCLASS()
class UProjectBopisAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:

	virtual void NativeInitializeAnimation() override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

	/** Kicks the recoil spring. Called by the character for every shot that fires. */
	void AddRecoil(bool bOffhand);

protected:

	// ---- Locomotion ----

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion")
	double Speed = 0.0;

	/** Travel direction relative to facing, -180..180. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion")
	double Direction = 0.0;

	/** Nearest of 0/90/-90/180, with hysteresis — drives which strafe clip plays. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion")
	double CardinalDirection = 0.0;

	/** What orientation warping rotates the legs by: Direction minus CardinalDirection. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion")
	double WarpAngle = 0.0;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion")
	double AimPitch = 0.0;

	/** Play rate of the lowered-dual whole-body walk/jog: LocomotionPlayRate scaled by
	    DualLoweredRateScale, since that unarmed clip has a quicker stride than the pistol
	    jog it has to match. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion")
	double DualLoweredPlayRate = 0.7;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion")
	bool bIsCrouched = false;

	// ---- Weapon and stance ----

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	EWeaponAnimType CurrentAnimType = EWeaponAnimType::Pistol;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	bool bIsWeaponRaised = false;

	/** Weight of the raised upper-body layer and the aim offsets. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	double UpperBodyAlpha = 0.0;

	/** Weight of the mirrored dual-wield left arm. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	double LeftArmAlpha = 0.0;

	/** Weight of the whole-body unarmed layer used for lowered dual pistols. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	double DualLoweredAlpha = 0.0;

	/** Weight of the two-handed left-hand IK onto the weapon. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	double LeftHandIKAlpha = 0.0;

	/** Where the left hand grips the weapon, relative to hand_r — from the weapon's
	    LeftHandGrip socket. The AnimGraph moves ik_hand_l here (in ik_hand_gun's space,
	    which is copied from hand_r) before the two-bone IK, replacing the clip's own
	    ik_hand_l, which assumes Lyra's rifle rather than our meshes. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	FVector LeftHandGripLocation = FVector::ZeroVector;

	/** 1 when the equipped weapon has a LeftHandGrip socket, else 0 — weapons without
	    one keep the clip's ik_hand_l. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	double LeftHandGripAlpha = 0.0;

	/** Any pistol-style hold (Pistol, PistolOneHanded or Dual) — the AnimGraph's
	    pistol-vs-long-gun switches (aim offset, hip-fire idle, crouch idle) read this
	    instead of == Pistol. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	bool bIsPistolHold = false;

	/** Dual wield, pistols or SMGs (the weapon's IsDualWield). Picks the spread raised idle
	    for the right arm; the dual left-arm and lowered-dual layers already key off it
	    through their alphas. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	bool bIsDualWield = false;

	/** Duals use the spread raised idle, except while aiming (ADS), where the original
	    narrower pose reads better. The AnimGraph's dual idle switches read this. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	bool bDualSpread = false;

	/** Weight of the one-handed pistol's free-arm pose (left hand at the side): only while
	    raised, eased out while reload-animating. Lowered, the one-handed clips own the arm. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	double FreeArmAlpha = 0.0;

	/** One-handed pistol: the free arm's procedural swing, read from the feet. A rotation
	    for the AnimGraph's upperarm_l Modify Bone (component space, additive). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	FRotator FreeArmSwingRotation = FRotator::ZeroRotator;
	// ---- Recoil ----

	/** Torso recoil, 0..1, every weapon. Weights a Transform (Modify) Bone on spine_05
	    whose own rotation is the full kick. Shots stack; the spring settles it. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Recoil")
	double SpineRecoilAlpha = 0.0;

	/** Gun-arm recoil, 0..1, pistol holds only. On a two-handed gun the torso carries
	    both arms instead, so the grip doesn't pull apart. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Recoil")
	double ArmRecoilAlpha = 0.0;

	/** Dual wield: left-arm recoil from off-hand shots. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Recoil")
	double OffhandArmRecoilAlpha = 0.0;

	/** One-handed pistol: recoil weight for the free arm, so it jolts with each shot.
	    Follows FreeArmAlpha, so it's off whenever the at-side pose is. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Recoil")
	double FreeArmRecoilAlpha = 0.0;

	/** Spring velocity one shot adds. Higher kicks harder; rapid shots stack up to full. */
	UPROPERTY(EditDefaultsOnly, Category = "Recoil")
	float RecoilImpulse = 15.0f;

	/** How hard the spring pulls back to rest. Higher recovers faster. */
	UPROPERTY(EditDefaultsOnly, Category = "Recoil")
	float RecoilStiffness = 150.0f;

	/** 1 eases back to rest; lower snaps back quicker. */
	UPROPERTY(EditDefaultsOnly, Category = "Recoil", meta = (ClampMin = "0.1", ClampMax = "1.0"))
	float RecoilDamping = 0.7f;

	// ---- Turn-in-place ----

	/** How far the mesh lags behind the capsule's yaw. Rotate Root Bone applies it;
	    the aim offsets twist the torso back to the camera by the same amount. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Turn In Place")
	double RootYawOffset = 0.0;

	UPROPERTY(EditDefaultsOnly, Category = "Turn In Place")
	TObjectPtr<UAnimMontage> TurnLeftMontage;

	UPROPERTY(EditDefaultsOnly, Category = "Turn In Place")
	TObjectPtr<UAnimMontage> TurnRightMontage;

	/** Lag past which a turn montage plays. Turn clips rotate 90 degrees. */
	UPROPERTY(EditDefaultsOnly, Category = "Turn In Place")
	float TurnThreshold = 90.0f;

	/** The mesh never lags further than this; beyond it the body is dragged along. */
	UPROPERTY(EditDefaultsOnly, Category = "Turn In Place")
	float MaxRootYawOffset = 120.0f;

	// ---- Tuning ----

	/** How fast the raised layer eases in, and eases out when it isn't snapping. */
	UPROPERTY(EditDefaultsOnly, Category = "Tuning")
	float UpperBodyInterpSpeed = 12.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Tuning")
	float LeftHandIKInterpSpeed = 10.0f;

	/** How fast RootYawOffset returns to zero once turning in place isn't allowed. */
	UPROPERTY(EditDefaultsOnly, Category = "Tuning")
	float RootYawRecoverySpeed = 10.0f;

	/** Below this speed the character counts as standing still. */
	UPROPERTY(EditDefaultsOnly, Category = "Tuning")
	float StationarySpeed = 10.0f;

	/** Play rate of every locomotion clip (free run, raised, aiming, crouch). Below 1 slows
	    the cadence for a heavier gait; stride warping (Graph mode) lengthens the steps to
	    match the capsule speed. Much below 0.75 and the stretched strides start to show. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Tuning", meta = (ClampMin = "0.5", ClampMax = "1.0"))
	double LocomotionPlayRate = 0.8;

	/** How much slower the lowered-dual unarmed walk/jog plays than the other locomotion
	    clips, so its cadence matches the one-handed pistol jog. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Tuning", meta = (ClampMin = "0.1", ClampMax = "1.0"))
	double DualLoweredRateScale = 0.7;

	/** Free-arm swing at full stride (left arm fully forward). Rotation in component space;
	    flip the sign or move it to another axis if the arm swings the wrong way. */
	UPROPERTY(EditDefaultsOnly, Category = "Tuning")
	FRotator FreeArmSwingFull = FRotator(0.0, 0.0, 25.0);

	/** Smallest fore-aft foot gap treated as a full stride (cm). The swing auto-scales to
	    the largest recent gap, so side-steps swing as fully as forward strides; this
	    floor stops near-still feet from being amplified into flapping. */
	UPROPERTY(EditDefaultsOnly, Category = "Tuning", meta = (ClampMin = "1.0"))
	float FreeArmMinStride = 8.0f;

	/** In the dive's own states (Start/Loop/Land/Prone) — the AnimGraph switches to the
	    Shootdodge state machine on this. False while getting up (a montage). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	bool bShootdodging = false;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	EShootdodgePhase ShootdodgePhase = EShootdodgePhase::None;

	/** Dive direction relative to the body, −180..180 — X of the Start/Loop/Land blend spaces. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgeDirection = 0.0f;

	/** Play rate for the current phase's blend space player. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgePlayRate = 1.0f;

	/** Normalised start position (0..1) for the current phase's blend space player. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgeStartPosition = 0.0f;

	/** Prone aim: camera yaw relative to the body (−180..180) and camera pitch. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgeAimYaw = 0.0f;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgeAimPitch = 0.0f;

	/** X of the prone blend space. Follows ShootdodgeDirection, except across the front span:
	    blends between Fwd and Fwd_Left/Right sink the legs, so the pose holds the diagonal and
	    only swaps to Fwd once the direction comes close to straight ahead. Eased at
	    PronePoseSwapSpeed, so a swap is a slow transition rather than a jump. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ProneBlendDirection = 0.0f;

	/** While the pose is off the real direction: the whole body turns by this so it still
	    lies along the dive... */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ProneBodyTurn = FRotator::ZeroRotator;

	/** ...and the spine turns back by this, on each of two spine bones, so the gun still
	    points at the aim. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ProneSpineCounterTurn = FRotator::ZeroRotator;

	/** How close to straight ahead (degrees) the direction has to come before the prone pose
	    swaps from the diagonal to Fwd. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "45.0"))
	float ProneForwardSnapAngle = 10.0f;

	/** Between Right/Left and Bwd_Right/Left the prone pose holds the back diagonal, and only
	    swaps to Right/Left once the direction is within this many degrees of it. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "45.0"))
	float ProneSideSnapAngle = 22.5f;

	/** Extra degrees before either swap goes back, so it doesn't flicker at the edge. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float ProneForwardSnapHysteresis = 5.0f;

	/** How fast the prone pose eases toward where it should be — a swap's transition speed.
	    Lower is slower. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float PronePoseSwapSpeed = 5.0f;

	/** Component-space foot IK targets mid-swap across the front: each foot as animated,
	    raised with the hips and above the floor. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FVector ProneFootTargetL = FVector::ZeroVector;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FVector ProneFootTargetR = FVector::ZeroVector;

	/** Weight of the mid-swap leg fix (torso lift and foot IK): 0 on every authored prone
	    pose, peaking halfway between Fwd and Fwd_Left/Right; 0 everywhere else. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	double ProneFootIKAlpha = 0.0;

	/** Component-space lift for the pelvis mid-swap: the whole torso comes up by what the
	    lower knee needs to clear the floor. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FVector ProneHipLift = FVector::ZeroVector;

	/** How high above the floor the knee joint (calf bone) has to stay mid-swap. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float ProneKneeClearance = 7.0f;

	/** How high above the floor the ankle bone has to stay mid-swap (roughly the ankle's
	    height above the heel). */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float ProneFootClearance = 10.0f;

private:

	void UpdateShootdodgeAim(const ABopisCharacterBase& Character, float DeltaSeconds);
	void UpdateProneDirection(float DeltaSeconds);
	void UpdateProneFeet(const ABopisCharacterBase& Character, float DeltaSeconds);

	/** How far Point sits below the floor plus Clearance (cm), 0 if it's clear or there's no floor. */
	float FloorShortfall(const USkeletalMeshComponent& Mesh, const FVector& Point, float Clearance) const;
	void UpdateLocomotion(const ABopisCharacterBase& Character);
	void UpdateUpperBody(float DeltaSeconds);
	void UpdateArmAlphas(const AWeaponBase* Weapon, float DeltaSeconds);
	void UpdateLeftHandGrip(const ABopisCharacterBase& Character, const AWeaponBase* Weapon);
	void UpdateTurnInPlace(float ActorYaw, float DeltaSeconds);
	void UpdateRecoil(float DeltaSeconds);
	void UpdateFreeArmSwing(float DeltaSeconds);

	/** Smoothed -1..1 swing phase: + when the right foot leads. */
	float FreeArmSwingPhase = 0.0f;

	/** Recent largest fore-aft foot gap — the swing's auto-gain. Decays slowly. */
	float FreeArmStridePeak = 0.0f;

	/** Latched while a fire/reload montage plays and until the drop it causes has
	    finished easing — so a montage ending eases the arms down instead of snapping. */
	bool bEaseLowering = false;

	/** A reload montage is playing (End included) — the left-hand IK stays off. */
	bool bReloadAnimating = false;

	/** Aim button held (ADS) — not hip-fire raises. The left-hand IK only runs while aiming. */
	bool bIsAiming = false;
	bool bWasWeaponRaised = false;
	float LastActorYaw = 0.0f;
	float PrevTurnYawCurve = 0.0f;

	/** Fraction of a 90-degree turn clip the current turn should cover. */
	float TurnScale = 1.0f;

	/** Eased 0..1 version of bIsCrouched that fades the standing lowered-dual layer out
	    while crouched, so standing up blends it back in instead of snapping. */
	float DualCrouchBlend = 0.0f;

	/** Eased 0..1 that fades the one-handed free-arm pose out while a reload montage plays
	    and back in after, so the left arm doesn't snap between the pose and the reload. */
	float FreeArmReloadBlend = 1.0f;

	/** Raw spring values behind the recoil alphas: main hand and off hand. */
	float MainRecoil = 0.0f;
	float OffhandRecoil = 0.0f;
	FFloatSpringState MainRecoilSpring;
	FFloatSpringState OffhandRecoilSpring;

	/** The front-span prone pose is on (or heading for) Fwd rather than a diagonal. */
	bool bProneHoldingForward = false;

	/** The back-side prone pose (between Right/Left and Bwd_Right/Left) is on (or heading for)
	    Right/Left rather than the back diagonal. */
	bool bProneHoldingSide = false;
};
