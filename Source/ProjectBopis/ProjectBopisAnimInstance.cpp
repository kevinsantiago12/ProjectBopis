// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProjectBopisAnimInstance.h"
#include "BopisCharacterBase.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/ShootdodgeComponent.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

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
	const ABopisCharacterBase* Character = Cast<ABopisCharacterBase>(TryGetPawnOwner());
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
		bIsPistolHold = IsPistolAnimType(CurrentAnimType);
		bIsDualWield = Weapon->IsDualWield();
	}

	bDualSpread = bIsDualWield && !bIsAiming;

	UpdateUpperBody(DeltaSeconds);
	UpdateLeftHandGrip(*Character, Weapon);
	UpdateArmAlphas(Weapon, DeltaSeconds);
	UpdateFreeArmSwing(DeltaSeconds);
	UpdateRecoil(DeltaSeconds);
	UpdateTurnInPlace(Character->GetActorRotation().Yaw, DeltaSeconds);
	UpdateShootdodgeAim(*Character, DeltaSeconds);
	UpdateProneDirection(DeltaSeconds);
	UpdateProneFeet(*Character, DeltaSeconds);
	UpdateShootdodgeAimCorrection(*Character, Weapon, DeltaSeconds);
}

void UProjectBopisAnimInstance::UpdateShootdodgeAimCorrection(const ABopisCharacterBase& Character, const AWeaponBase* Weapon, float DeltaSeconds)
{
	// The dive and prone clips aim wherever they were authored; the shots go to the crosshair.
	// So the upper body turns until the gun points there too. Outside the dive's own phases
	// it eases back to nothing.
	const USkeletalMeshComponent* Mesh = Character.GetMesh();
	const APlayerController* PlayerController = Cast<APlayerController>(Character.GetController());
	FQuat Target = FQuat::Identity;

	if (bShootdodging && Mesh && Weapon && PlayerController)
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

		// The gun as drawn (correction included) and where it should point, both in the mesh's
		// own space, where the spine nodes apply their rotation.
		const FTransform Muzzle = Weapon->GetMuzzleTransform();
		const FTransform& ToComponent = Mesh->GetComponentTransform();
		const FVector GunDirection = ToComponent.InverseTransformVectorNoScale(Muzzle.GetUnitAxis(EAxis::X));
		const FVector WantedDirection = ToComponent.InverseTransformVectorNoScale(
			(AimPoint - Muzzle.GetLocation()).GetSafeNormal());

		// The rest of the way from here: added on top of the correction already applied. Each
		// frame measures the result, so it settles rather than overshooting.
		Target = FQuat::FindBetweenNormals(GunDirection, WantedDirection) * AimCorrectionTotal;

		// Capped: past the limit the spine would corkscrew; the gun stays off instead.
		FVector Axis;
		float Angle;
		Target.ToAxisAndAngle(Axis, Angle);
		Angle = FMath::UnwindRadians(Angle);
		const float MaxAngle = FMath::DegreesToRadians(AimCorrectionMaxAngle);
		if (FMath::Abs(Angle) > MaxAngle)
		{
			Target = FQuat(Axis, FMath::Sign(Angle) * MaxAngle);
		}
	}

	const float Alpha = FMath::Clamp(DeltaSeconds * AimCorrectionSpeed, 0.0f, 1.0f);
	AimCorrectionTotal = FQuat::Slerp(AimCorrectionTotal, Target, Alpha).GetNormalized();

	// Half on each of two spine bones: the same mesh-space turn twice adds up to the whole.
	ShootdodgeAimCorrection = FQuat::Slerp(FQuat::Identity, AimCorrectionTotal, 0.5f).Rotator();
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
	const float Remaining = FRotator::NormalizeAxis(PoseDirection - ProneBlendDirection);
	ProneBlendDirection = FRotator::NormalizeAxis(
		ProneBlendDirection + FMath::FInterpTo(0.0f, Remaining, DeltaSeconds, PronePoseSwapSpeed));

	// The pose shows the body lying a little off the real direction: turn the whole body by
	// the difference so it lies where the dive put it, and the spine back by the same (half
	// on each of two bones) so the gun still points at the aim.
	const float Difference = FRotator::NormalizeAxis(ShootdodgeDirection - ProneBlendDirection);
	ProneBodyTurn = FRotator(0.0f, Difference, 0.0f);
	ProneSpineCounterTurn = FRotator(0.0f, -0.5f * Difference, 0.0f);
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
		ShootdodgeDirection = Shootdodge->GetDirectionAngle();
		ShootdodgePlayRate = Shootdodge->GetPhasePlayRate();
		ShootdodgeStartPosition = Shootdodge->GetPhaseStartPosition();
	}

	const FRotator Control = Character.GetControlRotation();
	ShootdodgeAimYaw = FRotator::NormalizeAxis(Control.Yaw - Character.GetActorRotation().Yaw);
	ShootdodgeAimPitch = FRotator::NormalizeAxis(Control.Pitch);
}

void UProjectBopisAnimInstance::UpdateLocomotion(const ABopisCharacterBase& Character)
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

	// Left-hand IK: long guns only, and only while aiming (ADS). Every other pose —
	// lowered, hip-fire raised, moving, pistols — keeps its hand-authored left hand.
	// Target: the weapon's LeftHandGrip socket, else the clip's ik_hand_l. Off while
	// reload-animating. Eases on, snaps off.
	const bool bLongGun = !IsPistolAnimType(CurrentAnimType);
	const double IKTarget = (bIsAiming && bLongGun && !bIsDualWield && !bReloadAnimating) ? 1.0 : 0.0;

	LeftHandIKAlpha = IKTarget < LeftHandIKAlpha
		? IKTarget
		: FMath::FInterpTo(LeftHandIKAlpha, IKTarget, DeltaSeconds, LeftHandIKInterpSpeed);

	// One-handed pistol: the raised pistol poses are two-handed, so while raised the free
	// left arm is overridden with the at-side pose. It follows the raised layer, and eases
	// out for reload montages (and back in after) so the two-handed reload blends in.
	FreeArmReloadBlend = FMath::FInterpTo(
		FreeArmReloadBlend, bReloadAnimating ? 0.0f : 1.0f, DeltaSeconds, UpperBodyInterpSpeed);

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

void UProjectBopisAnimInstance::AddRecoil(bool bOffhand)
{
	FFloatSpringState& Spring = bOffhand ? OffhandRecoilSpring : MainRecoilSpring;
	Spring.Velocity += RecoilImpulse;
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
