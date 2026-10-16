// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProjectBopisCharacter.h"
#include "Gameplay/FocusComponent.h"
#include "Gameplay/ShootdodgeComponent.h"
#include "Gameplay/RollComponent.h"
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
#include "Gameplay/HealthComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "EnhancedInputSubsystems.h"
#include "EnhancedPlayerInput.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"

AProjectBopisCharacter::AProjectBopisCharacter()
{
	// Capsule, weapon holder and tick come from ABopisCharacterBase.
	Focus =CreateDefaultSubobject<UFocusComponent>(TEXT("Focus"));
	Shootdodge = CreateDefaultSubobject<UShootdodgeComponent>(TEXT("Shootdodge"));
	Roll = CreateDefaultSubobject<URollComponent>(TEXT("Roll"));

	// The player never staggers: being rooted mid-fight (or mid-dive) is no fun. Hits stay
	// light reactions.
	StaggerDuration = 0.0f;

	// Enemies' hits can land on the head (rarely — see AEnemyBase::HitBoneWeights), but the
	// player takes it at normal damage: a stray round shouldn't be an instant death.
	BoneDamageMultipliers.Remove(TEXT("head"));

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

	CampAnchor = GetActorLocation();

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

		EnhancedInputComponent->BindAction(ShootdodgeAction, ETriggerEvent::Started, this,
			&AProjectBopisCharacter::DoShootdodge);

		EnhancedInputComponent->BindAction(RollAction, ETriggerEvent::Started, this,
			&AProjectBopisCharacter::DoRoll);

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

	// Mid-dive the dive owns movement; lying prone, any movement means "get up".
	if (Shootdodge && Shootdodge->IsDodging())
	{
		Shootdodge->NotifyMoveInput();
		return;
	}

	// Knelt after a roll: the slide carries on, input doesn't steer it.
	if (bPostRollCrouchHoldsPosition && bPostRollCrouching)
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

	// Faded markers go, in real time: Focus doesn't make them linger.
	const float RealNow = GetWorld()->GetRealTimeSeconds();
	HitIndicators.RemoveAll([RealNow](const FHitIndicator& Marker) { return RealNow - Marker.StartTime >= Marker.Duration; });

	// Dead: no stances, crouch or framing any more — just keep the body in view.
	if (IsDead())
	{
		// Counted in real seconds: FApp's delta is the frame's, before any time dilation.
		TimeSinceDeath += FApp::GetDeltaTime();
		if (bDeathSlowMo && TimeSinceDeath >= DeathSlowMoDuration)
		{
			bDeathSlowMo = false;
			Focus->EndFreeFocus();
		}
		if (TimeSinceDeath >= DeathRestartDelay)
		{
			RestartLevel();
			return;
		}

		FollowBodyWithCamera(DeltaSeconds);
		return;
	}

	UpdateCampingHeat(DeltaSeconds);
	if (IsEvadingNow())
	{
		LastEvadingTime = GetWorld()->GetTimeSeconds();
	}
	UpdateAutoReload(DeltaSeconds);
	UpdateCrouch();

	// Crouched in the combat stance, the gun comes up and stays up: facing the camera, ready
	// to fire, without the aim's zoom. On standing it lowers after the usual delay.
	if (bCrouchCombatStance && bIsCrouched && !IsDead())
	{
		TimeUntilWeaponLowered = FMath::Max(TimeUntilWeaponLowered, LowerWeaponDelay);
	}

	UpdateMovementStance();
	UpdateAimTurn(DeltaSeconds);
	UpdateCameraTransition(DeltaSeconds);
}

void AProjectBopisCharacter::AddHitIndicator(const FVector& Source, bool bHit)
{
	if (IsDead() || !(bHit ? bShowHitIndicators : bShowNearMissIndicators))
	{
		return;
	}
	const FVector ToSource = (Source - GetActorLocation()).GetSafeNormal2D();
	if (ToSource.IsNearlyZero())
	{
		return;
	}

	// A near miss from a shooter on screen says nothing new: you can see him.
	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (!bHit && bNearMissOnlyOffScreen && PlayerController && PlayerController->PlayerCameraManager)
	{
		const APlayerCameraManager* Camera = PlayerController->PlayerCameraManager;
		const FVector View = Camera->GetCameraRotation().Vector().GetSafeNormal2D();
		if (FVector::DotProduct(View, ToSource) > FMath::Cos(FMath::DegreesToRadians(Camera->GetFOVAngle() * 0.5f)))
		{
			return;
		}
	}

	// The direction's sector: one marker of each kind per sector.
	const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(ToSource.Y, ToSource.X)) + 180.0f;
	const int32 Sector = FMath::Clamp(FMath::FloorToInt(Yaw / (360.0f / HitIndicatorSectors)), 0, HitIndicatorSectors - 1);
	const float Now = GetWorld()->GetRealTimeSeconds();

	if (bHit)
	{
		// A hit supersedes the grey marker there.
		HitIndicators.RemoveAll([Sector](const FHitIndicator& Marker) { return !Marker.bHit && Marker.Sector == Sector; });
	}
	else
	{
		// Near misses stay quiet: not where a hit shows, not too often, not too many.
		int32 NearMisses = 0;
		for (const FHitIndicator& Marker : HitIndicators)
		{
			if (Marker.Sector == Sector && (Marker.bHit || Now - Marker.StartTime < NearMissIndicatorCooldown))
			{
				return;
			}
			NearMisses += Marker.bHit ? 0 : 1;
		}
		const bool bSectorShown = HitIndicators.ContainsByPredicate(
			[Sector](const FHitIndicator& Marker) { return !Marker.bHit && Marker.Sector == Sector; });
		if (!bSectorShown && NearMisses >= MaxNearMissIndicators)
		{
			return;
		}
	}

	// Refresh the sector's marker, or start one.
	FHitIndicator* Marker = HitIndicators.FindByPredicate(
		[Sector, bHit](const FHitIndicator& Existing) { return Existing.bHit == bHit && Existing.Sector == Sector; });
	if (!Marker)
	{
		Marker = &HitIndicators.AddDefaulted_GetRef();
		Marker->Sector = Sector;
		Marker->bHit = bHit;
	}
	Marker->Source = Source;
	Marker->StartTime = Now;
	Marker->Duration = bHit ? HitIndicatorDuration : NearMissIndicatorDuration;
}

void AProjectBopisCharacter::UpdateAimTurn(float DeltaSeconds)
{
	if (!bTurningToAim)
	{
		return;
	}

	// Turning at a fixed rate the short way round; once there, the camera takes over.
	const float TargetYaw = GetControlRotation().Yaw;
	const float NewYaw = FMath::FixedTurn(GetActorRotation().Yaw, TargetYaw, AimTurnRate * DeltaSeconds);
	SetActorRotation(FRotator(0.0f, NewYaw, 0.0f));
	if (FMath::Abs(FRotator::NormalizeAxis(TargetYaw - NewYaw)) < 0.5f)
	{
		bTurningToAim = false;
		bUseControllerRotationYaw = true;
	}
}

void AProjectBopisCharacter::UpdateCameraTransition(float DeltaSeconds)
{
	if (!CameraBoom || !FollowCamera)
	{
		return;
	}

	// Diving, landing and lying prone get their own framing; getting up eases back to normal.
	const EShootdodgePhase DodgePhase = Shootdodge ? Shootdodge->GetPhase() : EShootdodgePhase::None;
	const bool bDodgeCamera = DodgePhase != EShootdodgePhase::None && DodgePhase != EShootdodgePhase::GettingUp
		&& DodgePhase != EShootdodgePhase::WindUp;

	// Derived from state every frame rather than pushed on aim start/end. A weapon
	// swap mid-aim can't strand the camera, because there's nothing to strand.
	const float TargetArmLength = bDodgeCamera ? ShootdodgeArmLength : (bIsAiming ? AimArmLength : HipArmLength);
	const FVector TargetSocketOffset = bDodgeCamera ? ShootdodgeSocketOffset : (bIsAiming ? AimSocketOffset : HipSocketOffset);

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
	const float TargetCrouchOffset = (bCrouchCombatStance && bIsCrouched) ? CrouchCameraOffset : 0.0f;
	CurrentCrouchCameraOffset = FMath::FInterpTo(
		CurrentCrouchCameraOffset, TargetCrouchOffset, DeltaSeconds, CameraTransitionSpeed);

	CurrentShootdodgeCameraHeight = FMath::FInterpTo(CurrentShootdodgeCameraHeight,
		bDodgeCamera ? ShootdodgeCameraHeight : 0.0f, DeltaSeconds, CameraTransitionSpeed);

	// Instant part: crouching shrinks the capsule and lowers its centre by the lost
	// half-height in a single frame, and the boom rides on the capsule — so lift it by
	// the same amount, also in a single frame, or the camera dips and floats back.
	// Derived from the capsule's actual size rather than from crouch callbacks, whose
	// reported adjustments don't always pair up (accumulating them drifted the camera).
	const float CapsuleDrop = DefaultCapsuleHalfHeight - GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

	FVector BoomLocation = CameraBoom->GetRelativeLocation();
	BoomLocation.Z = BoomBaseHeight + CapsuleDrop + CurrentCrouchCameraOffset + CurrentShootdodgeCameraHeight;
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
		bTurningToAim = false;
		bUseControllerRotationYaw = false;
		Movement->bOrientRotationToMovement = true;
		Movement->RotationRate = FRotator(0.0f, FreeRunRotationRate, 0.0f);
		break;

	case EMovementStance::Aiming:
		// Yaw locked to camera, so movement reads as strafing — after a quick turn to it
		// (UpdateAimTurn) if the body was facing elsewhere.
		Movement->bOrientRotationToMovement = false;
		bTurningToAim = AimTurnRate > 0.0f
			&& FMath::Abs(FRotator::NormalizeAxis(GetControlRotation().Yaw - GetActorRotation().Yaw)) > 1.0f;
		bUseControllerRotationYaw = !bTurningToAim;
		break;

	case EMovementStance::AnimationDriven:
		// Both off: the montage owns rotation. Reachable once the shootdodge lands.
		bTurningToAim = false;
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
	// Winding up for a dive is a commitment: no hopping out of it. Nor out of a roll.
	if ((Shootdodge && Shootdodge->IsWindingUp()) || (Roll && Roll->IsRolling()))
	{
		return;
	}

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

	// Getting up from a dive leaves you open: the gun stays quiet until you're on your feet.
	// Same while winding up for one — the shooting starts with the leap — and mid-roll.
	if ((Shootdodge && (Shootdodge->IsGettingUp() || Shootdodge->IsWindingUp())) || (Roll && Roll->IsRolling()))
	{
		return;
	}

	// A trigger pull from the lowered stance turns the character to the camera (quickly,
	// see AimTurnRate) so it never stays sideways in a free-run pose.
	if (Holder->GetEquippedWeapon())
	{
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

void AProjectBopisCharacter::DoShootdodge()
{
	if (Roll && Roll->IsRolling())
	{
		return;
	}
	if (Shootdodge)
	{
		Shootdodge->TryStart();
	}
}

void AProjectBopisCharacter::DoRoll()
{
	if (!Roll)
	{
		return;
	}
	// A roll is the way out of a kneel (or a crouch): up first, then roll.
	bPostRollCrouching = false;
	bCrouchRequested = false;
	if (bIsCrouched)
	{
		UnCrouch();
	}
	Roll->TryRoll();
}

void AProjectBopisCharacter::StartPostRollCrouch()
{
	if (bPostRollCrouch && !IsDead())
	{
		bPostRollCrouching = true;

		// Down now, not on the next UpdateCrouch: the roll is already blending out, and it
		// has to blend into the crouch, not into a standing pose first.
		if (!bIsCrouched)
		{
			Crouch();
		}
	}
}

bool AProjectBopisCharacter::IsInputHeld(const UInputAction* Action) const
{
	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	const UEnhancedInputLocalPlayerSubsystem* Subsystem = PlayerController
		? ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PlayerController->GetLocalPlayer())
		: nullptr;
	const UEnhancedPlayerInput* PlayerInput = Subsystem ? Subsystem->GetPlayerInput() : nullptr;
	return PlayerInput && Action && PlayerInput->GetActionValue(Action).Get<bool>();
}

float AProjectBopisCharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
	AController* EventInstigator, AActor* DamageCauser)
{
	const float Result = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);

	// Starts the grace in which enemies can't roll another hit.
	if (Result > 0.0f)
	{
		LastHitTakenTime = GetWorld()->GetTimeSeconds();

		// Red marker toward whoever fired it (the shooter's body, else the round itself).
		const APawn* Shooter = EventInstigator ? EventInstigator->GetPawn() : nullptr;
		if (Shooter || DamageCauser)
		{
			AddHitIndicator(Shooter ? Shooter->GetActorLocation() : DamageCauser->GetActorLocation(), true);
		}
	}

	// The killing blow ragdolled a diving body (in Super): it keeps flying the way it was going.
	if (IsDead() && !DiveDeathVelocity.IsZero())
	{
		GetMesh()->SetAllPhysicsLinearVelocity(DiveDeathVelocity, true);
		DiveDeathVelocity = FVector::ZeroVector;
	}

	return Result;
}

void AProjectBopisCharacter::Die(AController* Killer, const FVector& ShotDirection)
{
	// Read before Super stops the movement: the dive's state and its speed.
	bDiedMidDive = Shootdodge && Shootdodge->IsBodyDown();
	DiveDeathVelocity = bDiedMidDive ? GetVelocity() : FVector::ZeroVector;
	if (Shootdodge)
	{
		Shootdodge->CancelForDeath();
	}
	if (Roll)
	{
		Roll->Cancel();
	}
	if (Focus)
	{
		// Whatever slow motion was running gives way to the death's own.
		Focus->StopFocus();
		if (DeathSlowMoDuration > 0.0f && Focus->BeginFreeFocus())
		{
			UGameplayStatics::SetGlobalTimeDilation(this, DeathTimeDilation);
			bDeathSlowMo = true;
		}
	}
	bIsAiming = false;

	Super::Die(Killer, ShotDirection);

	// Look still orbits the camera; nothing else answers, and the body no longer turns with it.
	bUseControllerRotationYaw = false;
	if (UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(InputComponent))
	{
		EnhancedInputComponent->ClearActionEventBindings();
		EnhancedInputComponent->BindAction(LookAction, ETriggerEvent::Triggered, this, &AProjectBopisCharacter::LookInput);
		EnhancedInputComponent->BindAction(MouseLookAction, ETriggerEvent::Triggered, this, &AProjectBopisCharacter::LookInput);
	}

	TimeSinceDeath = 0.0f;
}

bool AProjectBopisCharacter::PlayDeathAnimation(const FVector& ShotDirection)
{
	return !bDiedMidDive && Super::PlayDeathAnimation(ShotDirection);
}

void AProjectBopisCharacter::UpdateCampingHeat(float DeltaSeconds)
{
	// Moved on from the spot: a new spot starts here, and the time there starts again.
	if (FVector::Dist2D(GetActorLocation(), CampAnchor) > CampRadius)
	{
		CampAnchor = GetActorLocation();
		TimeAtCampAnchor = 0.0f;
	}
	// Evading (a dive or roll, and its linger after): the clock at this spot waits. After
	// that it runs as normal — knelt, crouched or standing.
	if (!IsEvading())
	{
		TimeAtCampAnchor += DeltaSeconds;
	}

	// Heat follows how long they've been here, past the grace; it climbs at that pace and
	// drains at its own once they've gone.
	const float TargetHeat = FMath::Clamp((TimeAtCampAnchor - CampGraceTime) / CampTimeToFullHeat, 0.0f, 1.0f);
	CampingHeat = TargetHeat >= CampingHeat
		? TargetHeat
		: FMath::Max(TargetHeat, CampingHeat - CampHeatDrainPerSecond * DeltaSeconds);
}

bool AProjectBopisCharacter::IsInHitGrace() const
{
	return GetWorld()->GetTimeSeconds() - LastHitTakenTime < HitGraceTime;
}

bool AProjectBopisCharacter::IsEvading() const
{
	// Under way now, or only just over: the effect lingers a while after landing or rolling.
	return IsEvadingNow() || GetWorld()->GetTimeSeconds() - LastEvadingTime < EvadeLingerTime;
}

bool AProjectBopisCharacter::IsEvadingNow() const
{
	// The dive's flight, or a dodge roll.
	return (Shootdodge && Shootdodge->IsAirborne()) || (Roll && Roll->IsRolling());
}

void AProjectBopisCharacter::FollowBodyWithCamera(float DeltaSeconds)
{
	if (!CameraBoom || !GetMesh()->DoesSocketExist(TEXT("pelvis")))
	{
		return;
	}
	const FVector Target = GetMesh()->GetSocketLocation(TEXT("pelvis"));
	CameraBoom->SetWorldLocation(FMath::VInterpTo(CameraBoom->GetComponentLocation(), Target, DeltaSeconds, DeathCameraFollowSpeed));
}

void AProjectBopisCharacter::RestartLevel()
{
	UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)));
}

void AProjectBopisCharacter::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);

	if (Shootdodge)
	{
		Shootdodge->NotifyLanded();
	}
}

void AProjectBopisCharacter::SetAnimationDrivenRotation(bool bAnimationDriven)
{
	ApplyMovementStance(bAnimationDriven ? EMovementStance::AnimationDriven : EMovementStance::FreeRun);
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
	// The dive is animated for the gun in hand; no swapping while winding up for it, or rolling.
	if ((Shootdodge && Shootdodge->IsWindingUp()) || (Roll && Roll->IsRolling()))
	{
		return;
	}

	if (UWeaponHolderComponent* Holder = GetWeaponHolder())
	{
		Holder->SelectSlot(Slot);
	}
}

void AProjectBopisCharacter::DoReload()
{
	if (Roll && Roll->IsRolling())
	{
		return;
	}

	// Lying prone after a dive, it reloads on the floor; the rest of a dive (wind-up, flight,
	// landing, getting up) has no time for it.
	if (Shootdodge && Shootdodge->IsDodging() && !Shootdodge->IsProne())
	{
		return;
	}

	// The montage only plays if a reload actually started, so mashing the key on a
	// full magazine does nothing rather than replaying the animation.
	UWeaponHolderComponent* Holder = GetWeaponHolder();
	if (!Holder || !Holder->ReloadEquippedWeapon())
	{
		return;
	}

	PlayReloadAnimation(Holder->GetEquippedWeapon());

	// Reloading breaks the moment: slow motion ends.
	if (bStopFocusOnReload && Focus && Focus->IsFocusActive())
	{
		Focus->StopFocus();
	}
}

void AProjectBopisCharacter::UpdateAutoReload(float DeltaSeconds)
{
	// An empty gun reloads itself once the player is free to — standing or lying prone, not
	// mid-dive or mid-roll — after a beat, so the last shot reads.
	const UWeaponHolderComponent* Holder = GetWeaponHolder();
	const AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr;
	const bool bInDive = Shootdodge && Shootdodge->IsDodging() && !Shootdodge->IsProne();
	const bool bFreeToReload = !bInDive && !(Roll && Roll->IsRolling()) && !IsEquipAnimating();
	if (!bAutoReload || !Weapon || !bFreeToReload || Weapon->GetAmmoInMagazine() > 0 || !Weapon->CanReload())
	{
		EmptyGunTime = 0.0f;
		return;
	}

	EmptyGunTime += DeltaSeconds;
	if (EmptyGunTime >= AutoReloadDelay)
	{
		EmptyGunTime = 0.0f;
		DoReload();
	}
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
	if ((Shootdodge && Shootdodge->IsDodging()) || (Roll && Roll->IsRolling()))
	{
		return;
	}

	// Knelt after a roll, firing (Vanquish): down for as long as the roll button is held —
	// let go and the normal rule below takes over again (standing, unless the player had
	// asked to crouch anyway).
	if (bPostRollCrouching && !IsRollHeld())
	{
		bPostRollCrouching = false;
	}
	if (bPostRollCrouching)
	{
		if (!bIsCrouched)
		{
			Crouch();
		}
		return;
	}

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
	// A held trigger doesn't break into a reload — only a fresh pull does. Otherwise a
	// tube-fed shotgun would fire each shell the moment it went in.
	if (!EquippedWeapon || EquippedWeapon->IsReloading())
	{
		return;
	}

	// Every weapon keeps firing while the trigger's held (Max Payne): Triggered comes every
	// frame, and the weapon's TimeBetweenShots paces it.
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
