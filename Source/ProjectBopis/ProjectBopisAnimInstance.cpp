// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProjectBopisAnimInstance.h"
#include "BopisCharacterBase.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/ShootdodgeComponent.h"
#include "Gameplay/RollComponent.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "AnimationRuntime.h"

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

	// The dive's blend space players (the Land state's) read their start position once, when they
	// first initialize — before the shootdodge component's BeginPlay, and before any per-frame
	// copy. Seed it so that first read isn't 0. (The Start state runs on ShootdodgeStartTime.)
	if (const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(TryGetPawnOwner()))
	{
		if (const UShootdodgeComponent* Shootdodge = Player->GetShootdodge())
		{
			ShootdodgeStartPosition = Shootdodge->GetRestStartPosition();
		}
	}
}

void UProjectBopisAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);

	// No pawn in the AnimBP editor preview; everything stays at its defaults.
	const ABopisCharacterBase* Character = Cast<ABopisCharacterBase>(TryGetPawnOwner());
	if (!Character)
	{
		return;
	}

	const UWeaponHolderComponent* Holder = Character->GetWeaponHolder();
	const AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr;

	UpdateLocomotion(*Character);

	bIsWeaponRaised = Character->IsWeaponRaised() && !Character->IsWeaponBlocked();
	const AProjectBopisCharacter* Hero = Cast<AProjectBopisCharacter>(Character);
	bTurningToAim = Hero && Hero->IsTurningToAim();
	bIsCrouched = Character->bIsCrouched;
	bReloadAnimating = Character->IsReloadAnimating();
	bEquipAnimating = Character->IsEquipAnimating();
	// The dive branch's upper-body layer (the reload/equip montages over the dive and prone
	// poses) is up for either — a mid-air quick reload or quick draw.
	const bool bUpperBodyMontage = bReloadAnimating || Character->IsEquipAnimating();
	ProneReloadAlpha = FMath::FInterpConstantTo(ProneReloadAlpha, bUpperBodyMontage ? 1.0f : 0.0f,
		DeltaSeconds, ProneReloadBlendSpeed);
	bIsAiming = Character->IsAiming() && !Character->IsWeaponBlocked();

	if (Weapon)
	{
		CurrentAnimType = Weapon->GetAnimType();
		bIsPistolHold = IsPistolAnimType(CurrentAnimType);
		bIsDualWield = Weapon->IsDualWield();
	}

	bDualSpread = bIsDualWield && !bIsAiming;

	// The one-handed pistol's bladed stance: the mirrored strafe copy reads the negated direction,
	// and fades in with the raised stance (standing, not diving).
	CardinalDirectionMirrored = -CardinalDirection;
	const bool bBlade = bBladeStance && Character->IsPlayerControlled()
		&& CurrentAnimType == EWeaponAnimType::PistolOneHanded
		&& bIsWeaponRaised && !bIsCrouched && !bShootdodging;
	StrafeBladeAlpha = FMath::FInterpTo(StrafeBladeAlpha, bBlade ? 1.0f : 0.0f, DeltaSeconds, UpperBodyInterpSpeed);

	// A grenade toss takes the upper body: the blade's turns ease out under it; the legs stay.
	bThrowingGrenade = Hero && Hero->IsThrowingGrenade();
	ThrowAlpha = FMath::FInterpConstantTo(ThrowAlpha, bThrowingGrenade ? 1.0f : 0.0f,
		DeltaSeconds, ThrowBladeBlendSpeed);

	// Two-handed holds at the hip (pistol, rifles, shotguns, the launcher): their poses don't
	// point the barrel at the crosshair, so the hand is turned to it as the blade does. Aimed
	// (ADS), the sight poses already line up.
	const bool bTwoHandedHold = !bIsDualWield && CurrentAnimType != EWeaponAnimType::PistolOneHanded;
	const bool bHipAimHand = Character->IsPlayerControlled() && bTwoHandedHold
		&& bIsWeaponRaised && !bIsAiming && !bShootdodging
		&& !bReloadAnimating && !bEquipAnimating && !bThrowingGrenade;
	HipAimHandAlpha = FMath::FInterpTo(HipAimHandAlpha, bHipAimHand ? 1.0f : 0.0f, DeltaSeconds, UpperBodyInterpSpeed);

	UpdateUpperBody(DeltaSeconds);
	UpdateLeftHandGrip(*Character, Weapon);
	UpdateArmAlphas(Weapon, DeltaSeconds);
	UpdateFreeArmSwing(DeltaSeconds);
	UpdateRecoil(DeltaSeconds);
	UpdateTurnInPlace(Character->GetActorRotation().Yaw, DeltaSeconds);
	UpdateShootdodgeAim(*Character, DeltaSeconds);
	UpdateProneDirection(DeltaSeconds);
	UpdateProneReloadLayers(DeltaSeconds);
	UpdateProneFeet(*Character, DeltaSeconds);
	UpdateShootdodgeAimCorrection(*Character, Weapon, DeltaSeconds);
	UpdateHeadLook(*Character, DeltaSeconds);
	UpdateBlade(*Character, Weapon, DeltaSeconds);
	UpdateLean(*Character, DeltaSeconds);
	UpdateFootsteps(*Character);
}

void UProjectBopisAnimInstance::UpdateFootsteps(const ABopisCharacterBase& Character)
{
	const USkeletalMeshComponent* Body = GetSkelMeshComponent();
	USkeletalMesh* MeshAsset = Body ? Body->GetSkeletalMeshAsset() : nullptr;
	if (!MeshAsset)
	{
		return;
	}

	// Rest heights from the reference pose, once per mesh (Manny and the CC bodies differ).
	if (FootRestMesh.Get() != MeshAsset)
	{
		const FReferenceSkeleton& RefSkeleton = MeshAsset->GetRefSkeleton();
		auto RestHeight = [&](FName Bone)
		{
			const int32 Index = RefSkeleton.FindBoneIndex(Bone);
			return Index != INDEX_NONE ? FAnimationRuntime::GetComponentSpaceTransformRefPose(RefSkeleton, Index).GetLocation().Z : 0.0f;
		};
		LeftFootRestHeight = RestHeight(Character.GetLeftFootBone());
		RightFootRestHeight = RestHeight(Character.GetRightFootBone());
		FootRestMesh = MeshAsset;
		bLeftFootLifted = bRightFootLifted = false;
	}

	// Last frame's final pose: lifted past the threshold, then back near the floor = a plant.
	auto Check = [&](FName Bone, float Rest, bool& bLifted, bool bLeft)
	{
		const float Height = Body->GetSocketTransform(Bone, RTS_Component).GetLocation().Z - Rest;
		if (Height > FootLiftHeight)
		{
			bLifted = true;
		}
		else if (bLifted && Height < FootPlantHeight)
		{
			bLifted = false;
			OnFootPlant(bLeft);
		}
	};
	Check(Character.GetLeftFootBone(), LeftFootRestHeight, bLeftFootLifted, true);
	Check(Character.GetRightFootBone(), RightFootRestHeight, bRightFootLifted, false);
}

void UProjectBopisAnimInstance::OnFootPlant(bool bLeft)
{
	// Only real steps: on the ground and moving. Idles, turns in place, the dive's legs in
	// the air and the prone poses all carry plants we don't want to hear.
	ABopisCharacterBase* Character = Cast<ABopisCharacterBase>(TryGetPawnOwner());
	const UCharacterMovementComponent* Movement = Character ? Character->GetCharacterMovement() : nullptr;
	if (!Character || !Movement || !Movement->IsMovingOnGround() || bShootdodging || Speed <= StationarySpeed)
	{
		return;
	}
	Character->PlayFootstep(bLeft);
}

void UProjectBopisAnimInstance::UpdateLean(const ABopisCharacterBase& Character, float DeltaSeconds)
{
	// Turn rate from the actor's yaw: the free run turns the body to the movement direction.
	const float Yaw = Character.GetActorRotation().Yaw;
	const float YawRate = DeltaSeconds > KINDA_SMALL_NUMBER
		? FRotator::NormalizeAxis(Yaw - LeanLastYaw) / DeltaSeconds : 0.0f;
	LeanLastYaw = Yaw;

	// Walking or jogging with the gun down, on the ground; not diving, rolling or crouched.
	const UCharacterMovementComponent* Movement = Character.GetCharacterMovement();
	const AProjectBopisCharacter* Hero = Cast<AProjectBopisCharacter>(&Character);
	const bool bRolling = Hero && Hero->GetRoll() && Hero->GetRoll()->IsRolling();
	const float SpeedNow = static_cast<float>(Speed);
	const bool bLean = bLeanIntoTurns && !bIsWeaponRaised && !bIsCrouched && !bShootdodging && !bRolling
		&& Movement && Movement->IsMovingOnGround() && SpeedNow > StationarySpeed;

	float Target = 0.0f;
	if (bLean)
	{
		const float SpeedScale = FMath::Clamp(SpeedNow / LeanFullSpeed, 0.0f, 1.0f);
		Target = FMath::Clamp(YawRate * LeanPerYawRate * SpeedScale, -MaxLeanAngle, MaxLeanAngle);
	}
	LeanAngle = FMath::FInterpTo(LeanAngle, Target, DeltaSeconds, LeanInterpSpeed);
	LeanSpineRotation = LeanPerDegree * (LeanAngle / 3.0f);
}

namespace
{
	/** Q, limited to MaxDegrees of turn about its own axis. */
	FQuat ClampTurn(const FQuat& Q, float MaxDegrees)
	{
		FVector Axis;
		float Angle;
		Q.ToAxisAndAngle(Axis, Angle);
		Angle = FMath::UnwindRadians(Angle);
		const float MaxAngle = FMath::DegreesToRadians(MaxDegrees);
		return FMath::Abs(Angle) > MaxAngle ? FQuat(Axis, FMath::Sign(Angle) * MaxAngle) : Q;
	}

	/** Direction, its up/down angle (from level, in degrees) kept within Min..Max; the way it
	    points across the ground is kept. Straight up or down there's no such way, so it's left. */
	FVector ClampElevation(const FVector& Direction, float MinDegrees, float MaxDegrees)
	{
		const FVector Flat = FVector(Direction.X, Direction.Y, 0.0f).GetSafeNormal();
		if (Flat.IsZero())
		{
			return Direction;
		}
		const float Elevation = FMath::Asin(FMath::Clamp(Direction.Z, -1.0f, 1.0f));
		const float Clamped = FMath::Clamp(Elevation, FMath::DegreesToRadians(MinDegrees), FMath::DegreesToRadians(MaxDegrees));
		return Flat * FMath::Cos(Clamped) + FVector::UpVector * FMath::Sin(Clamped);
	}
}

void UProjectBopisAnimInstance::UpdateShootdodgeAimCorrection(const ABopisCharacterBase& Character, const AWeaponBase* Weapon, float DeltaSeconds)
{
	// The dive and prone clips aim wherever they were authored; the shots go to the crosshair.
	// So the upper body turns until the gun points there too. Outside the dive's own phases
	// it eases back to nothing.
	//
	// Long guns borrow the pistol dive with their own arm hold, the left hand on the grip
	// (LeftHandGripLocation, in hand_r's space, from UpdateLeftHandGrip). That hold needs far
	// more lift than the pistol arms, so for them the turn is split: the chest takes the yaw
	// and only a little tilt, the arms the rest of the tilt, and the head looks at the target.
	const bool bLongGunDive = bShootdodging && Weapon && !bIsPistolHold;
	// A silent swap (face-down) changes the hold over the swap's own time instead of snapping.
	const float SilentSwapRate = Character.IsSilentEquipping()
		? 1.0f / FMath::Max(Character.GetSilentEquipDuration(), 0.05f) : 0.0f;
	ShootdodgeLongGunAlpha = SilentSwapRate > 0.0f
		? FMath::FInterpConstantTo(ShootdodgeLongGunAlpha, bLongGunDive ? 1.0 : 0.0, DeltaSeconds, SilentSwapRate)
		: FMath::FInterpTo(ShootdodgeLongGunAlpha, bLongGunDive ? 1.0 : 0.0, DeltaSeconds, 10.0f);
	// The hold lets go while a reload, draw or toss has the left hand (it used to stay pinned).
	ShootdodgeLeftHandAlpha = ShootdodgeLongGunAlpha * LeftHandGripAlpha * (1.0 - ProneReloadAlpha) * (1.0 - ThrowAlpha);

	// Duals: the dive's two-handed pistol arms would clasp the left gun to the right one, so
	// the left arm takes a mirrored one-handed hold instead (the AnimGraph's left-arm layer).
	const bool bDualDive = bShootdodging && Weapon && bIsDualWield;
	ShootdodgeDualAlpha = SilentSwapRate > 0.0f
		? FMath::FInterpConstantTo(ShootdodgeDualAlpha, bDualDive ? 1.0 : 0.0, DeltaSeconds, SilentSwapRate)
		: FMath::FInterpTo(ShootdodgeDualAlpha, bDualDive ? 1.0 : 0.0, DeltaSeconds, 10.0f);
	FQuat OffhandTarget = FQuat::Identity;

	const USkeletalMeshComponent* Mesh = Character.GetMesh();
	const APlayerController* PlayerController = Cast<APlayerController>(Character.GetController());
	FQuat Target = FQuat::Identity;
	FQuat ArmTarget = FQuat::Identity;
	FQuat HeadTarget = FQuat::Identity;

	// Reloading or drawing, the gun isn't being aimed: the correction lets go (it would bend the
	// torso to point a gun at the crosshair that's down by the chest), and comes back once done.
	if (bShootdodging && Mesh && Weapon && PlayerController && !bReloadAnimating && !Character.IsEquipAnimating())
	{
		// Where the crosshair is looking: the camera's view, out to whatever it hits.
		FVector ViewLocation;
		FRotator ViewRotation;
		PlayerController->GetPlayerViewPoint(ViewLocation, ViewRotation);
		const FVector ViewEnd = ViewLocation + ViewRotation.Vector() * Weapon->GetMaxRange();

		FCollisionQueryParams Params(SCENE_QUERY_STAT(ShootdodgeAim), false, &Character);
		Params.AddIgnoredActor(Weapon);
		FHitResult Hit;
		const FVector AimPoint = GetWorld()->LineTraceSingleByChannel(Hit, ViewLocation, ViewEnd, ECC_Visibility, Params)
			? Hit.ImpactPoint : ViewEnd;

		// The gun as drawn (corrections included) and where it should point, both in the
		// mesh's own space, where the correction nodes apply their rotation.
		const FTransform Muzzle = Weapon->GetMuzzleTransform();
		const FTransform& ToComponent = Mesh->GetComponentTransform();
		const FVector GunDirection = ToComponent.InverseTransformVectorNoScale(Muzzle.GetUnitAxis(EAxis::X));
		// The poses follow the aim up and down only so far (Max Payne's way): past the limit the
		// guns stay at it, while the shots still go from the muzzle to the crosshair's point.
		// (The mesh only ever turns about the vertical, so its up is the world's.)
		const FVector WantedDirection = ClampElevation(ToComponent.InverseTransformVectorNoScale(
			(AimPoint - Muzzle.GetLocation()).GetSafeNormal()), AimPitchMin(), AimPitchMax());

		// The gun as the poses alone hold it: the correction now applied taken back out. The
		// whole turn from there to the target is worked out fresh each frame, never added on to
		// last frame's — so no roll about the barrel (which aiming can't see, so nothing would
		// ever correct) piles up and twists the torso, head and wrists out of shape.
		const FQuat Applied = bLongGunDive ? ArmAimCorrectionTotal * AimCorrectionTotal : AimCorrectionTotal;
		const FQuat Whole = FQuat::FindBetweenNormals(Applied.UnrotateVector(GunDirection), WantedDirection);
		Target = Whole;

		if (bLongGunDive)
		{
			// The whole turn the gun needs, chest and arms together (the arms apply after the
			// chest). The chest takes only a little of each — LongGunMaxYaw of turn about the
			// vertical and LongGunMaxPitch of tilt: lying down, either one bends the torso (a turn
			// about the vertical is a sideways bend for a body on its back). The arms take exactly
			// the rest. A straight split each frame, so nothing switches on and off and jitters.
			FQuat Tilt, Yaw;
			Whole.ToSwingTwist(FVector::UpVector, Tilt, Yaw);
			Target = ClampTurn(Tilt, LongGunMaxPitch) * ClampTurn(Yaw, LongGunMaxYaw);
			ArmTarget = ClampTurn(Whole * Target.Inverse(), LongGunArmMaxAngle);

			// Head: turns to face the target as well. Its forward is whatever way it faces in
			// the reference pose (standing, facing the mesh's forward, +Y).
			if (HeadLocalForward.IsZero())
			{
				const FReferenceSkeleton& RefSkeleton = Mesh->GetSkinnedAsset()->GetRefSkeleton();
				const int32 HeadIndex = RefSkeleton.FindBoneIndex(TEXT("head"));
				if (HeadIndex != INDEX_NONE)
				{
					const FTransform RefHead = FAnimationRuntime::GetComponentSpaceTransformRefPose(RefSkeleton, HeadIndex);
					HeadLocalForward = RefHead.GetRotation().UnrotateVector(FVector::YAxisVector);
				}
			}
			if (!HeadLocalForward.IsZero())
			{
				const FTransform Head = Mesh->GetSocketTransform(TEXT("head"));
				const FVector HeadForward = ToComponent.InverseTransformVectorNoScale(
					Head.GetRotation().RotateVector(HeadLocalForward));
				const FVector ToTarget = ClampElevation(ToComponent.InverseTransformVectorNoScale(
					(AimPoint - Head.GetLocation()).GetSafeNormal()), AimPitchMin(), AimPitchMax());
				// Fresh each frame from the head as the poses (and the chest) hold it, as for the gun.
				HeadTarget = ClampTurn(FQuat::FindBetweenNormals(HeadCorrectionTotal.UnrotateVector(HeadForward), ToTarget),
					HeadLookMaxAngle);
			}
		}
		else
		{
			// Capped: past the limit the spine would corkscrew; the gun stays off instead.
			Target = ClampTurn(Target, AimCorrectionMaxAngle);
		}

		// Duals: the left gun aims on its own, from the left upper arm, on top of everything
		// the body already does for the right one. Same fresh measure, its own muzzle.
		if (bDualDive && Weapon->GetOffhandMesh())
		{
			const FTransform OffhandMuzzle = Weapon->GetMuzzleTransform(true);
			const FVector OffhandGun = ToComponent.InverseTransformVectorNoScale(OffhandMuzzle.GetUnitAxis(EAxis::X));
			const FVector OffhandWanted = ClampElevation(ToComponent.InverseTransformVectorNoScale(
				(AimPoint - OffhandMuzzle.GetLocation()).GetSafeNormal()), AimPitchMin(), AimPitchMax());
			OffhandTarget = ClampTurn(
				FQuat::FindBetweenNormals(OffhandAimCorrectionTotal.UnrotateVector(OffhandGun), OffhandWanted),
				OffhandAimMaxAngle);
		}
	}

	const float Alpha = FMath::Clamp(DeltaSeconds * AimCorrectionSpeed, 0.0f, 1.0f);
	AimCorrectionTotal = FQuat::Slerp(AimCorrectionTotal, Target, Alpha).GetNormalized();
	ArmAimCorrectionTotal = FQuat::Slerp(ArmAimCorrectionTotal, ArmTarget, Alpha).GetNormalized();
	HeadCorrectionTotal = FQuat::Slerp(HeadCorrectionTotal, HeadTarget, Alpha).GetNormalized();
	OffhandAimCorrectionTotal = FQuat::Slerp(OffhandAimCorrectionTotal, OffhandTarget, Alpha).GetNormalized();
	ShootdodgeOffhandAimCorrection = OffhandAimCorrectionTotal.Rotator();

	// Lying back: the back poses hold the guns down at the hips, between the legs.
	// The arms lift from the shoulders and the hands turn back down by the same amount, so
	// the guns rise without changing where they point (the corrections above still aim
	// them). From nothing at the side poses (90°) to BackGunLiftAngle from 135° round to
	// straight back.
	const float BackWeight = FMath::Clamp((FMath::Abs(ShootdodgeDirection) - 90.0f) / 45.0f, 0.0f, 1.0f);
	// Long guns too, with their own amount: the rifle hold sits low across the legs as well
	// (the left hand then follows the grip through its IK, which runs after the lift).
	const float LiftAmount = bLongGunDive ? LongGunBackLiftAngle : BackGunLiftAngle;
	const float LiftTarget = (bShootdodging && Weapon) ? BackWeight * LiftAmount : 0.0f;
	GunLiftAngle = FMath::FInterpTo(GunLiftAngle, LiftTarget, DeltaSeconds, 6.0f);

	// Duals' left arm sits lower still in those poses (its own one-handed hold), so it lifts
	// further; its turn is about its own gun.
	const float OffhandLiftTarget = (bShootdodging && bDualDive) ? BackWeight * BackOffhandExtraLift : 0.0f;
	OffhandExtraLiftAngle = FMath::FInterpTo(OffhandExtraLiftAngle, OffhandLiftTarget, DeltaSeconds, 6.0f);

	// Raised about the level line across a gun: turning its barrel about (gun × up) swings
	// it — and, from the shoulder, the hand — toward up. Then swung out by Spread. The hand
	// turns back by the whole of it, so the gun keeps pointing where it did.
	auto LiftFor = [Mesh](const FTransform& Muzzle, float Degrees, const FQuat& Spread, FRotator& OutArm, FRotator& OutHand)
	{
		FQuat Lift = FQuat::Identity;
		if (Degrees > KINDA_SMALL_NUMBER && Mesh)
		{
			const FVector Gun = Mesh->GetComponentTransform().InverseTransformVectorNoScale(Muzzle.GetUnitAxis(EAxis::X));
			const FVector Axis = FVector::CrossProduct(Gun, FVector::UpVector).GetSafeNormal();
			if (!Axis.IsZero())
			{
				Lift = FQuat(Axis, FMath::DegreesToRadians(Degrees));
			}
		}
		const FQuat Arm = Spread * Lift;
		OutArm = Arm.Rotator();
		OutHand = Arm.Inverse().Rotator();
	};

	// Duals: from behind the right shoulder, two guns aimed at one point sit in front of the
	// head and body. Each arm swings out to its own side of the screen (about the camera's
	// up), so the guns clear the body; the aim correction above still points them.
	FQuat SpreadRight = FQuat::Identity;
	FQuat SpreadLeft = FQuat::Identity;
	if (Mesh && PlayerController && ShootdodgeDualAlpha > KINDA_SMALL_NUMBER)
	{
		FVector ViewLocation;
		FRotator ViewRotation;
		PlayerController->GetPlayerViewPoint(ViewLocation, ViewRotation);
		const FVector CameraUp = Mesh->GetComponentTransform().InverseTransformVectorNoScale(
			ViewRotation.Quaternion().GetUpVector());
		const float Spread = FMath::DegreesToRadians(DualDiveSpreadAngle) * ShootdodgeDualAlpha;
		SpreadRight = FQuat(CameraUp, Spread);
		SpreadLeft = FQuat(CameraUp, -Spread);
	}

	if (Weapon)
	{
		LiftFor(Weapon->GetMuzzleTransform(), GunLiftAngle, SpreadRight, ShootdodgeArmLift, ShootdodgeHandCounterLift);
		LiftFor(Weapon->GetMuzzleTransform(bDualDive), GunLiftAngle + OffhandExtraLiftAngle, SpreadLeft,
			ShootdodgeArmLiftL, ShootdodgeHandCounterLiftL);
	}
	else
	{
		ShootdodgeArmLift = ShootdodgeHandCounterLift = ShootdodgeArmLiftL = ShootdodgeHandCounterLiftL = FRotator::ZeroRotator;
	}

	// Half on each of two bones: the same mesh-space turn twice adds up to the whole. Pistols
	// put it on spine_03/05, long guns on the chest (spine_04/05); each arm takes the whole
	// arm turn about its own shoulder.
	const FQuat HalfTurn = FQuat::Slerp(FQuat::Identity, AimCorrectionTotal, 0.5f);
	ShootdodgeAimCorrection = FQuat::Slerp(HalfTurn, FQuat::Identity, ShootdodgeLongGunAlpha).Rotator();
	ShootdodgeChestAimCorrection = FQuat::Slerp(FQuat::Identity, HalfTurn, ShootdodgeLongGunAlpha).Rotator();
	ShootdodgeArmAimCorrection = ArmAimCorrectionTotal.Rotator();
	ShootdodgeHeadCorrection = FQuat::Slerp(FQuat::Identity, HeadCorrectionTotal, 0.5f).Rotator();
}

void UProjectBopisAnimInstance::UpdateProneReloadLayers(float DeltaSeconds)
{
	// Face-down, the whole-arm reload would sweep the arms down through the floor: there only
	// the forearms and hands take it, the upper arms staying out in front. Everywhere else (the
	// air, a side, the back) the whole arms do, as before.
	const bool bFaceDown = ShootdodgePhase == EShootdodgePhase::Prone
		&& FMath::Abs(ShootdodgeDirection) <= ProneFrontMaxAngle;
	ProneFrontAlpha = FMath::FInterpTo(ProneFrontAlpha, bFaceDown ? 1.0f : 0.0f, DeltaSeconds, ProneDualReloadSwapSpeed);

	ProneArmReloadAlpha = ProneReloadAlpha * (1.0f - ProneFrontAlpha);
	ProneForearmReloadAlpha = ProneReloadAlpha * ProneFrontAlpha;
	ProneDualOffhandAlpha = bIsDualWield ? ProneArmReloadAlpha : 0.0f;
	ProneForearmDualAlpha = bIsDualWield ? ProneForearmReloadAlpha : 0.0f;

	// Long guns face-down: even forearms-only, a rifle reload brings the gun down into the floor.
	// So both upper arms raise about the shoulders' line, lifting the forearms and gun with them.
	const float RaiseAlpha = bIsPistolHold ? 0.0f : ProneForearmReloadAlpha;
	ProneLongGunArmRaise = FRotator::ZeroRotator;
	const USkeletalMeshComponent* Mesh = GetSkelMeshComponent();
	if (RaiseAlpha > KINDA_SMALL_NUMBER && Mesh && Mesh->DoesSocketExist(TEXT("upperarm_r")))
	{
		const FTransform& ToComponent = Mesh->GetComponentTransform();
		auto Bone = [Mesh, &ToComponent](const TCHAR* Name)
		{
			return ToComponent.InverseTransformPosition(Mesh->GetSocketLocation(Name));
		};
		const FVector Across = (Bone(TEXT("upperarm_r")) - Bone(TEXT("upperarm_l"))).GetSafeNormal();
		const FVector Arm = Bone(TEXT("lowerarm_r")) - Bone(TEXT("upperarm_r"));
		if (!Across.IsNearlyZero())
		{
			// Whichever way round the shoulders' line lifts the elbows rather than lowering them.
			const float Lift = FVector::CrossProduct(Across, Arm).Z >= 0.0f ? 1.0f : -1.0f;
			const float Angle = FMath::DegreesToRadians(ProneLongGunArmRaiseAngle) * RaiseAlpha * Lift;
			ProneLongGunArmRaise = FQuat(Across, Angle).Rotator();
		}
	}
}

void UProjectBopisAnimInstance::UpdateProneDirection(float DeltaSeconds)
{
	if (ShootdodgePhase != EShootdodgePhase::Prone)
	{
		// Not lying down: the prone pose starts from the real direction when it begins.
		ProneBlendDirection = ShootdodgeDirection;
		bProneHoldingForward = FMath::Abs(ShootdodgeDirection) < ProneForwardSnapAngle;
		bProneHoldingSide = FMath::Abs(ShootdodgeDirection) - 90.0f < ProneSideSnapAngle;
		ProneBodyTurn = FRotator::ZeroRotator;
		ProneSpineCounterTurn = FRotator::ZeroRotator;
		ProneNeutralAlpha = 0.0f;
		return;
	}

	// Two spans don't blend: between Fwd and Fwd_Left/Right the blends sink the legs through
	// the floor, and between Right/Left and Bwd_Right/Left they lift them. The front holds
	// the diagonal and only swaps to Fwd once the direction comes close to straight ahead;
	// the back-side span holds Bwd_Right/Left and only swaps to Right/Left once within
	// ProneSideSnapAngle of it (each with a little hysteresis). Everywhere else the pose
	// follows the direction. Either way it eases there at PronePoseSwapSpeed, so a swap is a
	// slow transition; the body/spine turn below covers any lag.
	const float AbsDirection = FMath::Abs(ShootdodgeDirection);
	const float Side = ShootdodgeDirection < 0.0f ? -1.0f : 1.0f;
	float PoseDirection = ShootdodgeDirection;
	const bool bWasHoldingForward = bProneHoldingForward;
	const bool bWasHoldingSide = bProneHoldingSide;
	bProneHoldingForward = false;
	bProneHoldingSide = false;
	if (AbsDirection < 45.0f)
	{
		bProneHoldingForward = AbsDirection
			< ProneForwardSnapAngle + (bWasHoldingForward ? ProneForwardSnapHysteresis : 0.0f);
		PoseDirection = bProneHoldingForward ? 0.0f : Side * 45.0f;
	}
	else if (AbsDirection > 90.0f && AbsDirection < 135.0f)
	{
		bProneHoldingSide = AbsDirection - 90.0f
			< ProneSideSnapAngle + (bWasHoldingSide ? ProneForwardSnapHysteresis : 0.0f);
		PoseDirection = Side * (bProneHoldingSide ? 90.0f : 135.0f);
	}

	// Eased along the shorter way round: across straight back the direction wraps from +180
	// to −180, and easing the plain number would sweep the pose through the front instead.
	// Duals and long guns reloading on a side: the lower shoulder leaves that arm no room, so the
	// body goes over onto its back (the back-prone pose) for the reload, and back once it's done.
	// Face-down and on the back they reload where they lie, as do the single pistols.
	const bool bSideDualReload = (bIsDualWield || !bIsPistolHold) && bReloadAnimating
		&& AbsDirection > ProneFrontMaxAngle && AbsDirection < ProneSideMaxAngle;
	if (bSideDualReload)
	{
		PoseDirection = 180.0f;
	}
	const float SwapSpeed = bSideDualReload ? ProneDualReloadSwapSpeed : PronePoseSwapSpeed;
	ProneNeutralAlpha = FMath::FInterpTo(ProneNeutralAlpha, bSideDualReload ? 1.0f : 0.0f, DeltaSeconds, ProneDualReloadSwapSpeed);

	const float Remaining = FRotator::NormalizeAxis(PoseDirection - ProneBlendDirection);
	ProneBlendDirection = FRotator::NormalizeAxis(
		ProneBlendDirection + FMath::FInterpTo(0.0f, Remaining, DeltaSeconds, SwapSpeed));

	// The pose shows the body lying a little off the real direction: turn the whole body by
	// the difference so it lies where the dive put it, and the spine back by the same (half
	// on each of two bones) so the gun still points at the aim.
	const float Difference = FRotator::NormalizeAxis(ShootdodgeDirection - ProneBlendDirection);
	ProneBodyTurn = FRotator(0.0f, Difference, 0.0f);
	// Under the side-prone dual reload the aim is ignored: no counter-turn (and no pitch), so
	// the body lies as the back pose has it, looking along the legs, until it's done.
	ProneSpineCounterTurn = FRotator(0.0f, -0.5f * Difference * (1.0f - ProneNeutralAlpha), 0.0f);
	ShootdodgeAimPitch *= 1.0f - ProneNeutralAlpha;
}

void UProjectBopisAnimInstance::UpdateProneFeet(const ABopisCharacterBase& Character, float DeltaSeconds)
{
	// Only while the pose sits between two authored ones — mid-swap across the front (Fwd ↔
	// Fwd_Left/Right) or the back sides (Right/Left ↔ Bwd_Right/Left). |sin 4θ| is 0 on every
	// authored pose and peaks halfway, so held poses are never touched. Across the front the
	// in-between pose sinks the knees: the torso comes up by what the lower knee needs (fine
	// mid-transition), and the feet with it. Across the back sides only the feet are kept out
	// of the floor.
	const USkeletalMeshComponent* Mesh = Character.GetMesh();
	const float AbsBlendDirection = FMath::Abs(ProneBlendDirection);
	const bool bFrontSpan = AbsBlendDirection < 45.0f;
	const bool bBackSideSpan = AbsBlendDirection > 90.0f && AbsBlendDirection < 135.0f;
	const float BetweenPoses = FMath::Abs(FMath::Sin(FMath::DegreesToRadians(ProneBlendDirection * 4.0f)));
	const double TargetAlpha = (Mesh && ShootdodgePhase == EShootdodgePhase::Prone && (bFrontSpan || bBackSideSpan))
		? BetweenPoses : 0.0;
	ProneFootIKAlpha = FMath::FInterpTo(ProneFootIKAlpha, TargetAlpha, DeltaSeconds, 10.0f);
	if (ProneFootIKAlpha <= KINDA_SMALL_NUMBER)
	{
		ProneFootIKAlpha = 0.0;
		ProneHipLift = FVector::ZeroVector;
		return;
	}

	// The AnimGraph copies the feet (onto ik_foot_*) and the knees (onto the spare ik_hand_*)
	// before the lift and the IK, and those bones hang off the root — so these are the legs
	// exactly as animated, with nothing fed back from the fix itself.
	const FVector FootL = Mesh->GetSocketLocation(TEXT("ik_foot_l"));
	const FVector FootR = Mesh->GetSocketLocation(TEXT("ik_foot_r"));
	const FVector KneeL = Mesh->GetSocketLocation(TEXT("ik_hand_l"));
	const FVector KneeR = Mesh->GetSocketLocation(TEXT("ik_hand_r"));

	const float HipLift = bFrontSpan
		? FMath::Max(FloorShortfall(*Mesh, KneeL, ProneKneeClearance), FloorShortfall(*Mesh, KneeR, ProneKneeClearance))
		: 0.0f;
	ProneHipLift = FVector(0.0, 0.0, HipLift);

	// The feet ride up with the hips, plus whatever more they need themselves.
	const FTransform& ComponentTransform = Mesh->GetComponentTransform();
	ProneFootTargetL = ComponentTransform.InverseTransformPosition(
		FootL + FVector::UpVector * FMath::Max(HipLift, FloorShortfall(*Mesh, FootL, ProneFootClearance)));
	ProneFootTargetR = ComponentTransform.InverseTransformPosition(
		FootR + FVector::UpVector * FMath::Max(HipLift, FloorShortfall(*Mesh, FootR, ProneFootClearance)));
}

float UProjectBopisAnimInstance::FloorShortfall(const USkeletalMeshComponent& Mesh, const FVector& Point, float Clearance) const
{
	FCollisionQueryParams Params(SCENE_QUERY_STAT(ProneFloor), false, Mesh.GetOwner());
	FHitResult Hit;
	if (!Mesh.GetWorld()->LineTraceSingleByChannel(Hit, Point + FVector::UpVector * 50.0f,
		Point - FVector::UpVector * 100.0f, ECC_Visibility, Params))
	{
		return 0.0f;
	}
	return FMath::Max(0.0f, Hit.ImpactPoint.Z + Clearance - Point.Z);
}

void UProjectBopisAnimInstance::UpdateShootdodgeAim(const ABopisCharacterBase& Character, float DeltaSeconds)
{
	// Only the player dives; enemies stay in the normal graph.
	const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(&Character);
	const UShootdodgeComponent* Shootdodge = Player ? Player->GetShootdodge() : nullptr;

	ShootdodgePhase = Shootdodge ? Shootdodge->GetPhase() : EShootdodgePhase::None;
	bShootdodging = ShootdodgePhase != EShootdodgePhase::None && ShootdodgePhase != EShootdodgePhase::GettingUp
		&& ShootdodgePhase != EShootdodgePhase::WindUp;

	if (Shootdodge)
	{
		// Most dives follow the live direction outright. After a jog's forward jump it eases round
		// from the jump to the live one, so the push-off turns into the flight instead of popping.
		const float TargetDirection = Shootdodge->GetAnimDirectionAngle();
		if (!bShootdodging || !Shootdodge->EasesAnimDirection() || Shootdodge->IsHoldingForwardJump())
		{
			ShootdodgeDirection = TargetDirection;
		}
		else
		{
			const float Step = ShootdodgeDirectionCatchUpRate * DeltaSeconds;
			ShootdodgeDirection = FRotator::NormalizeAxis(ShootdodgeDirection
				+ FMath::Clamp(FMath::FindDeltaAngleDegrees(ShootdodgeDirection, TargetDirection), -Step, Step));
		}
		ShootdodgePlayRate = Shootdodge->GetPhasePlayRate();
		ShootdodgeStartPosition = Shootdodge->GetPhaseStartPosition();
		ShootdodgeStartTime = Shootdodge->GetStartNormalizedTime();
	}

	const FRotator Control = Character.GetControlRotation();
	ShootdodgeAimYaw = FRotator::NormalizeAxis(Control.Yaw - Character.GetActorRotation().Yaw);
	// The prone poses' up/down too follows the aim only within the shootdodge limits.
	ShootdodgeAimPitch = FMath::Clamp(FRotator::NormalizeAxis(Control.Pitch), AimPitchMin(), AimPitchMax());
}

void UProjectBopisAnimInstance::UpdateLocomotion(const ABopisCharacterBase& Character)
{
	const FVector Velocity = Character.GetVelocity();
	Speed = Velocity.Size();

	// Travel direction relative to where the character faces.
	Direction = Speed > UE_KINDA_SMALL_NUMBER
		? FRotator::NormalizeAxis(Velocity.Rotation().Yaw - Character.GetActorRotation().Yaw)
		: 0.0f;

	// Moving backward plays the backsteps whichever way the strafe came from: a side clip held
	// on into a back diagonal and warped round twists the torso. Otherwise, hysteresis stops
	// the strafe clip flickering between two cardinals on a diagonal.
	const double AbsDirection = FMath::Abs(Direction);
	const bool bBackstepping = FMath::Abs(CardinalDirection) > 179.0;
	if (AbsDirection >= BackstepMinAngle || (bBackstepping && AbsDirection >= BackstepMinAngle - BackstepHysteresis))
	{
		CardinalDirection = 180.0;
	}
	else if (FMath::Abs(FRotator::NormalizeAxis(Direction - CardinalDirection)) > CardinalSwitchAngle
		|| bBackstepping)
	{
		CardinalDirection = FMath::GridSnap(Direction, 90.0);
	}

	// Orientation warping rotates the legs by whatever the cardinal clip doesn't cover.
	WarpAngle = FRotator::NormalizeAxis(Direction - CardinalDirection);

	AimPitch = FRotator::NormalizeAxis(Character.GetControlRotation().Pitch);

	DualLoweredPlayRate = LocomotionPlayRate * DualLoweredRateScale;
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
	// change; crouched, the snap reads as a pop. Duals and the one-handed pistol have no
	// shared grip and always ease; so does the drop after a montage.
	const bool bSharedGrip = !bIsDualWield && CurrentAnimType != EWeaponAnimType::PistolOneHanded;

	const bool bSnap = bLowering
		&& !bEaseLowering
		&& bSharedGrip
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

	// Duals: the mirrored left arm follows the raised layer. Crouched, the
	// lowered-dual layer (a standing whole-body pose) is faded out — eased with the
	// crouch so standing up blends it back in — and the left arm comes from the
	// crouch clip until raised.
	DualCrouchBlend = FMath::FInterpTo(
		DualCrouchBlend, bIsCrouched ? 1.0f : 0.0f, DeltaSeconds, UpperBodyInterpSpeed);

	LeftArmAlpha = bIsDualWield ? UpperBodyAlpha : 0.0;

	DualLoweredAlpha = bIsDualWield
		? (1.0 - UpperBodyAlpha) * (1.0 - DualCrouchBlend)
		: 0.0;

	// Left-hand IK: two-handed holds (long guns and the two-handed pistol), whenever the gun is
	// up (aimed, or raised for hip-fire), so the hand stays on the grip at any pitch — the aim
	// offsets' arm poses don't match every raised or fire pose under them. Not the one-handed
	// pistol (free arm) or duals (a gun in each hand); off while a reload, draw or grenade toss
	// uses the hand. Target: the weapon's LeftHandGrip socket, else the clip's ik_hand_l.
	// Eases on, snaps off.
	const bool bTwoHanded = !bIsDualWield && CurrentAnimType != EWeaponAnimType::PistolOneHanded;
	const bool bGunUp = bIsAiming || bIsWeaponRaised;
	const double IKTarget = (bGunUp && bTwoHanded
		&& !bReloadAnimating && !bEquipAnimating && !bThrowingGrenade) ? 1.0 : 0.0;

	LeftHandIKAlpha = IKTarget < LeftHandIKAlpha
		? IKTarget
		: FMath::FInterpTo(LeftHandIKAlpha, IKTarget, DeltaSeconds, LeftHandIKInterpSpeed);

	// One-handed pistol: the raised pistol poses are two-handed, so while raised the free
	// left arm is overridden with the at-side pose. It follows the raised layer, and eases
	// out for reload, equip and grenade montages (and back in after) so their own left arm
	// plays — the toss is authored from a hand-forward hold, not one at the side.
	FreeArmReloadBlend = FMath::FInterpTo(FreeArmReloadBlend,
		(bReloadAnimating || bEquipAnimating || bThrowingGrenade) ? 0.0f : 1.0f, DeltaSeconds, UpperBodyInterpSpeed);

	const bool bOneHanded = CurrentAnimType == EWeaponAnimType::PistolOneHanded;
	FreeArmAlpha = bOneHanded ? UpperBodyAlpha * FreeArmReloadBlend : 0.0;}

void UProjectBopisAnimInstance::UpdateFreeArmSwing(float DeltaSeconds)
{
	// Last frame's pose: how far the right foot leads the left along the way the body
	// faces. Opposite arm follows opposite leg, so this alone drives a swing in step
	// with the feet — forward, backpedal and strafe alike, at any gait rate.
	float Target = 0.0f;

	const USkeletalMeshComponent* Mesh = GetSkelMeshComponent();
	const APawn* Pawn = TryGetPawnOwner();
	if (Mesh && Pawn && Speed > StationarySpeed)
	{
		const FVector FootGap = Mesh->GetSocketLocation(TEXT("foot_r")) - Mesh->GetSocketLocation(TEXT("foot_l"));
		const float Lead = FVector::DotProduct(FootGap, Pawn->GetActorForwardVector());

		// Auto-gain: scale to the largest recent gap, so a side-step's small fore-aft
		// alternation still gives a full swing. Rises at once, falls back over ~a second.
		FreeArmStridePeak = FMath::Max(FMath::Abs(Lead),
			FMath::FInterpTo(FreeArmStridePeak, FreeArmMinStride, DeltaSeconds, 1.0f));
		FreeArmStridePeak = FMath::Max(FreeArmStridePeak, FreeArmMinStride);

		Target = FMath::Clamp(Lead / FreeArmStridePeak, -1.0f, 1.0f);
	}

	FreeArmSwingPhase = FMath::FInterpTo(FreeArmSwingPhase, Target, DeltaSeconds, 12.0f);

	// Fades in with speed, so a slow start doesn't flap the arm.
	const float SpeedScale = FMath::Clamp(Speed / 300.0, 0.0, 1.0);
	FreeArmSwingRotation = FreeArmSwingFull * (FreeArmSwingPhase * SpeedScale);
}

void UProjectBopisAnimInstance::AddRecoil(bool bOffhand, float Strength)
{
	FFloatSpringState& Spring = bOffhand ? OffhandRecoilSpring : MainRecoilSpring;
	Spring.Velocity += RecoilImpulse * Strength;
}

void UProjectBopisAnimInstance::UpdateRecoil(float DeltaSeconds)
{
	// A shot only adds spring velocity, so rapid fire stacks instead of restarting the way
	// a fire montage does. Clamped 0..1 (hitting either end zeroes the velocity): the
	// AnimGraph nodes hold the full-kick rotation, these just weight it.
	MainRecoil = UKismetMathLibrary::FloatSpringInterp(MainRecoil, 0.0f, MainRecoilSpring,
		RecoilStiffness, RecoilDamping, DeltaSeconds, 1.0f, 1.0f, true, 0.0f, 1.0f);
	OffhandRecoil = UKismetMathLibrary::FloatSpringInterp(OffhandRecoil, 0.0f, OffhandRecoilSpring,
		RecoilStiffness, RecoilDamping, DeltaSeconds, 1.0f, 1.0f, true, 0.0f, 1.0f);

	SpineRecoilAlpha = FMath::Max(MainRecoil, OffhandRecoil);
	ArmRecoilAlpha = bIsPistolHold ? MainRecoil : 0.0;
	OffhandArmRecoilAlpha = bIsDualWield ? OffhandRecoil : 0.0;
	FreeArmRecoilAlpha = CurrentAnimType == EWeaponAnimType::PistolOneHanded
		? MainRecoil * FreeArmAlpha
		: 0.0;
}

void UProjectBopisAnimInstance::UpdateLeftHandGrip(const ABopisCharacterBase& Character, const AWeaponBase* Weapon)
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

	// The raise frame doesn't count, nor the quick turn to the camera that follows it — the
	// body turns with the capsule on purpose, rather than starting a turn-in-place.
	const bool bCanTurn = bIsWeaponRaised
		&& bWasWeaponRaised
		&& !bTurningToAim
		&& Speed < TurnInPlaceMaxSpeed
		&& (!bIsCrouched || (CrouchTurnLeftMontage && CrouchTurnRightMontage));

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

		// Negative offset: the body lags left of the camera, so it steps right. Crouched,
		// the crouch's own steps.
		UAnimMontage* LeftMontage = bIsCrouched ? CrouchTurnLeftMontage : TurnLeftMontage;
		UAnimMontage* RightMontage = bIsCrouched ? CrouchTurnRightMontage : TurnRightMontage;
		UAnimMontage* TurnMontage = RootYawOffset < 0.0f ? RightMontage : LeftMontage;
		if (TurnMontage)
		{
			// bStopAllMontages = false, or starting a turn would cancel fire/reload.
			Montage_Play(TurnMontage, 1.0f, EMontagePlayReturnType::MontageLength, 0.0f, false);
		}
	}
}

void UProjectBopisAnimInstance::UpdateHeadLook(const ABopisCharacterBase& Character, float DeltaSeconds)
{
	FQuat Target = FQuat::Identity;
	FVector LookAt;
	const USkeletalMeshComponent* Mesh = Character.GetMesh();
	if (Mesh && !bShootdodging && Character.GetHeadLookTarget(LookAt))
	{
		// From the head, in the mesh's own space (it faces +Y): how far round, and how far up or down.
		const FVector ToTarget = Mesh->GetComponentTransform().InverseTransformVectorNoScale(
			(LookAt - Mesh->GetSocketLocation(TEXT("head"))).GetSafeNormal());
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(-ToTarget.X, ToTarget.Y));

		// Behind the shoulder: let go rather than strain. Otherwise turn toward it, held at the limits.
		if (FMath::Abs(Yaw) <= HeadLookGiveUpAngle)
		{
			const float ClampedYaw = FMath::DegreesToRadians(FMath::Clamp(Yaw, -HeadLookMaxYaw, HeadLookMaxYaw));
			const float MaxPitch = FMath::DegreesToRadians(HeadLookMaxPitch);
			const float Pitch = FMath::Clamp(FMath::Asin(FMath::Clamp(ToTarget.Z, -1.0f, 1.0f)), -MaxPitch, MaxPitch);
			const FVector Flat(-FMath::Sin(ClampedYaw), FMath::Cos(ClampedYaw), 0.0f);
			Target = FQuat::FindBetweenNormals(FVector::YAxisVector, Flat * FMath::Cos(Pitch) + FVector::UpVector * FMath::Sin(Pitch));
		}
	}

	// Eased in and out, so the head turns rather than snaps when a target comes or goes.
	HeadLookTotal = FQuat::Slerp(HeadLookTotal, Target, FMath::Clamp(DeltaSeconds * HeadLookSpeed, 0.0f, 1.0f)).GetNormalized();
	HeadLookRotation = FQuat::Slerp(FQuat::Identity, HeadLookTotal, 0.5f).Rotator();
}

void UProjectBopisAnimInstance::UpdateBlade(const ABopisCharacterBase& Character, const AWeaponBase* Weapon, float DeltaSeconds)
{
	// The one-handed pistol's bladed upper body, off while a reload, draw or grenade toss owns the arms.
	const float Alpha = StrafeBladeAlpha * (1.0f - ProneReloadAlpha) * (1.0f - ThrowAlpha);

	// Chest turned about the vertical so the right shoulder leads; the head turns back by the same.
	const float HalfTurn = 0.5f * BladeAngle * Alpha;
	BladeSpineTurn = FRotator(0.0f, -HalfTurn, 0.0f);
	BladeHeadTurn = FRotator(0.0f, HalfTurn, 0.0f);

	// Gun arm: turned from the shoulder so the arm's line (shoulder to hand) points at the aim point;
	// the arm keeps the pose's shape and the hand its grip. Fresh each frame from the arm as the
	// pose holds it (this turn taken back out), as for the dive.
	FQuat Target = FQuat::Identity;
	FQuat HandTarget = FQuat::Identity;
	const float HandAlpha = FMath::Max(Alpha, HipAimHandAlpha);
	const USkeletalMeshComponent* Mesh = Character.GetMesh();
	const APlayerController* PlayerController = Cast<APlayerController>(Character.GetController());
	if (HandAlpha > KINDA_SMALL_NUMBER && Mesh && Weapon && PlayerController)
	{
		FVector ViewLocation;
		FRotator ViewRotation;
		PlayerController->GetPlayerViewPoint(ViewLocation, ViewRotation);
		const FVector ViewEnd = ViewLocation + ViewRotation.Vector() * Weapon->GetMaxRange();

		FCollisionQueryParams Params(SCENE_QUERY_STAT(BladeAim), false, &Character);
		Params.AddIgnoredActor(Weapon);
		FHitResult Hit;
		const FVector AimPoint = GetWorld()->LineTraceSingleByChannel(Hit, ViewLocation, ViewEnd, ECC_Visibility, Params)
			? Hit.ImpactPoint : ViewEnd;

		const FTransform& ToComponent = Mesh->GetComponentTransform();

		// Turning in place, the whole pose is counter-rotated at the root (RotateRootBone, by
		// RootYawOffset) after these turns in the graph, but the bones read here already
		// include it. Everything is brought back to the frame the turns apply in.
		const FQuat PreRoot = FRotator(0.0f, RootYawOffset, 0.0f).Quaternion().Inverse();

		// The arm turn is the blade's alone.
		if (Alpha > KINDA_SMALL_NUMBER)
		{
			const FVector Shoulder = Mesh->GetSocketLocation(TEXT("upperarm_r"));
			const FVector Hand = Mesh->GetSocketLocation(TEXT("hand_r"));
			const FVector ArmLine = PreRoot * ToComponent.InverseTransformVectorNoScale((Hand - Shoulder).GetSafeNormal());
			const FVector Wanted = PreRoot * ToComponent.InverseTransformVectorNoScale((AimPoint - Shoulder).GetSafeNormal());
			Target = ClampTurn(FQuat::FindBetweenNormals(BladeArmTotal.UnrotateVector(ArmLine), Wanted), BladeArmMaxAngle);
			Target = FQuat::Slerp(FQuat::Identity, Target, Alpha);
		}

		// Then the hand: the barrel lined up with the crosshair. The gun as held already includes
		// both turns; only the hand's own is taken back out (it applies after the arm's).
		const FTransform Muzzle = Weapon->GetMuzzleTransform();
		const FVector GunDirection = PreRoot * ToComponent.InverseTransformVectorNoScale(Muzzle.GetUnitAxis(EAxis::X));
		const FVector GunWanted = PreRoot * ToComponent.InverseTransformVectorNoScale((AimPoint - Muzzle.GetLocation()).GetSafeNormal());
		HandTarget = ClampTurn(FQuat::FindBetweenNormals(BladeHandTotal.UnrotateVector(GunDirection), GunWanted), BladeHandMaxAngle);
		HandTarget = FQuat::Slerp(FQuat::Identity, HandTarget, HandAlpha);
	}
	BladeArmTotal = FQuat::Slerp(BladeArmTotal, Target, FMath::Clamp(DeltaSeconds * AimCorrectionSpeed, 0.0f, 1.0f)).GetNormalized();
	BladeArmTurn = BladeArmTotal.Rotator();
	BladeHandTotal = FQuat::Slerp(BladeHandTotal, HandTarget, FMath::Clamp(DeltaSeconds * AimCorrectionSpeed, 0.0f, 1.0f)).GetNormalized();
	BladeHandTurn = BladeHandTotal.Rotator();
}
