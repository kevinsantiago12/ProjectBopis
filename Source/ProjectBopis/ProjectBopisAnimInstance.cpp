// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProjectBopisAnimInstance.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"

namespace
{
	const FName DefaultSlotName(TEXT("DefaultSlot"));
	const FName TurnSlotName(TEXT("TurnSlot"));
	const FName TurnGroupName(TEXT("TurnGroup"));

	// Curves authored on the Lyra turn clips.
	const FName TurnYawWeightCurve(TEXT("TurnYawWeight"));
	const FName RemainingTurnYawCurve(TEXT("RemainingTurnYaw"));

	const FName LeftHandGripSocket(TEXT("LeftHandGrip"));
	const FName RightHandBone(TEXT("hand_r"));

	/** Direction has to move this far from the current cardinal before the cardinal
	    changes — a 10-degree dead zone past each 45-degree boundary. */
	constexpr float CardinalSwitchAngle = 55.0f;

	/** Turn-in-place only runs below this speed — stricter than StationarySpeed, so a
	    slow start cancels the turn. */
	constexpr float TurnInPlaceMaxSpeed = 5.0f;

	constexpr float TurnCancelBlendOut = 0.2f;
}

void UProjectBopisAnimInstance::NativeInitializeAnimation()
{
	Super::NativeInitializeAnimation();

	// Seed from the real facing, or the first frame reads the whole spawn yaw as a
	// camera swing and the body starts twisted.
	if (const APawn* Pawn = TryGetPawnOwner())
	{
		LastActorYaw = Pawn->GetActorRotation().Yaw;
	}
}

void UProjectBopisAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);

	// No pawn in the AnimBP editor preview; everything stays at its defaults.
	const AProjectBopisCharacter* Character = Cast<AProjectBopisCharacter>(TryGetPawnOwner());
	if (!Character)
	{
		return;
	}

	const UWeaponHolderComponent* Holder = Character->GetWeaponHolder();
	const AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr;

	UpdateLocomotion(*Character);

	bIsWeaponRaised = Character->IsWeaponRaised();
	bIsCrouched = Character->bIsCrouched;
	bReloadAnimating = Character->IsReloadAnimating();
	bIsAiming = Character->IsAiming();

	if (Weapon)
	{
		CurrentAnimType = Weapon->GetAnimType();
		bIsDualWield = Weapon->IsDualWield();
	}

	UpdateUpperBody(DeltaSeconds);
	UpdateLeftHandGrip(*Character, Weapon);
	UpdateArmAlphas(Weapon, DeltaSeconds);
	UpdateTurnInPlace(Character->GetActorRotation().Yaw, DeltaSeconds);
}

void UProjectBopisAnimInstance::UpdateLocomotion(const AProjectBopisCharacter& Character)
{
	const FVector Velocity = Character.GetVelocity();
	Speed = Velocity.Size();

	// Travel direction relative to where the character faces.
	Direction = Speed > UE_KINDA_SMALL_NUMBER
		? FRotator::NormalizeAxis(Velocity.Rotation().Yaw - Character.GetActorRotation().Yaw)
		: 0.0f;

	// Hysteresis stops the strafe clip flickering between two cardinals on a diagonal.
	if (FMath::Abs(FRotator::NormalizeAxis(Direction - CardinalDirection)) > CardinalSwitchAngle)
	{
		CardinalDirection = FMath::GridSnap(Direction, 90.0);
	}

	// Orientation warping rotates the legs by whatever the cardinal clip doesn't cover.
	WarpAngle = FRotator::NormalizeAxis(Direction - CardinalDirection);

	AimPitch = FRotator::NormalizeAxis(Character.GetControlRotation().Pitch);
}

void UProjectBopisAnimInstance::UpdateUpperBody(float DeltaSeconds)
{
	// Fire and reload play in DefaultSlot. Turn montages use their own slot and
	// deliberately don't count.
	const bool bMontageActive = IsSlotActive(DefaultSlotName);

	const float Target = (bIsWeaponRaised || bMontageActive) ? 1.0f : 0.0f;
	const bool bLowering = Target < UpperBodyAlpha;

	bEaseLowering = bMontageActive || (bEaseLowering && bLowering);

	// Easing the layer out drags a two-handed grip's left arm through the torso, so
	// that one case snaps — only standing still and upright. Moving, the legs carry the
	// change; crouched, the snap reads as a pop. Duals have no shared grip and always
	// ease; so does the drop after a montage.
	const bool bSnap = bLowering
		&& !bEaseLowering
		&& !bIsDualWield
		&& !bIsCrouched
		&& Speed < StationarySpeed;

	UpperBodyAlpha = bSnap
		? Target
		: FMath::FInterpTo(UpperBodyAlpha, Target, DeltaSeconds, UpperBodyInterpSpeed);
}

void UProjectBopisAnimInstance::UpdateArmAlphas(const AWeaponBase* Weapon, float DeltaSeconds)
{
	if (!Weapon)
	{
		return;
	}

	// Duals: the mirrored left arm follows the raised layer. Crouched duals hold both
	// guns up, since the lowered-dual layer is a standing pose — blended by the eased
	// crouch so standing up lowers the guns smoothly.
	DualCrouchBlend = FMath::FInterpTo(
		DualCrouchBlend, bIsCrouched ? 1.0f : 0.0f, DeltaSeconds, UpperBodyInterpSpeed);

	LeftArmAlpha = bIsDualWield
		? FMath::Lerp(UpperBodyAlpha, 1.0, DualCrouchBlend)
		: 0.0;

	DualLoweredAlpha = bIsDualWield
		? (1.0 - UpperBodyAlpha) * (1.0 - DualCrouchBlend)
		: 0.0;

	// Left-hand IK: long guns only, and only while aiming (ADS). Every other pose —
	// lowered, hip-fire raised, moving, pistols — keeps its hand-authored left hand.
	// Target: the weapon's LeftHandGrip socket, else the clip's ik_hand_l. Off while
	// reload-animating. Eases on, snaps off.
	const bool bLongGun = CurrentAnimType != EWeaponAnimType::Pistol;
	const double IKTarget = (bIsAiming && bLongGun && !bIsDualWield && !bReloadAnimating) ? 1.0 : 0.0;

	LeftHandIKAlpha = IKTarget < LeftHandIKAlpha
		? IKTarget
		: FMath::FInterpTo(LeftHandIKAlpha, IKTarget, DeltaSeconds, LeftHandIKInterpSpeed);
}

void UProjectBopisAnimInstance::UpdateLeftHandGrip(const AProjectBopisCharacter& Character, const AWeaponBase* Weapon)
{
	const USkeletalMeshComponent* WeaponMesh = Weapon ? Weapon->GetWeaponMesh() : nullptr;
	const USkeletalMeshComponent* BodyMesh = Character.GetMesh();

	if (!WeaponMesh || !BodyMesh || !WeaponMesh->DoesSocketExist(LeftHandGripSocket))
	{
		LeftHandGripAlpha = 0.0;
		return;
	}

	// The weapon rides hand_r rigidly, so the socket's offset from hand_r is constant;
	// re-applied relative to this frame's hand in the AnimGraph.
	const FTransform GripWorld = WeaponMesh->GetSocketTransform(LeftHandGripSocket);
	const FTransform HandWorld = BodyMesh->GetSocketTransform(RightHandBone);

	LeftHandGripLocation = GripWorld.GetRelativeTransform(HandWorld).GetLocation();
	LeftHandGripAlpha = 1.0;
}

void UProjectBopisAnimInstance::UpdateTurnInPlace(float ActorYaw, float DeltaSeconds)
{
	const float YawDelta = FRotator::NormalizeAxis(ActorYaw - LastActorYaw);
	LastActorYaw = ActorYaw;

	// The raise frame doesn't count — firing snaps the capsule to the camera on purpose,
	// and the body should snap with it rather than start a turn.
	const bool bCanTurn = bIsWeaponRaised
		&& bWasWeaponRaised
		&& Speed < TurnInPlaceMaxSpeed
		&& !bIsCrouched;

	bWasWeaponRaised = bIsWeaponRaised;

	if (bCanTurn)
	{
		// The capsule follows the camera; counter-rotate the mesh so the feet stay planted.
		RootYawOffset = FMath::Clamp(
			FRotator::NormalizeAxis(RootYawOffset - YawDelta), -MaxRootYawOffset, MaxRootYawOffset);
	}
	else
	{
		RootYawOffset = FMath::FInterpTo(RootYawOffset, 0.0f, DeltaSeconds, RootYawRecoverySpeed);
	}

	// While a turn clip plays, its RemainingTurnYaw curve counts down; winding the offset
	// by the same amount keeps the feet in sync with the clip's steps. Dividing by the
	// weight undoes the montage blend scaling the curve.
	const float TurnWeight = GetCurveValue(TurnYawWeightCurve);
	const bool bTurning = TurnWeight > 0.01f;
	const float TurnYawCurve = bTurning ? GetCurveValue(RemainingTurnYawCurve) / TurnWeight : 0.0f;

	if (bTurning && !FMath::IsNearlyZero(PrevTurnYawCurve, 0.001f))
	{
		RootYawOffset -= (TurnYawCurve - PrevTurnYawCurve) * TurnScale;
	}
	PrevTurnYawCurve = TurnYawCurve;

	if (!bCanTurn)
	{
		// Montage_Stop with no montage would stop fire/reload too; the group only holds turns.
		Montage_StopGroupByName(TurnCancelBlendOut, TurnGroupName);
		return;
	}

	if (FMath::Abs(RootYawOffset) > TurnThreshold && !IsSlotActive(TurnSlotName))
	{
		// A turn should close exactly the gap that triggered it, not always 90 degrees.
		TurnScale = static_cast<float>(FMath::Abs(RootYawOffset) / 90.0);

		// Negative offset: the body lags left of the camera, so it steps right.
		UAnimMontage* TurnMontage = RootYawOffset < 0.0f ? TurnRightMontage : TurnLeftMontage;
		if (TurnMontage)
		{
			// bStopAllMontages = false, or starting a turn would cancel fire/reload.
			Montage_Play(TurnMontage, 1.0f, EMontagePlayReturnType::MontageLength, 0.0f, false);
		}
	}
}
