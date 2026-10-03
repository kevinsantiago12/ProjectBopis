// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Animation/AnimInstance.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "InputActionValue.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "ProjectBopis.h"
#include "Blueprint/UserWidget.h"
#include "UI/PlayerHUDWidget.h"
#include "Weapons/WeaponBase.h"

AProjectBopisCharacter::AProjectBopisCharacter()
{
	// The camera transition is driven per-frame from aim state, so tick is load-bearing.
	PrimaryActorTick.bCanEverTick = true;

	// Set size for collision capsule
	GetCapsuleComponent()->InitCapsuleSize(55.f, 96.0f);

	WeaponHolder = CreateDefaultSubobject<UWeaponHolderComponent>(TEXT("WeaponHolder"));

	// Rotation model, set explicitly rather than inherited — Step 2 of the third-person
	// conversion toggles this pair at runtime. For now the character faces control
	// rotation, which keeps actor-forward and camera-forward identical so the existing
	// DoMove stays correct.
	bUseControllerRotationYaw = true;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;
	GetCharacterMovement()->bOrientRotationToMovement = false;

	// The boom owns the control rotation; the camera just rides its far end. Setting
	// bUsePawnControlRotation on both would apply the rotation twice.
	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("Camera Boom"));
	CameraBoom->SetupAttachment(GetCapsuleComponent());
	CameraBoom->SetRelativeLocation(FVector(0.0f, 0.0f, 70.0f));
	CameraBoom->TargetArmLength = 300.0f;
	CameraBoom->SocketOffset = FVector(0.0f, 50.0f, 0.0f);
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bDoCollisionTest = true;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("Follow Camera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	// The body is now the only mesh, and everyone sees it.
	GetMesh()->SetOwnerNoSee(false);

	GetCapsuleComponent()->SetCapsuleSize(34.0f, 96.0f);

	// Configure character movement
	GetCharacterMovement()->BrakingDecelerationFalling = 1500.0f;
	GetCharacterMovement()->AirControl = 0.5f;

	// Crouch does nothing at all without this, and fails silently — CanCrouch()
	// just returns false with no warning. It is false by default.
	GetCharacterMovement()->NavAgentProps.bCanCrouch = true;
	GetCharacterMovement()->MaxWalkSpeedCrouched = CrouchedSpeed;
}

void AProjectBopisCharacter::BeginPlay()
{
	Super::BeginPlay();

	DefaultFOV = FollowCamera->FieldOfView;

	// Explicit rather than relying on constructor defaults, so the runtime path
	// is exercised from frame one instead of only after the first aim.
	ApplyMovementStance(EMovementStance::FreeRun);

	if (IsLocallyControlled() && HUDWidgetClass)
	{
		if (UPlayerHUDWidget* HUDWidget = CreateWidget<UPlayerHUDWidget>(GetWorld(), HUDWidgetClass))
		{
			HUDWidget->AddToViewport();
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

		// Reloading
		EnhancedInputComponent->BindAction(ReloadAction, ETriggerEvent::Started, this,
			&AProjectBopisCharacter::DoReload);

		// Crouching — both edges bound; bCrouchIsToggle decides what they mean.
		EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Started, this,
			&AProjectBopisCharacter::DoCrouchStart);

		EnhancedInputComponent->BindAction(CrouchAction, ETriggerEvent::Completed, this,
			&AProjectBopisCharacter::DoCrouchEnd);

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
	if (!GetController())
	{
		return;
	}

	// Camera-relative in BOTH stances — this is the whole camera-relative model.
	// Only pitch and roll are discarded; yaw defines the movement frame. The
	// stance decides whether the character rotates to face the result, not
	// which direction the input means.
	const FRotator YawRotation(0.0f, GetControlRotation().Yaw, 0.0f);
	const FRotationMatrix RotationMatrix(YawRotation);

	AddMovementInput(RotationMatrix.GetUnitAxis(EAxis::Y), Right);
	AddMovementInput(RotationMatrix.GetUnitAxis(EAxis::X), Forward);
}

void AProjectBopisCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	UpdateCameraTransition(DeltaSeconds);
}

void AProjectBopisCharacter::UpdateCameraTransition(float DeltaSeconds)
{
	if (!CameraBoom || !FollowCamera)
	{
		return;
	}

	// Derived from state every frame rather than pushed on aim start/end. A weapon
	// swap mid-aim can't strand the camera, because there's nothing to strand.
	const float TargetArmLength = bIsAiming ? AimArmLength : HipArmLength;
	const FVector TargetSocketOffset = bIsAiming ? AimSocketOffset : HipSocketOffset;

	float TargetFOV = DefaultFOV;
	if (bIsAiming && WeaponHolder)
	{
		if (const AWeaponBase* EquippedWeapon = WeaponHolder->GetEquippedWeapon())
		{
			// Magnification stays weapon-specific; the stance and shoulder-in don't.
			if (EquippedWeapon->HasZoom())
			{
				TargetFOV = EquippedWeapon->GetZoomedFOV();
			}
		}
	}

	CameraBoom->TargetArmLength = FMath::FInterpTo(
		CameraBoom->TargetArmLength, TargetArmLength, DeltaSeconds, CameraTransitionSpeed);

	CameraBoom->SocketOffset = FMath::VInterpTo(
		CameraBoom->SocketOffset, TargetSocketOffset, DeltaSeconds, CameraTransitionSpeed);

	FollowCamera->SetFieldOfView(FMath::FInterpTo(
		FollowCamera->FieldOfView, TargetFOV, DeltaSeconds, CameraTransitionSpeed));
}

void AProjectBopisCharacter::ApplyMovementStance(EMovementStance NewStance)
{
	CurrentStance = NewStance;

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	if (!Movement)
	{
		return;
	}

	switch (NewStance)
	{
	case EMovementStance::FreeRun:
		// Character turns to face where it's going; camera looks around freely.
		bUseControllerRotationYaw = false;
		Movement->bOrientRotationToMovement = true;
		Movement->RotationRate = FRotator(0.0f, FreeRunRotationRate, 0.0f);
		Movement->MaxWalkSpeed = FreeRunSpeed;
		break;

	case EMovementStance::Aiming:
		// Yaw locked to camera, so movement reads as strafing.
		bUseControllerRotationYaw = true;
		Movement->bOrientRotationToMovement = false;
		Movement->MaxWalkSpeed = AimingSpeed;
		break;

	case EMovementStance::AnimationDriven:
		// Both off: the montage owns rotation. Reachable once the shootdodge lands.
		bUseControllerRotationYaw = false;
		Movement->bOrientRotationToMovement = false;
		break;
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
	if (!WeaponHolder)
	{
		return;
	}

	// Only a real shot animates. RateLimited and Reloading must stay silent, and
	// Empty is handled by the weapon's own dry-fire sound.
	const EFireResult FireResult = WeaponHolder->FireEquippedWeapon();

	AWeaponBase* EquippedWeapon = WeaponHolder->GetEquippedWeapon();
	if (!EquippedWeapon)
	{
		return;
	}

	if (FireResult == EFireResult::Fired)
	{
		// Deliberately not gated on UsesAnimationDrivenFeedback() — that flag says
		// where the *weapon's* sound and muzzle flash come from. The arms animation
		// is the character animating itself, and plays either way. Looked up by the
		// weapon's anim type, so each weapon gets its own without owning the asset.
		TObjectPtr<UAnimMontage>* FoundMontage = FireMontages.Find(EquippedWeapon->GetAnimType());

		if (FoundMontage && *FoundMontage)
		{
			if (UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance())
			{
				AnimInstance->Montage_Play(*FoundMontage);
			}
		}
	}
	else if (FireResult == EFireResult::Empty && EquippedWeapon->ShouldAutoReloadWhenEmpty())
	{
		// Handled here rather than inside the weapon, so the montage and the state
		// change stay together — the weapon has no business knowing about montages.
		DoReload();
	}
}

void AProjectBopisCharacter::DoReload()
{
	// The montage only plays if a reload actually started, so mashing the key on a
	// full magazine does nothing rather than replaying the animation.
	if (!WeaponHolder || !WeaponHolder->ReloadEquippedWeapon())
	{
		return;
	}

	AWeaponBase* EquippedWeapon = WeaponHolder->GetEquippedWeapon();
	if (!EquippedWeapon)
	{
		return;
	}

	TObjectPtr<UAnimMontage>* FoundMontage = ReloadMontages.Find(EquippedWeapon->GetAnimType());

	if (FoundMontage && *FoundMontage)
	{
		if (UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance())
		{
			AnimInstance->Montage_Play(*FoundMontage);
		}
	}
}

void AProjectBopisCharacter::DoCrouchStart()
{
	// Crouch is orthogonal to the aim/free-run pair — all four combinations are
	// legal, so stance is deliberately left alone here. The movement component
	// owns height and crouched speed; ApplyMovementStance owns rotation.
	if (bCrouchIsToggle)
	{
		if (bIsCrouched)
		{
			UnCrouch();
		}
		else
		{
			Crouch();
		}
	}
	else
	{
		Crouch();
	}
}

void AProjectBopisCharacter::DoCrouchEnd()
{
	// In toggle mode the release carries no meaning; the press already did the work.
	if (!bCrouchIsToggle)
	{
		UnCrouch();
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
	// State only — UpdateCameraTransition derives the camera from this every frame.
	bIsAiming = true;

	ApplyMovementStance(EMovementStance::Aiming);
}

void AProjectBopisCharacter::DoAimEnd()
{
	bIsAiming = false;

	ApplyMovementStance(EMovementStance::FreeRun);
}
