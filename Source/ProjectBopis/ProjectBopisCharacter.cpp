// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProjectBopisCharacter.h"
#include "Gameplay/FocusComponent.h"
#include "Components/PostProcessComponent.h"
#include "Weapons/WeaponHolderComponent.h"
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
	// Capsule, weapon holder and tick come from ABopisCharacterBase.
	Focus =CreateDefaultSubobject<UFocusComponent>(TEXT("Focus"));

	FocusPostProcess = CreateDefaultSubobject<UPostProcessComponent>(TEXT("FocusPostProcess"));
	FocusPostProcess->SetupAttachment(RootComponent);
	FocusPostProcess->bUnbound = true;
	FocusPostProcess->BlendWeight = 0.0f;

	// Default look — tweak on the Blueprint.
	FPostProcessSettings& Look = FocusPostProcess->Settings;
	Look.bOverride_ColorSaturation = true;
	Look.ColorSaturation = FVector4(0.5f, 0.5f, 0.5f, 1.0f);
	Look.bOverride_VignetteIntensity = true;
	Look.VignetteIntensity = 0.8f;
	Look.bOverride_SceneFringeIntensity = true;
	Look.SceneFringeIntensity = 1.5f;

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

	// Configure character movement
	GetCharacterMovement()->BrakingDecelerationFalling = 1500.0f;
	GetCharacterMovement()->AirControl = 0.5f;
	GetCharacterMovement()->MaxWalkSpeedCrouched = CrouchedSpeed;
}

void AProjectBopisCharacter::BeginPlay()
{
	Super::BeginPlay();

	DefaultFOV = FollowCamera->FieldOfView;

	BoomBaseHeight = CameraBoom->GetRelativeLocation().Z;
	DefaultCapsuleHalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

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

		// Weapon slots — each key passes its own slot number along with the event.
		for (int32 Index = 0; Index < WeaponSlotActions.Num(); ++Index)
		{
			if (WeaponSlotActions[Index])
			{
				EnhancedInputComponent->BindAction(WeaponSlotActions[Index], ETriggerEvent::Started, this,
					&AProjectBopisCharacter::DoSelectWeaponSlot, Index + 1);
			}
		}

		// Bullet time
		EnhancedInputComponent->BindAction(FocusAction, ETriggerEvent::Started, this,
			&AProjectBopisCharacter::DoToggleFocus);

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
	// The base counts down the lowering timer and drives the reload montage.
	Super::Tick(DeltaSeconds);

	UpdateCrouch();
	UpdateMovementStance();
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
	if (bIsAiming && GetWeaponHolder())
	{
		if (const AWeaponBase* EquippedWeapon = GetWeaponHolder()->GetEquippedWeapon())
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

	// Eased part: the optional crouch offset, moving at the same speed as the hip/aim move.
	const float TargetCrouchOffset = bIsCrouched ? CrouchCameraOffset : 0.0f;
	CurrentCrouchCameraOffset = FMath::FInterpTo(
		CurrentCrouchCameraOffset, TargetCrouchOffset, DeltaSeconds, CameraTransitionSpeed);

	// Instant part: crouching shrinks the capsule and lowers its centre by the lost
	// half-height in a single frame, and the boom rides on the capsule — so lift it by
	// the same amount, also in a single frame, or the camera dips and floats back.
	// Derived from the capsule's actual size rather than from crouch callbacks, whose
	// reported adjustments don't always pair up (accumulating them drifted the camera).
	const float CapsuleDrop = DefaultCapsuleHalfHeight - GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

	FVector BoomLocation = CameraBoom->GetRelativeLocation();
	BoomLocation.Z = BoomBaseHeight + CapsuleDrop + CurrentCrouchCameraOffset;
	CameraBoom->SetRelativeLocation(BoomLocation);
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
		break;

	case EMovementStance::Aiming:
		// Yaw locked to camera, so movement reads as strafing.
		bUseControllerRotationYaw = true;
		Movement->bOrientRotationToMovement = false;
		break;

	case EMovementStance::AnimationDriven:
		// Both off: the montage owns rotation. Reachable once the shootdodge lands.
		bUseControllerRotationYaw = false;
		Movement->bOrientRotationToMovement = false;
		break;
	}
}

void AProjectBopisCharacter::UpdateMovementStance()
{
	// Animation-owned rotation is entered and left explicitly; aiming or firing must
	// not pull the character out of a shootdodge mid-dive.
	if (CurrentStance == EMovementStance::AnimationDriven)
	{
		return;
	}

	const EMovementStance DesiredStance = IsWeaponRaised()
		? EMovementStance::Aiming
		: EMovementStance::FreeRun;

	if (DesiredStance != CurrentStance)
	{
		ApplyMovementStance(DesiredStance);
	}

	// Speed follows the aim button, not the stance — hip-fire strafes at full
	// free-run speed. Per frame, since aiming can start while already strafing.
	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->MaxWalkSpeed = bIsAiming ? AimingSpeed : FreeRunSpeed;
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
	UWeaponHolderComponent* Holder = GetWeaponHolder();
	if (!Holder)
	{
		return;
	}

	// Mid-equip the gun isn't up yet; the trigger waits for the animation.
	if (IsEquipAnimating())
	{
		return;
	}

	// A trigger pull from the lowered stance turns the character to the camera
	// before the shot leaves, so it never fires sideways out of a free-run pose.
	// Snapped rather than interpolated: the shot is this frame.
	if (Holder->GetEquippedWeapon())
	{
		if (!IsWeaponRaised())
		{
			SetActorRotation(FRotator(0.0f, GetControlRotation().Yaw, 0.0f));
		}

		TimeUntilWeaponLowered = LowerWeaponDelay;
		UpdateMovementStance();
	}

	// Only a real shot animates. RateLimited and Reloading must stay silent, and
	// Empty is handled by the weapon's own dry-fire sound.
	const EFireResult FireResult = Holder->FireEquippedWeapon();

	AWeaponBase* EquippedWeapon = Holder->GetEquippedWeapon();
	if (!EquippedWeapon)
	{
		return;
	}

	if (FireResult == EFireResult::Fired)
	{
		PlayFireAnimation(EquippedWeapon);
	}
	else if (FireResult == EFireResult::Empty && EquippedWeapon->ShouldAutoReloadWhenEmpty())
	{
		// Handled here rather than inside the weapon, so the montage and the state
		// change stay together — the weapon has no business knowing about montages.
		DoReload();
	}
}

void AProjectBopisCharacter::DoToggleFocus()
{
	if (Focus)
	{
		Focus->Toggle();
	}
}

void AProjectBopisCharacter::DoSelectWeaponSlot(int32 Slot)
{
	if (UWeaponHolderComponent* Holder = GetWeaponHolder())
	{
		Holder->SelectSlot(Slot);
	}
}

void AProjectBopisCharacter::DoReload()
{
	// The montage only plays if a reload actually started, so mashing the key on a
	// full magazine does nothing rather than replaying the animation.
	UWeaponHolderComponent* Holder = GetWeaponHolder();
	if (!Holder || !Holder->ReloadEquippedWeapon())
	{
		return;
	}

	PlayReloadAnimation(Holder->GetEquippedWeapon());
}

void AProjectBopisCharacter::DoCrouchStart()
{
	// Only records the request — UpdateCrouch decides whether the character is
	// actually down, since crouch only applies while standing still.
	bCrouchRequested = bCrouchIsToggle ? !bCrouchRequested : true;
}

void AProjectBopisCharacter::DoCrouchEnd()
{
	// In toggle mode the release carries no meaning; the press already did the work.
	if (!bCrouchIsToggle)
	{
		bCrouchRequested = false;
	}
}

void AProjectBopisCharacter::UpdateCrouch()
{
	const UCharacterMovementComponent* Movement = GetCharacterMovement();
	if (!Movement)
	{
		return;
	}

	// Acceleration comes from input, not velocity: releasing the stick crouches
	// immediately rather than waiting for braking to finish, and any input stands
	// the character up on the same frame.
	const bool bWantsToMove = !Movement->GetCurrentAcceleration().IsNearlyZero();

	if (bWantsToMove && bMovementCancelsCrouch)
	{
		bCrouchRequested = false;
	}

	const bool bShouldCrouch = bCrouchRequested && !bWantsToMove && Movement->IsMovingOnGround();

	if (bShouldCrouch && !bIsCrouched)
	{
		Crouch();
	}
	else if (!bShouldCrouch && bIsCrouched)
	{
		// Fails quietly under a low ceiling; the movement component keeps retrying.
		UnCrouch();
	}
}

void AProjectBopisCharacter::DoFireHeld()
{
	UWeaponHolderComponent* Holder = GetWeaponHolder();
	if (!Holder)
	{
		return;
	}

	AWeaponBase* EquippedWeapon = Holder->GetEquippedWeapon();
	if (!EquippedWeapon || EquippedWeapon->GetFireMode() != EWeaponFireMode::Auto)
	{
		return;
	}

	// The weapon's own fire-rate cap paces this; Triggered fires every frame the trigger is held.
	DoFire();
}

void AProjectBopisCharacter::DoAimStart()
{
	// State only — Tick derives the stance and camera from this every frame.
	bIsAiming = true;
}

void AProjectBopisCharacter::DoAimEnd()
{
	bIsAiming = false;
}
