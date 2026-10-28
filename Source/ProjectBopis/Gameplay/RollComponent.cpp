// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/RollComponent.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/ShootdodgeComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Gameplay/FocusComponent.h"
#include "Misc/App.h"

URollComponent::URollComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void URollComponent::BeginPlay()
{
	Super::BeginPlay();

	Character = Cast<AProjectBopisCharacter>(GetOwner());
}

void URollComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	CooldownLeft = FMath::Max(0.0f, CooldownLeft - DeltaTime);
	FireDelayLeft = FMath::Max(0.0f, FireDelayLeft - DeltaTime);

	// This roll's slow motion counts down in real seconds — FApp's delta is from before the
	// dilation — and ends on its own, even after the roll.
	if (bOwnsFocus)
	{
		RollFocusLeft -= FApp::GetDeltaTime();
		if (RollFocusLeft <= 0.0f)
		{
			bOwnsFocus = false;
			if (UFocusComponent* Focus = Character ? Character->GetFocus() : nullptr)
			{
				Focus->EndFreeFocus();
			}
		}
	}

	if (RollMontage && Character)
	{
		UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
		const float Position = AnimInstance ? AnimInstance->Montage_GetPosition(RollMontage) : 0.0f;
		const float Length = RollMontage->GetPlayLength();

		// The tumble lands: the thud.
		if (!bRollThudDone && Position >= Length * RollThudAt)
		{
			bRollThudDone = true;
			Character->PlayRollThud();
		}

		// Partway in: slow motion to line up the way out. Not if the player's own Focus is on
		// (BeginFreeFocus leaves that alone).
		if (bRollFocus && !bRollFocusDone && Position >= Length * RollFocusStartAt)
		{
			bRollFocusDone = true;
			UFocusComponent* Focus = Character->GetFocus();
			if (Focus && Focus->BeginFreeFocus())
			{
				bOwnsFocus = true;
				RollFocusLeft = RollFocusDuration;
			}
		}

		// The stick let go partway through: cut into a kneel (Vanquish), if the kneel is on
		// (the character's bPostRollCrouch). Still pushed, it runs out below instead.
		const FVector Input = Character->GetLastMovementInputVector();
		const bool bPlaying = AnimInstance && AnimInstance->Montage_IsPlaying(RollMontage);
		if (bPlaying && Position >= Length * CrouchOutAfter && Character->CanPostRollCrouch()
			&& !Character->IsPushingStick())
		{
			EndRoll();
			Character->StartPostRollCrouch();
			AnimInstance->Montage_Stop(CrouchOutBlendTime, RollMontage);
		}
		// Moving out of the recovery: cut the roll short and hand control back, running.
		else if (bPlaying && Position >= Length * MoveOutAfter && !Input.IsNearlyZero())
		{
			AnimInstance->Montage_Stop(MoveOutBlendTime, RollMontage);
			if (bCarryMomentum)
			{
				UCharacterMovementComponent* Movement = Character->GetCharacterMovement();
				const FVector Run = Input.GetSafeNormal2D() * Movement->MaxWalkSpeed;
				Movement->Velocity = FVector(Run.X, Run.Y, Movement->Velocity.Z);
			}
			EndRoll();
		}
		// Played out (or cut off) — caught as it starts blending out.
		else if (!AnimInstance || !AnimInstance->Montage_IsPlaying(RollMontage)
			|| Position >= Length - BlendOutTime * PlayRate)
		{
			EndRoll();
		}
	}
}

bool URollComponent::TryRoll()
{
	if (!Character || IsRolling() || CooldownLeft > 0.0f || Character->IsDead()
		|| !Character->GetCharacterMovement()->IsMovingOnGround())
	{
		return false;
	}
	if (const UShootdodgeComponent* Shootdodge = Character->GetShootdodge(); Shootdodge && Shootdodge->IsDodging())
	{
		return false;
	}

	const FRollAnims* Anims = Animations.Find(PickDirection());
	UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance();
	if (!Anims || Anims->Clips.Num() == 0 || !AnimInstance)
	{
		return false;
	}
	UAnimSequenceBase* Clip = Anims->Clips[FMath::RandRange(0, Anims->Clips.Num() - 1)];
	if (!Clip)
	{
		return false;
	}

	// The clips are picked relative to the camera but play relative to the body: square the
	// body up to the camera first, so "right" is right on screen whatever way it was facing.
	Character->SetActorRotation(FRotator(0.0f, Character->GetControlRotation().Yaw, 0.0f));

	RollMontage = AnimInstance->PlaySlotAnimationAsDynamicMontage(Clip, SlotName, BlendInTime, BlendOutTime, PlayRate);
	if (!RollMontage)
	{
		return false;
	}
	bRollFocusDone = false;
	bRollThudDone = false;

	// The roll's root motion runs in the body's frame: lock the body's rotation to the
	// animation, or turning the camera would steer the roll.
	Character->SetAnimationDrivenRotation(true);
	return true;
}

void URollComponent::Cancel()
{
	if (!IsRolling())
	{
		return;
	}
	if (UAnimInstance* AnimInstance = Character->GetMesh()->GetAnimInstance())
	{
		AnimInstance->Montage_Stop(0.0f, RollMontage);
	}

	// Death takes over the slow motion; this roll's ends here.
	if (bOwnsFocus)
	{
		bOwnsFocus = false;
		if (UFocusComponent* Focus = Character->GetFocus())
		{
			Focus->EndFreeFocus();
		}
	}
	EndRoll();
}

void URollComponent::EndRoll()
{
	RollMontage = nullptr;
	CooldownLeft = Cooldown;
	FireDelayLeft = FireDelayAfterRoll;
	if (Character)
	{
		Character->SetAnimationDrivenRotation(false);
	}
}

EShootdodgeDirection URollComponent::PickDirection() const
{
	const FVector Input = Character->GetLastMovementInputVector();
	if (Input.IsNearlyZero())
	{
		return EShootdodgeDirection::Forward;
	}

	// Nearest eighth of a turn, relative to the camera; the enum's order is the octant order.
	const FVector Local = FRotator(0.0f, Character->GetControlRotation().Yaw, 0.0f).UnrotateVector(Input);
	const float Angle = FMath::RadiansToDegrees(FMath::Atan2(Local.Y, Local.X));
	const int32 Octant = (FMath::RoundToInt(FRotator::NormalizeAxis(Angle) / 45.0f) + 8) % 8;
	return static_cast<EShootdodgeDirection>(Octant);
}
