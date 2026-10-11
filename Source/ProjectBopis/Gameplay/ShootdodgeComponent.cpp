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

UShootdodgeComponent::UShootdodgeComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UShootdodgeComponent::BeginPlay()
{
	Super::BeginPlay();

	Character = Cast<AProjectBopisCharacter>(GetOwner());
}

bool UShootdodgeComponent::TryStart()
{
	if (!Character || IsDodging() || Character->bIsCrouched
		|| !Character->GetCharacterMovement()->IsMovingOnGround())
	{
		return false;
	}

	// Pistols and duals only, for now — the only weapons the dive is animated for.
	const UWeaponHolderComponent* Holder = Character->GetWeaponHolder();
	const AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr;
	if (!Weapon || !IsPistolAnimType(Weapon->GetAnimType()) || Character->IsEquipAnimating())
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
	// go of in TickComponent once fully out), and the movement gets its braking back.
	if (Phase == EShootdodgePhase::WindUp)
	{
		if (UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance())
		{
			AnimInstance->Montage_Stop(WindUpBlendOutTime, WindUpMontage);
			AnimInstance->SetRootMotionMode(SavedRootMotionMode);
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

	// The wind-up counts until its animation has fully blended out over the flight.
	if (WindUpMontage && Phase != EShootdodgePhase::WindUp)
	{
		const UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
		if (!AnimInstance || !AnimInstance->Montage_IsActive(WindUpMontage))
		{
			WindUpMontage = nullptr;
		}
	}

	// Winding up, flying, landing and lying prone, the body turns to face the aim; the blend
	// spaces show the dive (and the prone pose) for the flight's direction relative to it.
	if (Phase == EShootdodgePhase::WindUp || Phase == EShootdodgePhase::Start || Phase == EShootdodgePhase::Loop
		|| Phase == EShootdodgePhase::Land || Phase == EShootdodgePhase::Prone)
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
