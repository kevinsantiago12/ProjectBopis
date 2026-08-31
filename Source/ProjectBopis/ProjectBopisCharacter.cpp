// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Animation/AnimInstance.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "InputActionValue.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "ProjectBopis.h"
#include "Blueprint/UserWidget.h"
#include "UI/ReticleWidget.h"
#include "Weapons/WeaponBase.h"

AProjectBopisCharacter::AProjectBopisCharacter()
{
	// Set size for collision capsule
	GetCapsuleComponent()->InitCapsuleSize(55.f, 96.0f);
	
	WeaponHolder = CreateDefaultSubobject<UWeaponHolderComponent>(TEXT("WeaponHolder"));

	// Create the Camera Component first — the arms attach to it (not the other way around),
	// so the arms rigidly follow camera pitch instead of needing skeletal aim-offset blending
	FirstPersonCameraComponent = CreateDefaultSubobject<UCameraComponent>(TEXT("First Person Camera"));
	FirstPersonCameraComponent->SetupAttachment(GetCapsuleComponent());
	FirstPersonCameraComponent->SetRelativeLocation(FVector(0.0f, 0.0f, 90.0f));
	FirstPersonCameraComponent->bUsePawnControlRotation = true;
	FirstPersonCameraComponent->bEnableFirstPersonFieldOfView = true;
	FirstPersonCameraComponent->bEnableFirstPersonScale = true;
	FirstPersonCameraComponent->FirstPersonFieldOfView = 70.0f;
	FirstPersonCameraComponent->FirstPersonScale = 0.6f;

	// Create the first person mesh, now attached to the camera instead of the body.
	// Relative location/rotation intentionally left at zero — this attachment
	// relationship is new, so there's no prior tuned offset to reuse; needs
	// visual tuning in the editor once compiled.
	FirstPersonMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("First Person Mesh"));
	FirstPersonMesh->SetupAttachment(FirstPersonCameraComponent);
	FirstPersonMesh->SetOnlyOwnerSee(true);
	FirstPersonMesh->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
	FirstPersonMesh->SetCollisionProfileName(FName("NoCollision"));

	// configure the character comps
	GetMesh()->SetOwnerNoSee(true);
	GetMesh()->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::WorldSpaceRepresentation;

	GetCapsuleComponent()->SetCapsuleSize(34.0f, 96.0f);

	// Configure character movement
	GetCharacterMovement()->BrakingDecelerationFalling = 1500.0f;
	GetCharacterMovement()->AirControl = 0.5f;
}

void AProjectBopisCharacter::BeginPlay()
{
	Super::BeginPlay();

	DefaultFOV = FirstPersonCameraComponent->FieldOfView;

	if (IsLocallyControlled() && ReticleWidgetClass)
	{
		if (UReticleWidget* ReticleWidget = CreateWidget<UReticleWidget>(GetWorld(), ReticleWidgetClass))
		{
			ReticleWidget->AddToViewport();
		}
	}
}

void AProjectBopisCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{	
	// Set up action bindings
	if (UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(PlayerInputComponent))
	{
		// Jumping
		EnhancedInputComponent->BindAction(JumpAction, ETriggerEvent::Started, this, &AProjectBopisCharacter::DoJumpStart);
		EnhancedInputComponent->BindAction(JumpAction, ETriggerEvent::Completed, this, &AProjectBopisCharacter::DoJumpEnd);

		//Firing
		EnhancedInputComponent->BindAction(FireAction, ETriggerEvent::Started, this,
			&AProjectBopisCharacter::DoFire);

		EnhancedInputComponent->BindAction(FireAction, ETriggerEvent::Triggered, this,
			&AProjectBopisCharacter::DoFireHeld);

		// Moving
		EnhancedInputComponent->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AProjectBopisCharacter::MoveInput);

		// Looking/Aiming
		EnhancedInputComponent->BindAction(LookAction, ETriggerEvent::Triggered, this, &AProjectBopisCharacter::LookInput);
		EnhancedInputComponent->BindAction(MouseLookAction, ETriggerEvent::Triggered, this, &AProjectBopisCharacter::LookInput);

		EnhancedInputComponent->BindAction(AimAction, ETriggerEvent::Started, this, &AProjectBopisCharacter::DoAimStart);
		EnhancedInputComponent->BindAction(AimAction, ETriggerEvent::Completed, this, &AProjectBopisCharacter::DoAimEnd);

	}
	else
	{
		UE_LOG(LogProjectBopis, Error, TEXT("'%s' Failed to find an Enhanced Input Component! This template is built to use the Enhanced Input system. If you intend to use the legacy system, then you will need to update this C++ file."), *GetNameSafe(this));
	}
}


void AProjectBopisCharacter::MoveInput(const FInputActionValue& Value)
{
	// get the Vector2D move axis
	FVector2D MovementVector = Value.Get<FVector2D>();

	// pass the axis values to the move input
	DoMove(MovementVector.X, MovementVector.Y);

}

void AProjectBopisCharacter::LookInput(const FInputActionValue& Value)
{
	// get the Vector2D look axis
	FVector2D LookAxisVector = Value.Get<FVector2D>();

	// pass the axis values to the aim input
	DoAim(LookAxisVector.X, LookAxisVector.Y);

}

void AProjectBopisCharacter::DoAim(float Yaw, float Pitch)
{
	if (GetController())
	{
		// pass the rotation inputs
		AddControllerYawInput(Yaw);
		AddControllerPitchInput(Pitch);
	}
}

void AProjectBopisCharacter::DoMove(float Right, float Forward)
{
	if (GetController())
	{
		// pass the move inputs
		AddMovementInput(GetActorRightVector(), Right);
		AddMovementInput(GetActorForwardVector(), Forward);
	}
}

void AProjectBopisCharacter::DoJumpStart()
{
	// pass Jump to the character
	Jump();
}

void AProjectBopisCharacter::DoJumpEnd()
{
	// pass StopJumping to the character
	StopJumping();
}

void AProjectBopisCharacter::DoFire()
{
	if (WeaponHolder)
	{
		// Only animate if the shot actually happened — a rate-capped click must not replay the montage.
		const bool bDidFire = WeaponHolder->FireEquippedWeapon();

		if (bDidFire)
		{
			if (AWeaponBase* EquippedWeapon = WeaponHolder->GetEquippedWeapon())
			{
				if (EquippedWeapon->UsesAnimationDrivenFeedback() && FireMontage)
				{
					if (UAnimInstance* AnimInstance = FirstPersonMesh->GetAnimInstance())
					{
						AnimInstance->Montage_Play(FireMontage);
					}
				}
			}
		}
	}
}

void AProjectBopisCharacter::DoFireHeld()
{
	if (!WeaponHolder)
	{
		return;
	}

	AWeaponBase* EquippedWeapon = WeaponHolder->GetEquippedWeapon();
	if (!EquippedWeapon || EquippedWeapon->GetFireMode() != EWeaponFireMode::Auto)
	{
		return;
	}

	// The weapon's own fire-rate cap paces this; Triggered fires every frame the trigger is held.
	DoFire();
}

void AProjectBopisCharacter::DoAimStart()
{
	bIsAiming = true;

	if (WeaponHolder)
	{
		if (AWeaponBase* EquippedWeapon = WeaponHolder->GetEquippedWeapon())
		{
			if (EquippedWeapon->HasZoom())
			{
				FirstPersonCameraComponent->SetFieldOfView(EquippedWeapon->GetZoomedFOV());
			}
		}
	}
}

void AProjectBopisCharacter::DoAimEnd()
{
	bIsAiming = false;
	FirstPersonCameraComponent->SetFieldOfView(DefaultFOV);
}
