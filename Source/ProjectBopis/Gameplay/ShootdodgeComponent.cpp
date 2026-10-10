// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/ShootdodgeComponent.h"
#include "Gameplay/FocusComponent.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
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

	Direction = PickDirection();
	const FShootdodgeAnims* Anims = Animations.Find(Direction);
	if (!Anims || !Anims->Loop)
	{
		return false;
	}

	Focus->SpendMeter(FocusCost);

	// Face the camera, so every direction is relative to where the player is looking.
	Character->SetActorRotation(FRotator(0.0f, Character->GetControlRotation().Yaw, 0.0f));
	Character->SetAnimationDrivenRotation(true);
	Character->GetCharacterMovement()->StopMovementImmediately();

	// Straight into the air: a dodge is a reaction, so nothing stands between the key
	// and leaving the ground.
	TakeOff();
	return true;
}

EShootdodgeDirection UShootdodgeComponent::PickDirection() const
{
	const FVector Input = Character->GetLastMovementInputVector();
	if (Input.IsNearlyZero())
	{
		return EShootdodgeDirection::Forward;
	}

	// Angle of the input in the camera's frame: 0 ahead, +90 right. Rounded to the nearest
	// eighth of a turn, which is the enum's order.
	const FVector Local = FRotator(0.0f, Character->GetControlRotation().Yaw, 0.0f).UnrotateVector(Input);
	const float Angle = FMath::RadiansToDegrees(FMath::Atan2(Local.Y, Local.X));
	const int32 Octant = (FMath::RoundToInt(Angle / 45.0f) + 8) % 8;
	return static_cast<EShootdodgeDirection>(Octant);
}

void UShootdodgeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	switch (Phase)
	{
	case EShootdodgePhase::Airborne:
		// Push-off done, still flying: settle into the looping flight pose.
		if (!bLooping && HasFinished(ActiveMontage))
		{
			ActiveMontage = Play(Animations.FindChecked(Direction).Loop, LoopPlayRate, 1000);
			bLooping = true;
		}
		break;

	case EShootdodgePhase::Landing:
		if (HasFinished(ActiveMontage))
		{
			EnterProne();
		}
		break;

	case EShootdodgePhase::GettingUp:
		if (HasFinished(ActiveMontage))
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
	const FShootdodgeAnims& Anims = Animations.FindChecked(Direction);

	// The dive direction in the world: the camera's yaw turned by this direction's eighth.
	const float Yaw = Character->GetActorRotation().Yaw + static_cast<int32>(Direction) * 45.0f;
	const FVector Horizontal = FRotator(0.0f, Yaw, 0.0f).Vector();

	// Lighter gravity for the flight: a floatier arc than the launch alone would give.
	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	SavedGravityScale = Movement->GravityScale;
	Movement->GravityScale = SavedGravityScale * DiveGravityScale;
	SavedAirBraking = Movement->BrakingDecelerationFalling;
	Movement->BrakingDecelerationFalling = DiveAirBraking;

	Character->LaunchCharacter(Horizontal * DiveSpeed + FVector::UpVector * DiveLift, true, true);

	Phase = EShootdodgePhase::Airborne;

	// The tail of the push-off — from where the feet leave the ground — then the loop.
	const float Offset = Anims.StartOffset >= 0.0f ? Anims.StartOffset : StartClipOffset;
	const float ClipLength = Anims.Start ? Anims.Start->GetPlayLength() : 0.0f;
	bLooping = !Anims.Start || Offset >= ClipLength;
	ActiveMontage = bLooping ? Play(Anims.Loop, LoopPlayRate, 1000) : Play(Anims.Start, StartPlayRate, 1, Offset);
}

void UShootdodgeComponent::NotifyLanded()
{
	if (Phase != EShootdodgePhase::Airborne)
	{
		return;
	}

	// Normal gravity again. The horizontal speed carries on as a slide, slowed only by
	// LandSlideDeceleration (friction off), until the body comes to rest.
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

	const FShootdodgeAnims& Anims = Animations.FindChecked(Direction);
	Phase = EShootdodgePhase::Landing;
	// Straight to the impact: the clip's airborne lead-in already happened as the real fall.
	const float LandStart = Anims.LandOffset >= 0.0f ? Anims.LandOffset : LandClipOffset;
	ActiveMontage = Play(Anims.Land, LandPlayRate, 1, LandStart);
	if (!ActiveMontage)
	{
		EnterProne();
	}
}

void UShootdodgeComponent::EnterProne()
{
	const FShootdodgeAnims& Anims = Animations.FindChecked(Direction);
	Phase = EShootdodgePhase::Prone;
	ActiveMontage = Play(Anims.Prone, PronePlayRate, 1000);
}

void UShootdodgeComponent::NotifyMoveInput()
{
	if (Phase != EShootdodgePhase::Prone)
	{
		return;
	}

	const FShootdodgeAnims& Anims = Animations.FindChecked(Direction);
	Phase = EShootdodgePhase::GettingUp;
	ActiveMontage = Play(Anims.Getup, GetupPlayRate);
	if (!ActiveMontage)
	{
		Finish();
	}
}

void UShootdodgeComponent::Finish()
{
	if (UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance(); AnimInstance && ActiveMontage)
	{
		AnimInstance->Montage_Stop(0.2f, ActiveMontage);
	}

	ActiveMontage = nullptr;
	Phase = EShootdodgePhase::None;
	Character->GetCharacterMovement()->GravityScale = SavedGravityScale;
	Character->GetCharacterMovement()->BrakingDecelerationFalling = SavedAirBraking;

	UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
	if (Phase == EShootdodgePhase::None && SavedWalkingBraking > 0.0f)
	{
		Movement->BrakingDecelerationWalking = SavedWalkingBraking;
		Movement->bUseSeparateBrakingFriction = bSavedSeparateBrakingFriction;
		Movement->BrakingFriction = SavedBrakingFriction;
	}

	Character->SetAnimationDrivenRotation(false);
}

UAnimMontage* UShootdodgeComponent::Play(UAnimSequenceBase* Clip, float PlayRate, int32 LoopCount, float StartTime)
{
	UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
	if (!Clip || !AnimInstance)
	{
		return nullptr;
	}

	// Short blends: the clips are cut together into one motion.
	return AnimInstance->PlaySlotAnimationAsDynamicMontage(Clip, SlotName, 0.1f, 0.1f, PlayRate,
		LoopCount, -1.0f, StartTime);
}

bool UShootdodgeComponent::HasFinished(const UAnimMontage* Montage) const
{
	const UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
	return !Montage || !AnimInstance || !AnimInstance->Montage_IsPlaying(Montage)
		|| AnimInstance->Montage_GetPosition(Montage) >= Montage->GetPlayLength() - 0.1f;
}
