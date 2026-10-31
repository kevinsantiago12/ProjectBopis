#include "Gameplay/GamepadAimComponent.h"
#include "ProjectBopisCharacter.h"
#include "Enemies/EnemyBase.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/App.h"

UGamepadAimComponent::UGamepadAimComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

APlayerController* UGamepadAimComponent::GetPlayerController() const
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	return Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
}

bool UGamepadAimComponent::CanAssist() const
{
	const AProjectBopisCharacter* Character = Cast<AProjectBopisCharacter>(GetOwner());
	const UWeaponHolderComponent* Holder = Character ? Character->GetWeaponHolder() : nullptr;
	return bSoftLock && bUsingGamepad && Character && !Character->IsDead() && !Character->IsWeaponWheelOpen()
		&& !Character->IsInKillCam() && Holder && Holder->GetEquippedWeapon() && GetPlayerController();
}

void UGamepadAimComponent::ApplyStick(const FVector2D& Stick, bool bAiming)
{
	APlayerController* PlayerController = GetPlayerController();
	if (!PlayerController)
	{
		return;
	}

	// Real time: slow motion slows the world, not the player's aim.
	const float DeltaTime = FApp::GetDeltaTime();
	const double Now = FPlatformTime::Seconds();

	// The push's strength through the response curve, kept in the push's direction.
	const float Push = FMath::Min(1.0f, Stick.Size());
	const FVector2D Direction = Stick.GetSafeNormal();
	const float Curved = FMath::Pow(Push, ResponseExponent);

	// Held hard sideways a moment, the boost ramps in, for turning on the spot. A gap in the
	// input (the stick let go) starts the count over.
	if (Now - LastStickTime > 0.1 || FMath::Abs(Stick.X) < 0.9f)
	{
		HardOverTime = 0.0f;
	}
	else
	{
		HardOverTime += DeltaTime;
	}
	LastStickTime = Now;
	const float Boost = FMath::Clamp((HardOverTime - BoostDelay) / BoostRampTime, 0.0f, 1.0f) * BoostYawSpeed;

	// Slower near an enemy, the more so the nearer the crosshair is to dead on.
	float Slowdown = 1.0f;
	float Angle = 0.0f;
	FVector AimPoint;
	if (CanAssist() && FindTarget(SlowdownAngle, Angle, AimPoint))
	{
		Slowdown = 1.0f - SlowdownStrength * (1.0f - Angle / FMath::Max(SlowdownAngle, KINDA_SMALL_NUMBER));
	}

	const float Scale = (bAiming ? AimSpeedScale : 1.0f) * Slowdown;
	const float Yaw = Direction.X * Curved * (YawSpeed + Boost) * Scale * DeltaTime;
	const float PitchSign = bInvertPitch ? 1.0f : -1.0f;
	const float Pitch = PitchSign * Direction.Y * Curved * PitchSpeed * Scale * DeltaTime;
	PlayerController->SetControlRotation(PlayerController->GetControlRotation() + FRotator(Pitch, Yaw, 0.0f));
}

void UGamepadAimComponent::SnapToTarget()
{
	float Angle = 0.0f;
	FVector AimPoint;
	SnapTarget = CanAssist() ? FindTarget(SnapAngle, Angle, AimPoint) : nullptr;
	SnapTimeLeft = SnapTarget.IsValid() ? SnapTime : 0.0f;
}

void UGamepadAimComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	APlayerController* PlayerController = GetPlayerController();
	if (!PlayerController || !CanAssist())
	{
		SnapTimeLeft = 0.0f;
		return;
	}
	FVector ViewLocation;
	FRotator ViewRotation;
	PlayerController->GetPlayerViewPoint(ViewLocation, ViewRotation);

	// The snap: eased onto the target's aim point over SnapTime, in real time.
	const AEnemyBase* Snapping = SnapTarget.Get();
	if (SnapTimeLeft > 0.0f && Snapping && !Snapping->IsDead())
	{
		const float RealDelta = FApp::GetDeltaTime();
		const FRotator Wanted = (GetAimPoint(Snapping) - ViewLocation).Rotation();
		const FRotator Current = PlayerController->GetControlRotation();
		const float Alpha = FMath::Clamp(RealDelta / SnapTimeLeft, 0.0f, 1.0f);
		PlayerController->SetControlRotation(Current + (Wanted - Current).GetNormalized() * Alpha);
		SnapTimeLeft -= RealDelta;
		return;
	}
	SnapTimeLeft = 0.0f;

	// Following: the view turns with an enemy near the crosshair as the line to it swings, from
	// its movement and the player's, by FollowStrength. World time: both move in it.
	float Angle = 0.0f;
	FVector AimPoint;
	if (const AEnemyBase* Target = FindTarget(FollowAngle, Angle, AimPoint))
	{
		const FVector Offset = AimPoint - ViewLocation;
		const FVector Velocity = Target->GetVelocity() - GetOwner()->GetVelocity();
		const float Flat = FVector2D(Offset.X, Offset.Y).SizeSquared();
		if (Flat > 1.0f)
		{
			// How fast the line of sight turns (radians per second), round the vertical and up/down.
			const float FlatLength = FMath::Sqrt(Flat);
			const float YawRate = (Offset.X * Velocity.Y - Offset.Y * Velocity.X) / Flat;
			const float PitchRate = (FlatLength * Velocity.Z - Offset.Z * (Offset.X * Velocity.X + Offset.Y * Velocity.Y) / FlatLength)
				/ Offset.SizeSquared();
			const FRotator Turn(FMath::RadiansToDegrees(PitchRate), FMath::RadiansToDegrees(YawRate), 0.0f);
			PlayerController->SetControlRotation(PlayerController->GetControlRotation() + Turn * (FollowStrength * DeltaTime));
		}
	}
}

AEnemyBase* UGamepadAimComponent::FindTarget(float MaxAngle, float& OutAngle, FVector& OutAimPoint) const
{
	const APlayerController* PlayerController = GetPlayerController();
	if (!PlayerController || MaxAngle <= 0.0f)
	{
		return nullptr;
	}
	FVector ViewLocation;
	FRotator ViewRotation;
	PlayerController->GetPlayerViewPoint(ViewLocation, ViewRotation);
	const FVector Forward = ViewRotation.Vector();

	// Our own gun can sit in the camera's line; it never blocks the view of a target.
	FCollisionQueryParams Params(SCENE_QUERY_STAT(GamepadAimSight), false, GetOwner());
	if (const AProjectBopisCharacter* Character = Cast<AProjectBopisCharacter>(GetOwner()))
	{
		if (const UWeaponHolderComponent* Holder = Character->GetWeaponHolder(); Holder && Holder->GetEquippedWeapon())
		{
			Params.AddIgnoredActor(Holder->GetEquippedWeapon());
		}
	}

	AEnemyBase* Best = nullptr;
	float BestAngle = MaxAngle;
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		AEnemyBase* Enemy = *It;
		if (Enemy->IsDead() || Enemy->IsAsleep())
		{
			continue;
		}
		const FVector AimPoint = GetAimPoint(Enemy);
		const FVector ToTarget = AimPoint - ViewLocation;
		const float Distance = ToTarget.Size();
		if (Distance > MaxRange || Distance < KINDA_SMALL_NUMBER)
		{
			continue;
		}
		const float Angle = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(Forward, ToTarget / Distance), -1.0f, 1.0f)));
		if (Angle > BestAngle)
		{
			continue;
		}

		// In sight from the camera: nothing in the way but the enemy and its gun.
		FCollisionQueryParams SightParams = Params;
		SightParams.AddIgnoredActor(Enemy);
		if (const UWeaponHolderComponent* EnemyHolder = Enemy->GetWeaponHolder(); EnemyHolder && EnemyHolder->GetEquippedWeapon())
		{
			SightParams.AddIgnoredActor(EnemyHolder->GetEquippedWeapon());
		}
		FHitResult Hit;
		if (GetWorld()->LineTraceSingleByChannel(Hit, ViewLocation, AimPoint, ECC_Visibility, SightParams))
		{
			continue;
		}
		Best = Enemy;
		BestAngle = Angle;
		OutAimPoint = AimPoint;
	}
	OutAngle = BestAngle;
	return Best;
}

FVector UGamepadAimComponent::GetAimPoint(const AEnemyBase* Enemy) const
{
	const USkeletalMeshComponent* Mesh = Enemy->GetMesh();
	return (Mesh && Mesh->DoesSocketExist(TargetBone)) ? Mesh->GetSocketLocation(TargetBone) : Enemy->GetActorLocation();
}
