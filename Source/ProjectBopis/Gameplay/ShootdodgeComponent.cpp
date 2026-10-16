// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/ShootdodgeComponent.h"
#include "Gameplay/FocusComponent.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequenceBase.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"

UShootdodgeComponent::UShootdodgeComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UShootdodgeComponent::BeginPlay()
{
	Super::BeginPlay();

	Character = Cast<AProjectBopisCharacter>(GetOwner());

	// Don't make the movement wait for this component's tick (AddTickPrerequisiteComponent):
	// it reorders the frame so the landing's switch of the legs onto physics (made inside the
	// movement update) races the mesh's animation work on another thread, and crashes. The
	// wall check's trimmed velocity simply takes effect a frame later.

	// The Start blend space captures its start position when it first initializes, so it must
	// be the push-off point from the outset, not 0 (see GetRestStartPosition).
	PhaseStartPosition = GetRestStartPosition();
}

float UShootdodgeComponent::GetRestStartPosition() const
{
	const FShootdodgeAnims* Forward = Animations.Find(EShootdodgeDirection::Forward);
	if (!Forward || !Forward->Start || Forward->Start->GetPlayLength() <= 0.0f)
	{
		return 0.0f;
	}
	const float Offset = Forward->StartOffset >= 0.0f ? Forward->StartOffset : StartClipOffset;
	return FMath::Clamp(Offset / Forward->Start->GetPlayLength(), 0.0f, 1.0f);
}

bool UShootdodgeComponent::TryStart()
{
	if (!Character || IsDodging() || Character->bIsCrouched
		|| !Character->GetCharacterMovement()->IsMovingOnGround())
	{
		return false;
	}

	// Any weapon unless bPistolsOnly: the dive is animated for pistols, and long guns borrow
	// it with their own arm hold (the AnimGraph layers it on, see the anim instance).
	const UWeaponHolderComponent* Holder = Character->GetWeaponHolder();
	const AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr;
	if (!Weapon || (bPistolsOnly && !IsPistolAnimType(Weapon->GetAnimType())) || Character->IsEquipAnimating())
	{
		return false;
	}

	UFocusComponent* Focus = Character->GetFocus();
	if (!Focus || Focus->GetMeter() < MinFocusToDive)
	{
		return false;
	}

	const EShootdodgeDirection Direction = PickDirection();
	if (!Animations.Contains(Direction))
	{
		return false;
	}

	// Rotation belongs to the dive from the press: the body turns toward the camera over the
	// next moments (TickComponent), through the wind-up and the flight.
	Character->SetAnimationDrivenRotation(true);

	// The wind-up is the deliberate dive, from a held aim; from anything else (running,
	// hip-fire) the dive goes on the press.
	if (!bWindUp || !Character->IsAiming() || !BeginWindUp(Direction))
	{
		Launch(Direction);
	}
	return true;
}

UAnimSequenceBase* UShootdodgeComponent::PickWindUp(EShootdodgeDirection Direction) const
{
	// Lyra's dash comes in four directions. Forward and its diagonals take the forward dash;
	// the back diagonals take the side dash on their side; only straight back (within 22.5°
	// of it — the Backward octant) takes the backward dash.
	switch (Direction)
	{
	case EShootdodgeDirection::Forward:
	case EShootdodgeDirection::ForwardRight:
	case EShootdodgeDirection::ForwardLeft:   return WindUpForward;
	case EShootdodgeDirection::Right:
	case EShootdodgeDirection::BackwardRight: return WindUpRight;
	case EShootdodgeDirection::Left:
	case EShootdodgeDirection::BackwardLeft:  return WindUpLeft;
	case EShootdodgeDirection::Backward:      return WindUpBackward;
	default:                                  return nullptr;
	}
}

bool UShootdodgeComponent::BeginWindUp(EShootdodgeDirection Direction)
{
	UAnimSequenceBase* Clip = PickWindUp(Direction);
	UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
	if (!Clip || !AnimInstance || WindUpLength <= 0.0f)
	{
		return false;
	}

	// The dash clips carry root motion; the wind-up plays in place, so it's ignored until the
	// launch.
	SavedRootMotionMode = AnimInstance->RootMotionMode;
	AnimInstance->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);

	WindUpMontage = AnimInstance->PlaySlotAnimationAsDynamicMontage(Clip, SlotName, 0.1f, 0.15f, WindUpPlayRate);
	if (!WindUpMontage)
	{
		AnimInstance->SetRootMotionMode(SavedRootMotionMode);
		return false;
	}

	// Carry the run into the wind-up, slowing gradually: movement input goes to the dive now
	// (and is ignored), so the walking braking would otherwise stop the character dead.
	// Until the launch the speed bleeds off at WindUpDeceleration instead, friction off.
	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	SavedWalkingBraking = Movement->BrakingDecelerationWalking;
	bSavedSeparateBrakingFriction = Movement->bUseSeparateBrakingFriction;
	SavedBrakingFriction = Movement->BrakingFriction;
	Movement->BrakingDecelerationWalking = WindUpDeceleration;
	Movement->bUseSeparateBrakingFriction = true;
	Movement->BrakingFriction = 0.0f;

	WindUpDirection = Direction;
	Phase = EShootdodgePhase::WindUp;
	PhaseTime = 0.0f;
	PhaseDuration = WindUpLength / WindUpPlayRate;
	return true;
}

void UShootdodgeComponent::Launch(EShootdodgeDirection Direction)
{
	// The wind-up (if any) hands over: its montage blends out over the dive's Start (it's let
	// go of in TickComponent once fully out, and only then does root motion come back — the
	// dash's own, still blending, would otherwise push the flight up), and the movement gets
	// its braking back.
	if (Phase == EShootdodgePhase::WindUp)
	{
		if (UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance())
		{
			AnimInstance->Montage_Stop(WindUpBlendOutTime, WindUpMontage);
		}

		UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
		Movement->BrakingDecelerationWalking = SavedWalkingBraking;
		Movement->bUseSeparateBrakingFriction = bSavedSeparateBrakingFriction;
		Movement->BrakingFriction = SavedBrakingFriction;
	}

	if (UFocusComponent* Focus = Character->GetFocus())
	{
		Focus->SpendMeter(FocusCost);
	}

	// The flight goes this direction's eighth of a turn away from the camera.
	Character->GetCharacterMovement()->StopMovementImmediately();
	DiveYaw = Character->GetControlRotation().Yaw + static_cast<int32>(Direction) * 45.0f;

	TakeOff();
}

EShootdodgeDirection UShootdodgeComponent::PickDirection() const
{
	const FVector Input = Character->GetLastMovementInputVector();
	if (Input.IsNearlyZero())
	{
		return EShootdodgeDirection::Forward;
	}

	const FVector Local = FRotator(0.0f, Character->GetControlRotation().Yaw, 0.0f).UnrotateVector(Input);
	return OctantOf(FMath::RadiansToDegrees(FMath::Atan2(Local.Y, Local.X)));
}

EShootdodgeDirection UShootdodgeComponent::OctantOf(float Angle)
{
	// Nearest eighth of a turn; the enum's order is the octant order.
	const int32 Octant = (FMath::RoundToInt(FRotator::NormalizeAxis(Angle) / 45.0f) + 8) % 8;
	return static_cast<EShootdodgeDirection>(Octant);
}

float UShootdodgeComponent::GetDirectionAngle() const
{
	return Character ? FRotator::NormalizeAxis(DiveYaw - Character->GetActorRotation().Yaw) : 0.0f;
}

float UShootdodgeComponent::GetPhasePlayRate() const
{
	switch (Phase)
	{
	case EShootdodgePhase::Start: return StartPlayRate;
	case EShootdodgePhase::Loop:  return LoopPlayRate;
	case EShootdodgePhase::Land:  return LandPlayRate;
	case EShootdodgePhase::Prone: return PronePlayRate;
	default:                      return 1.0f;
	}
}

float UShootdodgeComponent::PhaseLength(const UAnimSequenceBase* Clip, float Offset, float PlayRate)
{
	return Clip ? FMath::Max(0.0f, Clip->GetPlayLength() - Offset) / PlayRate : 0.0f;
}

void UShootdodgeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	PhaseTime += DeltaTime;

	// Slid off an edge while landing or lying down: back into the air, to land again.
	if ((Phase == EShootdodgePhase::Land || Phase == EShootdodgePhase::Prone)
		&& Character->GetCharacterMovement()->IsFalling())
	{
		FallOffEdge();
	}

	if (IsBodyDown())
	{
		KeepBodyOutOfWalls(DeltaTime);
	}

	// The wind-up counts until its animation has fully blended out over the flight; then root
	// motion comes back.
	if (WindUpMontage && Phase != EShootdodgePhase::WindUp)
	{
		UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
		if (!AnimInstance || !AnimInstance->Montage_IsActive(WindUpMontage))
		{
			WindUpMontage = nullptr;
			if (AnimInstance)
			{
				AnimInstance->SetRootMotionMode(SavedRootMotionMode);
			}
		}
	}

	// Winding up, flying, landing and lying prone, the body turns to face the aim; the blend
	// spaces show the dive (and the prone pose) for the flight's direction relative to it.
	if (Phase == EShootdodgePhase::WindUp || IsBodyDown())
	{
		const FRotator Aim(0.0f, Character->GetControlRotation().Yaw, 0.0f);
		Character->SetActorRotation(FaceAimSpeed > 0.0f
			? FMath::RInterpTo(Character->GetActorRotation(), Aim, DeltaTime, FaceAimSpeed)
			: Aim);
	}

	switch (Phase)
	{
	case EShootdodgePhase::WindUp:
		if (PhaseTime >= PhaseDuration)
		{
			Launch(WindUpDirection);
		}
		break;

	case EShootdodgePhase::Start:
		if (PhaseTime >= PhaseDuration)
		{
			Phase = EShootdodgePhase::Loop;
			PhaseTime = 0.0f;
			PhaseStartPosition = 0.0f;
		}
		break;

	case EShootdodgePhase::Land:
		if (PhaseTime >= PhaseDuration)
		{
			EnterProne();
		}
		break;

	case EShootdodgePhase::GettingUp:
		if (HasFinished(GetupMontage))
		{
			Finish();
		}
		break;

	default:
		break;
	}
}

void UShootdodgeComponent::TakeOff()
{
	// Lighter gravity and no air braking for the flight.
	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	SavedGravityScale = Movement->GravityScale;
	Movement->GravityScale = SavedGravityScale * DiveGravityScale;
	SavedAirBraking = Movement->BrakingDecelerationFalling;
	Movement->BrakingDecelerationFalling = DiveAirBraking;

	// The body flies, lands and lies flat: a standing-height capsule would catch on what it
	// visibly clears (a low window, under a table). Short from here until getting up.
	ShrinkCapsule();

	Character->LaunchCharacter(FRotator(0.0f, DiveYaw, 0.0f).Vector() * DiveSpeed
		+ FVector::UpVector * DiveLift, true, true);

	// The Start phase lasts as long as the take-off direction's clip has left to play.
	const FShootdodgeAnims& Anims = Animations.FindChecked(OctantOf(GetDirectionAngle()));
	const float Offset = Anims.StartOffset >= 0.0f ? Anims.StartOffset : StartClipOffset;
	const float Length = Anims.Start ? Anims.Start->GetPlayLength() : 0.0f;

	Phase = EShootdodgePhase::Start;
	PhaseTime = 0.0f;
	PhaseDuration = PhaseLength(Anims.Start, Offset, StartPlayRate);
	PhaseStartPosition = Length > 0.0f ? FMath::Clamp(Offset / Length, 0.0f, 1.0f) : 0.0f;

	if (bSlowMotion)
	{
		if (UFocusComponent* Focus = Character->GetFocus())
		{
			bOwnsSlowMotion = Focus->BeginFreeFocus();
		}
	}
}

void UShootdodgeComponent::GetBodyShape(FVector& OutCentre, FQuat& OutRotation, float& OutRadius, float& OutHalfHeight) const
{
	// The body lies along the line it launched on and never turns from it: a capsule laid flat
	// along the dive's direction, centred on the character, resting on the main capsule's
	// bottom — the same shape from take-off until standing up.
	const UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
	OutRadius = BodyCapsuleRadius;
	OutHalfHeight = FMath::Max(BodyCapsuleRadius, BodyCapsuleHalfLength);
	OutCentre = Character->GetActorLocation()
		+ FVector(0.0f, 0.0f, BodyCapsuleRadius - Capsule->GetScaledCapsuleHalfHeight());
	OutRotation = FRotationMatrix::MakeFromZ(FRotator(0.0f, DiveYaw, 0.0f).Vector()).ToQuat();
}

void UShootdodgeComponent::KeepBodyOutOfWalls(float DeltaTime)
{
	if (!bBodyCollision)
	{
		return;
	}

	// Geometry queries only — nothing is created or moved, so nothing touches the mesh's
	// physics. The body shape is swept ahead by this frame's movement; the velocity into
	// whatever wall it meets comes off, so the body slides along it, the way the main capsule
	// does. Tested just clear of the floor it lies on; floor-like surfaces aren't walls.
	FVector Centre;
	FQuat Rotation;
	float Radius, HalfHeight;
	GetBodyShape(Centre, Rotation, Radius, HalfHeight);
	Centre.Z += 2.0f;

	// Swept ahead by this frame's movement — or a hair, standing still, so an overlap is still
	// found while lying there.
	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	FVector Move = FVector(Movement->Velocity.X, Movement->Velocity.Y, 0.0f) * DeltaTime;
	if (Move.IsNearlyZero())
	{
		Move = FVector(0.0f, 0.0f, 0.1f);
	}

	FCollisionQueryParams Params(SCENE_QUERY_STAT(ShootdodgeBody), false, Character);
	FCollisionResponseParams Responses(ECR_Ignore);
	Responses.CollisionResponse.SetResponse(ECC_WorldStatic, ECR_Block);
	Responses.CollisionResponse.SetResponse(ECC_WorldDynamic, ECR_Block);

	FHitResult Hit;
	if (!GetWorld()->SweepSingleByChannel(Hit, Centre, Centre + Move, Rotation, ECC_Pawn,
		FCollisionShape::MakeCapsule(Radius, HalfHeight), Params, Responses))
	{
		return;
	}

	const FVector Normal = Hit.bStartPenetrating ? Hit.Normal : Hit.ImpactNormal;
	if (Normal.Z >= 0.7f)
	{
		return;
	}
	const FVector Wall = FVector(Normal.X, Normal.Y, 0.0f).GetSafeNormal();

	// Already in it (diving off right beside a wall, or slid along into it): eased back out,
	// a little each frame rather than popping.
	if (Hit.bStartPenetrating)
	{
		const float Out = FMath::Min(Hit.PenetrationDepth + 0.5f, BodyPushOutPerFrame);
		Character->AddActorWorldOffset(Wall * Out, true);
	}

	// No further into it: the velocity into the wall comes off; along it stays.
	const float Into = FVector::DotProduct(Movement->Velocity, Wall);
	if (Into < 0.0f)
	{
		Movement->Velocity -= Wall * Into;
	}
}

void UShootdodgeComponent::ShrinkCapsule()
{
	UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
	const float FullHalfHeight = Capsule->GetUnscaledCapsuleHalfHeight();
	const float ShortHalfHeight = FMath::Max(DiveCapsuleHalfHeight, Capsule->GetUnscaledCapsuleRadius());
	if (bCapsuleShrunk || ShortHalfHeight >= FullHalfHeight)
	{
		return;
	}

	// The bottom stays where it is: the centre comes down by the difference and the mesh goes
	// back up by the same, so nothing visibly moves. (The camera is re-derived from the
	// capsule's size every frame, as for crouching.)
	SavedCapsuleHalfHeight = FullHalfHeight;
	const float Drop = FullHalfHeight - ShortHalfHeight;
	Capsule->SetCapsuleHalfHeight(ShortHalfHeight);
	Character->AddActorWorldOffset(FVector(0.0, 0.0, -Drop * Capsule->GetShapeScale()));
	Character->GetMesh()->AddRelativeLocation(FVector(0.0, 0.0, Drop));
	bCapsuleShrunk = true;
}

bool UShootdodgeComponent::RestoreCapsule()
{
	if (!bCapsuleShrunk)
	{
		return true;
	}

	UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
	const float Drop = SavedCapsuleHalfHeight - Capsule->GetUnscaledCapsuleHalfHeight();
	const FVector StandingCentre = Capsule->GetComponentLocation() + FVector(0.0, 0.0, Drop * Capsule->GetShapeScale());

	// Room to stand: the full capsule, bottom where it is now, against whatever blocks it.
	FCollisionQueryParams Params(SCENE_QUERY_STAT(ShootdodgeStand), false, Character);
	FCollisionResponseParams Responses;
	Capsule->InitSweepCollisionParams(Params, Responses);
	const FCollisionShape StandingShape = FCollisionShape::MakeCapsule(
		Capsule->GetScaledCapsuleRadius(), SavedCapsuleHalfHeight * Capsule->GetShapeScale());
	if (GetWorld()->OverlapBlockingTestByChannel(StandingCentre, Capsule->GetComponentQuat(),
		Capsule->GetCollisionObjectType(), StandingShape, Params, Responses))
	{
		return false;
	}

	Capsule->SetCapsuleHalfHeight(SavedCapsuleHalfHeight);
	Character->AddActorWorldOffset(FVector(0.0, 0.0, Drop * Capsule->GetShapeScale()));
	Character->GetMesh()->AddRelativeLocation(FVector(0.0, 0.0, -Drop));
	bCapsuleShrunk = false;
	return true;
}

void UShootdodgeComponent::NotifyLanded()
{
	if (!IsAirborne())
	{
		return;
	}

	EndSlowMotion();

	// Normal gravity; the horizontal speed carries on as a slide, slowed only by
	// LandSlideDeceleration (friction off).
	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	Movement->GravityScale = SavedGravityScale;
	Movement->BrakingDecelerationFalling = SavedAirBraking;

	SavedWalkingBraking = Movement->BrakingDecelerationWalking;
	bSavedSeparateBrakingFriction = Movement->bUseSeparateBrakingFriction;
	SavedBrakingFriction = Movement->BrakingFriction;
	Movement->BrakingDecelerationWalking = LandSlideDeceleration;
	Movement->bUseSeparateBrakingFriction = true;
	Movement->BrakingFriction = 0.0f;
	Movement->Velocity.Z = 0.0f;

	// The landing — straight to the impact frame — for the direction it came down in.
	LandDirection = OctantOf(GetDirectionAngle());
	const FShootdodgeAnims& Anims = Animations.FindChecked(LandDirection);
	const float Offset = Anims.LandOffset >= 0.0f ? Anims.LandOffset : LandClipOffset;
	const float Length = Anims.Land ? Anims.Land->GetPlayLength() : 0.0f;

	Phase = EShootdodgePhase::Land;
	PhaseTime = 0.0f;
	PhaseDuration = PhaseLength(Anims.Land, Offset, LandPlayRate);
	PhaseStartPosition = Length > 0.0f ? FMath::Clamp(Offset / Length, 0.0f, 1.0f) : 0.0f;

	// Some landing clips sink the legs into the floor; on physics, the floor pushes them back.
	if (bLandingLegPhysics)
	{
		Character->SimulateLegs(LandingLegHoldStrength);
	}
}

void UShootdodgeComponent::FallOffEdge()
{
	// The walking braking was set for the landing slide; put it back first, so the next
	// landing saves (and Finish restores) the real values rather than the slide's.
	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	Movement->BrakingDecelerationWalking = SavedWalkingBraking;
	Movement->bUseSeparateBrakingFriction = bSavedSeparateBrakingFriction;
	Movement->BrakingFriction = SavedBrakingFriction;

	// Over the edge with the slide's speed: no air braking, so it carries on; normal gravity
	// (the light dive gravity is for the leap, not a fall). NotifyLanded puts the air braking
	// back on touchdown, as for the first landing.
	SavedAirBraking = Movement->BrakingDecelerationFalling;
	Movement->BrakingDecelerationFalling = DiveAirBraking;

	// The landing's physics legs ease off; the body falls in the flight pose.
	Character->EndSimulatedLegs(LandingLegBlendOutTime);
	Phase = EShootdodgePhase::Loop;
	PhaseTime = 0.0f;
	PhaseStartPosition = 0.0f;
}

void UShootdodgeComponent::EnterProne()
{
	Phase = EShootdodgePhase::Prone;
	PhaseTime = 0.0f;
	PhaseStartPosition = 0.0f;

	// Down and settled: the legs ease back to the animation.
	Character->EndSimulatedLegs(LandingLegBlendOutTime);
}

void UShootdodgeComponent::NotifyMoveInput()
{
	RequestGetUp();
}

void UShootdodgeComponent::RequestGetUp(bool bThenReload)
{
	if (Phase != EShootdodgePhase::Prone)
	{
		return;
	}

	// Standing up needs the full capsule to fit where the body lies; under a table or low
	// cover it doesn't, and the body stays down until there's room.
	if (!RestoreCapsule())
	{
		return;
	}

	bReloadQueued = bThenReload;
	Phase = EShootdodgePhase::GettingUp;
	PhaseTime = 0.0f;

	// The get-up for how the body lies now — the player may have turned while down.
	LandDirection = OctantOf(GetDirectionAngle());
	const FShootdodgeAnims& Anims = Animations.FindChecked(LandDirection);
	UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
	GetupMontage = (Anims.Getup && AnimInstance)
		? AnimInstance->PlaySlotAnimationAsDynamicMontage(Anims.Getup, SlotName, 0.15f, 0.2f, GetupPlayRate)
		: nullptr;

	if (!GetupMontage)
	{
		Finish();
	}
}

void UShootdodgeComponent::Finish()
{
	if (UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance(); AnimInstance && GetupMontage)
	{
		AnimInstance->Montage_Stop(0.2f, GetupMontage);
	}
	GetupMontage = nullptr;

	EndSlowMotion();
	Phase = EShootdodgePhase::None;

	// In case the dive ended without lying prone.
	Character->EndSimulatedLegs(LandingLegBlendOutTime);
	RestoreCapsule();

	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	Movement->GravityScale = SavedGravityScale;
	Movement->BrakingDecelerationFalling = SavedAirBraking;
	if (SavedWalkingBraking > 0.0f)
	{
		Movement->BrakingDecelerationWalking = SavedWalkingBraking;
		Movement->bUseSeparateBrakingFriction = bSavedSeparateBrakingFriction;
		Movement->BrakingFriction = SavedBrakingFriction;
	}

	Character->SetAnimationDrivenRotation(false);

	// On the feet again: the reload asked for while lying there goes now.
	if (bReloadQueued)
	{
		bReloadQueued = false;
		Character->ReloadAfterShootdodge();
	}
}

void UShootdodgeComponent::CancelForDeath()
{
	if (UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance())
	{
		if (WindUpMontage)
		{
			AnimInstance->Montage_Stop(0.1f, WindUpMontage);
			AnimInstance->SetRootMotionMode(SavedRootMotionMode);
		}
		if (GetupMontage)
		{
			AnimInstance->Montage_Stop(0.1f, GetupMontage);
		}
	}
	WindUpMontage = nullptr;
	GetupMontage = nullptr;

	EndSlowMotion();
	bReloadQueued = false;
	Phase = EShootdodgePhase::None;
	SetComponentTickEnabled(false);
}

void UShootdodgeComponent::EndSlowMotion()
{
	if (bOwnsSlowMotion)
	{
		if (UFocusComponent* Focus = Character->GetFocus())
		{
			Focus->EndFreeFocus();
		}
	}
	bOwnsSlowMotion = false;
}

bool UShootdodgeComponent::HasFinished(const UAnimMontage* Montage) const
{
	const UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
	return !Montage || !AnimInstance || !AnimInstance->Montage_IsPlaying(Montage)
		|| AnimInstance->Montage_GetPosition(Montage) >= Montage->GetPlayLength() - 0.1f;
}
