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
	void AddRecoil(bool bOffhand, float Strength = 1.0f);

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

	/** CardinalDirection negated: what the mirrored strafe copy is fed, so its mirrored feet
	    step the way the character is actually moving. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion|Blade")
	double CardinalDirectionMirrored = 0.0;

	/** Weight of the bladed (mirrored) lower body: one-handed pistol, raised, standing; eased. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion|Blade")
	float StrafeBladeAlpha = 0.0f;

	/** Weight of a grenade toss: the blade's upper-body turns ease out under it (not the legs). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion|Blade")
	float ThrowAlpha = 0.0f;

	/** Weight of the hand turn that points a two-handed pistol at the crosshair from the hip
	    (the blade's hand turn, without its chest and arm turns). Eased. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion|Blade")
	float HipAimHandAlpha = 0.0f;

	/** How fast (per second) the blade's turns ease out for a throw, and back after. */
	UPROPERTY(EditDefaultsOnly, Category = "Locomotion|Blade", meta = (ClampMin = "0.1"))
	float ThrowBladeBlendSpeed = 8.0f;

	/** The one-handed pistol's raised stance blades the other way: hips and feet mirrored,
	    right hand forward. */
	UPROPERTY(EditDefaultsOnly, Category = "Locomotion|Blade")
	bool bBladeStance = true;

	/** Bladed stance: how far the chest turns about the vertical (degrees) so the right shoulder
	    leads; half on spine_03, half on spine_05. The head turns back by the same. Negative turns
	    the other way. */
	UPROPERTY(EditDefaultsOnly, Category = "Locomotion|Blade", meta = (ClampMin = "-90.0", ClampMax = "90.0"))
	float BladeAngle = 35.0f;

	/** Most the gun arm turns from the shoulder (degrees) to point at the aim. */
	UPROPERTY(EditDefaultsOnly, Category = "Locomotion|Blade", meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float BladeArmMaxAngle = 60.0f;

	/** Half the chest turn, for each of spine_03 and spine_05 (component space, added). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion|Blade")
	FRotator BladeSpineTurn = FRotator::ZeroRotator;

	/** Half the head's turn back to the target, for each of neck_01 and head (component space, added). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion|Blade")
	FRotator BladeHeadTurn = FRotator::ZeroRotator;

	/** The gun arm's turn (upperarm_r, component space, added): the shoulder-to-hand line pointed at
	    the aim point, the arm held as the pose has it. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion|Blade")
	FRotator BladeArmTurn = FRotator::ZeroRotator;

	/** The gun hand's turn (hand_r, component space, added), after the arm's: lines the barrel up
	    with the crosshair. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Locomotion|Blade")
	FRotator BladeHandTurn = FRotator::ZeroRotator;

	/** Most the gun hand turns (degrees) to line the barrel up. */
	UPROPERTY(EditDefaultsOnly, Category = "Locomotion|Blade", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float BladeHandMaxAngle = 45.0f;

	/** Travel further than this from forward (degrees) always plays the backstep clips, however
	    the strafe got there — a side clip warped round past it twists the torso. */
	UPROPERTY(EditDefaultsOnly, Category = "Locomotion", meta = (ClampMin = "90.0", ClampMax = "180.0"))
	float BackstepMinAngle = 105.0f;

	/** Once backstepping, stays so until the travel comes this much further forward than
	    BackstepMinAngle — no flicker at the edge. */
	UPROPERTY(EditDefaultsOnly, Category = "Locomotion", meta = (ClampMin = "0.0", ClampMax = "45.0"))
	float BackstepHysteresis = 10.0f;

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

	/** Crouched turns. Without both, a crouched body doesn't turn in place (it turns
	    rigidly with the capsule). */
	UPROPERTY(EditDefaultsOnly, Category = "Turn In Place")
	TObjectPtr<UAnimMontage> CrouchTurnLeftMontage;

	UPROPERTY(EditDefaultsOnly, Category = "Turn In Place")
	TObjectPtr<UAnimMontage> CrouchTurnRightMontage;

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

	/** Weight of the dive branch's upper-body montage layer (reload or equip) over the dive and
	    prone poses (the AnimGraph's layered blend, from the clavicles down): eased in while
	    either plays, out after. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ProneReloadAlpha = 0.0f;

	/** Duals: weight of the mirrored off-hand montage on the left arm in the dive branch (the
	    standing branch's mirrored off-hand pose) — ProneReloadAlpha while dual-wielding, else 0. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ProneDualOffhandAlpha = 0.0f;

	/** Weight of the whole-arm dive/prone reload layer (LayeredBoneBlend_8): ProneReloadAlpha
	    less the face-down part, which takes only the forearms. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge|Prone")
	float ProneArmReloadAlpha = 0.0f;

	/** Face-down reloads: only the forearms and hands take the reload, the upper arms stay out
	    in front as the prone pose has them (the forearm layer)... */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge|Prone")
	float ProneForearmReloadAlpha = 0.0f;

	/** ...and, for duals, the left forearm takes the off-hand's mirrored reload. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge|Prone")
	float ProneForearmDualAlpha = 0.0f;

	/** Long guns reloading face-down: both upper arms raised (about the shoulders' line), so the
	    forearm reload and the gun come up off the floor. On upperarm_l and upperarm_r
	    (component space, added). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge|Prone")
	FRotator ProneLongGunArmRaise = FRotator::ZeroRotator;

	/** How far the upper arms raise for a face-down long-gun reload (degrees). */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge|Prone", meta = (ClampMin = "0.0", ClampMax = "80.0"))
	float ProneLongGunArmRaiseAngle = 30.0f;

	/** How fast ProneReloadAlpha eases in and out (per second; 6 ≈ 0.17 s). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Tuning", meta = (ClampMin = "0.1"))
	float ProneReloadBlendSpeed = 6.0f;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	EShootdodgePhase ShootdodgePhase = EShootdodgePhase::None;

	/** Dive direction relative to the body, −180..180 — X of the Start/Loop/Land blend spaces. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgeDirection = 0.0f;

	/** Play rate for the current phase's blend space player. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgePlayRate = 1.0f;

	/** Normalised start position (0..1) for the current phase's blend space player (the Land
	    state; the Start state uses ShootdodgeStartTime). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgeStartPosition = 0.0f;

	/** The Start clip's time, 0..1 (see UShootdodgeComponent::GetStartNormalizedTime): drives
	    the Start state's blend space evaluator. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	float ShootdodgeStartTime = 0.0f;

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

	/** Duals and long guns reloading prone on a side: the lower arm has no room, so the pose
	    goes to the back-prone one for the reload (at this speed) and returns after. Face-down
	    and on the back they reload where they lie, as do the single pistols. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.1"))
	float ProneDualReloadSwapSpeed = 8.0f;

	/** Prone directions within this of straight ahead (degrees) are face-down: no flip there
	    (the roll from the front was too big a move)... */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "180.0"))
	float ProneFrontMaxAngle = 45.0f;

	/** ...and this far from straight ahead or more are on the back already. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "180.0"))
	float ProneSideMaxAngle = 150.0f;

	/** The back-pose reload's weight (eased): the aim is ignored under it — no spine
	    counter-turn, no pitch — so the reload plays looking along the legs. */
	float ProneNeutralAlpha = 0.0f;

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

	/** Shootdodge aim correction, on each of two spine bones (component space): turns the upper
	    body so the gun points at the crosshair, whatever the dive or prone pose aims at. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeAimCorrection = FRotator::ZeroRotator;

	/** Long guns in a shootdodge: weight of their arm hold (the rifle hip-fire pose from the
	    clavicles down, layered over the pistol dive) and of the left hand's IK onto the
	    weapon's grip. 0 for pistols and outside the dive. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	double ShootdodgeLongGunAlpha = 0.0;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	double ShootdodgeLeftHandAlpha = 0.0;

	/** Long guns' share of the aim correction: on each of the chest bones (spine_04/05), each
	    upper arm, and each of neck_01/head (component space). The pistol share stays on
	    ShootdodgeAimCorrection; each fades with ShootdodgeLongGunAlpha. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeChestAimCorrection = FRotator::ZeroRotator;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeArmAimCorrection = FRotator::ZeroRotator;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeHeadCorrection = FRotator::ZeroRotator;

	/** Duals in a shootdodge: weight of the left arm's own one-handed hold (a mirrored pistol
	    hip-fire arm, replacing the dive's two-handed clasp), and the left gun's own aim
	    correction on upperarm_l (component space). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	double ShootdodgeDualAlpha = 0.0;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeOffhandAimCorrection = FRotator::ZeroRotator;

	/** Head look outside the shootdodge (an enemy searching with its gun down): half the turn
	    on each of neck_01 and head (component space, added to the pose). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Head Look")
	FRotator HeadLookRotation = FRotator::ZeroRotator;

	/** Most the head turns toward its target across the ground, in degrees. Past it, it holds at the limit. */
	UPROPERTY(EditDefaultsOnly, Category = "Head Look", meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float HeadLookMaxYaw = 70.0f;

	/** Most it tilts up or down toward the target, in degrees. */
	UPROPERTY(EditDefaultsOnly, Category = "Head Look", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float HeadLookMaxPitch = 30.0f;

	/** A target further round than this (behind the shoulder) isn't looked at: the head comes
	    back forward rather than straining. */
	UPROPERTY(EditDefaultsOnly, Category = "Head Look", meta = (ClampMin = "0.0", ClampMax = "180.0"))
	float HeadLookGiveUpAngle = 130.0f;

	/** How quickly the head turns to its target, and back. */
	UPROPERTY(EditDefaultsOnly, Category = "Head Look", meta = (ClampMin = "0.0"))
	float HeadLookSpeed = 5.0f;

	/** Pistols lying back: the arms' lift (on each upper arm) and the hands' matching turn back
	    (on each hand), component space — the guns rise off the hips without changing aim. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeArmLift = FRotator::ZeroRotator;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeHandCounterLift = FRotator::ZeroRotator;

	/** The left arm's own lift and hand counter-turn (duals lift it further, about its own gun). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeArmLiftL = FRotator::ZeroRotator;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "Shootdodge")
	FRotator ShootdodgeHandCounterLiftL = FRotator::ZeroRotator;

	/** Long guns' own back-pose lift, in degrees (the rifle hold sits low across the legs too). */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float LongGunBackLiftAngle = 30.0f;

	/** Duals: how much further the left arm lifts in the back poses, in degrees — its
	    one-handed hold sits lower and would clip the legs. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float BackOffhandExtraLift = 20.0f;

	/** Duals in a shootdodge: how far each arm swings out to its own side of the screen, in
	    degrees, so the guns clear the head and body from behind the shoulder. The hands turn
	    back by the same, so the guns still point where they did. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "60.0"))
	float DualDiveSpreadAngle = 20.0f;

	/** How far the arms lift the guns in the back poses, in degrees (full from 135° round to
	    straight back, nothing at the side poses). */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float BackGunLiftAngle = 35.0f;

	/** Duals: most the left arm turns to aim the left gun, in degrees. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float OffhandAimMaxAngle = 60.0f;

	/** Long guns: most the chest tilts (up/down) and turns (about the vertical) to aim, in
	    degrees — beyond them a lying body bends over. The arms do the rest. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float LongGunMaxPitch = 20.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float LongGunMaxYaw = 35.0f;

	/** Long guns: most the arms turn on top of the chest, in degrees. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float LongGunArmMaxAngle = 60.0f;

	/** Long guns: most the head turns to look at the target, in degrees. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float HeadLookMaxAngle = 60.0f;

	/** After the Start, how fast (degrees per second) the dive's blend space direction catches
	    up from the take-off direction to the live one — a jog's forward jump easing into the
	    flight's real direction, rather than the blend space snapping round. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "1.0"))
	float ShootdodgeDirectionCatchUpRate = 720.0f;

	/** Pistols and duals: how far down / up (degrees from level) the dive and prone poses
	    follow the aim. Past it the guns hold at the limit; the shots still go from the muzzle to
	    the crosshair's point. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "-89.0", ClampMax = "0.0"))
	float ShootdodgeAimPitchMin = -35.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "89.0"))
	float ShootdodgeAimPitchMax = 45.0f;

	/** Long guns' own down / up limits for the same (rifles, shotguns; head included). */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "-89.0", ClampMax = "0.0"))
	float LongGunAimPitchMin = -35.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "89.0"))
	float LongGunAimPitchMax = 45.0f;

	/** Furthest the aim correction turns the upper body, in degrees. Past it the gun stays off. */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float AimCorrectionMaxAngle = 70.0f;

	/** How quickly the correction closes the gap (interp speed; higher is snappier). */
	UPROPERTY(EditDefaultsOnly, Category = "Shootdodge", meta = (ClampMin = "0.0"))
	float AimCorrectionSpeed = 12.0f;

private:

	void UpdateShootdodgeAimCorrection(const ABopisCharacterBase& Character, const AWeaponBase* Weapon, float DeltaSeconds);

	/** The shootdodge's up/down aim limits for the gun in hand: long guns' or pistols'. */
	float AimPitchMin() const { return bIsPistolHold ? ShootdodgeAimPitchMin : LongGunAimPitchMin; }
	float AimPitchMax() const { return bIsPistolHold ? ShootdodgeAimPitchMax : LongGunAimPitchMax; }

	/** The full aim correction (both spine bones together), component space. */
	FQuat AimCorrectionTotal = FQuat::Identity;

	/** Long guns: the arms' extra tilt, and the head's turn (both bones together). */
	FQuat ArmAimCorrectionTotal = FQuat::Identity;
	FQuat HeadCorrectionTotal = FQuat::Identity;

	/** Duals: the left arm's turn for the left gun. */
	FQuat OffhandAimCorrectionTotal = FQuat::Identity;

	/** The back poses' gun lift right now, eased (degrees). */
	float GunLiftAngle = 0.0f;

	/** Duals: the left arm's extra lift right now, eased (degrees). */
	float OffhandExtraLiftAngle = 0.0f;

	/** Which way the head bone faces, in its own space — from the reference pose, found once. */
	FVector HeadLocalForward = FVector::ZeroVector;

	/** The whole head turn, eased; HeadLookRotation is half of it. */
	FQuat HeadLookTotal = FQuat::Identity;

	void UpdateHeadLook(const ABopisCharacterBase& Character, float DeltaSeconds);

	void UpdateBlade(const ABopisCharacterBase& Character, const AWeaponBase* Weapon, float DeltaSeconds);

	/** The gun arm's whole turn, eased; BladeArmTurn is it as a rotator. */
	FQuat BladeArmTotal = FQuat::Identity;

	/** The gun hand's whole turn, eased; BladeHandTurn is it as a rotator. */
	FQuat BladeHandTotal = FQuat::Identity;

	void UpdateShootdodgeAim(const ABopisCharacterBase& Character, float DeltaSeconds);
	void UpdateProneDirection(float DeltaSeconds);

	/** Splits the prone reload between the whole-arm and the face-down forearm layers. */
	void UpdateProneReloadLayers(float DeltaSeconds);

	/** Face-down prone, eased (0 elsewhere): how much of the reload is forearms-only. */
	float ProneFrontAlpha = 0.0f;
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

	/** A reload montage is playing (End included) — the left-hand IK stays off, and the
	    prone branch borrows the upper-body slot's arms. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon", meta = (AllowPrivateAccess = "true"))
	bool bReloadAnimating = false;

	/** An equip montage is playing (the pull-out): the free arm eases out for it, as for a reload. */
	bool bEquipAnimating = false;

	/** The owner is turning to throw or mid-toss (see AProjectBopisCharacter::IsThrowingGrenade). */
	bool bThrowingGrenade = false;

	/** Aim button held (ADS) — not hip-fire raises. The left-hand IK only runs while aiming. */
	bool bIsAiming = false;
	bool bWasWeaponRaised = false;
	float LastActorYaw = 0.0f;

	/** The character is turning to the camera as the gun comes up: no turn-in-place then. */
	bool bTurningToAim = false;
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
