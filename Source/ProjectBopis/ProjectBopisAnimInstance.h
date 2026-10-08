// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Kismet/KismetMathLibrary.h"
#include "Weapons/WeaponBase.h"
#include "ProjectBopisAnimInstance.generated.h"

class AProjectBopisCharacter;
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

private:

	void UpdateLocomotion(const AProjectBopisCharacter& Character);
	void UpdateUpperBody(float DeltaSeconds);
	void UpdateArmAlphas(const AWeaponBase* Weapon, float DeltaSeconds);
	void UpdateLeftHandGrip(const AProjectBopisCharacter& Character, const AWeaponBase* Weapon);
	void UpdateTurnInPlace(float ActorYaw, float DeltaSeconds);
	void UpdateRecoil(float DeltaSeconds);

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
};
