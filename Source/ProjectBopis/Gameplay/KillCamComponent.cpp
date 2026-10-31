// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/KillCamComponent.h"
#include "Gameplay/FocusComponent.h"
#include "Gameplay/EncounterTrigger.h"
#include "Gameplay/EncounterDirector.h"
#include "Enemies/EnemyBase.h"
#include "ProjectBopisCharacter.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraTypes.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/App.h"

UKillCamComponent::UKillCamComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// After physics, so the camera follows where a ragdoll is this frame, not the last.
	PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void UKillCamComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// Never leave the world slowed behind us.
	Stop();
	Super::EndPlay(EndPlayReason);
}

void UKillCamComponent::NotifyKill(AEnemyBase* Victim)
{
	const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(GetOwner());
	if (!bEnabled || bActive || !Victim || !Player || Player->IsDead() || Player->IsWeaponWheelOpen())
	{
		return;
	}

	// Only the kill that ends a fight, with no one anywhere else still fighting: one that leaves
	// its room done (no one standing, nothing left to come), or its director's set fight. The
	// room's (or the director's) own shot if it picks one, else ours. Enemies of neither never
	// play it.
	if (IsAnyoneFighting(Victim))
	{
		return;
	}
	for (TActorIterator<AEncounterTrigger> It(GetWorld()); It; ++It)
	{
		if (It->HasEnemy(Victim))
		{
			if (It->PlaysKillCam() && It->IsRoomDone())
			{
				Start(Victim, It->GetKillCamStyle(Style));
			}
			return;
		}
	}
	for (TActorIterator<AEncounterDirector> It(GetWorld()); It; ++It)
	{
		if (It->HasEnemy(Victim))
		{
			if (It->PlaysKillCam() && It->IsFightDone())
			{
				Start(Victim, It->GetKillCamStyle(Style));
			}
			return;
		}
	}
}

void UKillCamComponent::Start(AEnemyBase* Victim, EKillCamStyle Shot)
{
	Target = Victim;
	LastTargetPoint = GetTargetPoint();
	LookPoint = LastTargetPoint;

	// Where the player's camera is, round the body: the side the shots start from.
	FVector ViewLocation = LookPoint - Victim->GetActorForwardVector() * StartDistance;
	const APawn* Pawn = Cast<APawn>(GetOwner());
	const APlayerController* PlayerController = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (PlayerController && PlayerController->PlayerCameraManager)
	{
		ViewLocation = PlayerController->PlayerCameraManager->GetCameraLocation();
	}
	const FVector FromBody = ViewLocation - LookPoint;
	const float PlayerSideYaw = FromBody.Rotation().Yaw;
	const float PlayerSideRadius = FMath::Clamp(static_cast<float>(FromBody.Size2D()), EndDistance, FMath::Max(StartDistance, EndDistance));

	// Random: one of the three, picked fresh each kill. The shot, if it has a clear place to
	// stand; else the orbit. Nowhere clear for that either (a body in a cupboard): no kill cam.
	if (Shot == EKillCamStyle::Random)
	{
		const EKillCamStyle Shots[] = { EKillCamStyle::Orbit, EKillCamStyle::ReverseShot, EKillCamStyle::Steady };
		Shot = Shots[FMath::RandRange(0, 2)];
	}
	Playing = Shot;
	bool bPlaced = (Shot == EKillCamStyle::ReverseShot && PlaceReverseShot())
		|| (Shot == EKillCamStyle::Steady && PlaceSteady(PlayerSideYaw));
	if (!bPlaced)
	{
		Playing = EKillCamStyle::Orbit;
		bPlaced = PlaceOrbit(PlayerSideYaw, PlayerSideRadius);
	}
	if (!bPlaced)
	{
		Target = nullptr;
		return;
	}

	bActive = true;
	bBlendingOut = false;
	bSpinHeld = false;
	HiddenTime = 0.0f;
	Elapsed = 0.0f;
	EndAt = MinDuration;
	BlendOutElapsed = 0.0f;
	Weight = 0.0f;

	if (UFocusComponent* Focus = GetFocus())
	{
		Focus->SetTimeDilationOverride(TimeDilation);
	}
	if (StartSound)
	{
		UGameplayStatics::PlaySound2D(this, StartSound);
	}
	UpdateCamera(0.0f);
}

bool UKillCamComponent::PlaceOrbit(float PlayerSideYaw, float PlayerSideRadius)
{
	// A fresh swing: no turn back yet.
	bSwungBack = false;
	SwingStartedAt = 0.0f;

	// The player's side if that's clear, else the nearest clear place round from it, at its
	// distance or else in close (the first that's clear wins: || stops there).
	const auto TryStart = [this](float Yaw, float Radius)
	{
		StartYaw = Yaw;
		StartRadius = Radius;
		return IsClearView(GetSwingLocation(0.0f, 1.0f));
	};
	constexpr float SearchStep = 20.0f;
	bool bClearStart = false;
	for (float Offset = 0.0f; Offset <= 180.0f && !bClearStart; Offset += SearchStep)
	{
		bClearStart = TryStart(PlayerSideYaw + Offset, PlayerSideRadius) || TryStart(PlayerSideYaw - Offset, PlayerSideRadius)
			|| TryStart(PlayerSideYaw + Offset, EndDistance) || TryStart(PlayerSideYaw - Offset, EndDistance);
	}
	if (!bClearStart)
	{
		return false;
	}

	// It swings toward the side it can go further round with nothing in the way (looked at up to
	// where it'd be once MinDuration's up).
	const auto ClearSteps = [this](float Sign)
	{
		constexpr int32 Steps = 8;
		int32 Clear = 0;
		while (Clear < Steps && IsClearView(GetSwingLocation(MinDuration * (Clear + 1) / Steps, Sign)))
		{
			++Clear;
		}
		return Clear;
	};
	OrbitSign = ClearSteps(1.0f) >= ClearSteps(-1.0f) ? 1.0f : -1.0f;
	CameraLocation = GetSwingLocation(0.0f, OrbitSign);
	return true;
}

bool UKillCamComponent::PlaceReverseShot()
{
	// Behind the body on the line from the player through it, off to one side: over its
	// shoulder, back at the player, seeing both. Then the other side, then half as far off to
	// the side, then all of that in closer. No room anywhere behind it (a body against a wall):
	// false.
	PlayerLookPoint = GetPlayerPoint();
	const FVector Back = (LookPoint - PlayerLookPoint).GetSafeNormal2D();
	if (Back.IsNearlyZero())
	{
		return false;
	}
	const FVector Across = FVector::CrossProduct(FVector::UpVector, Back);
	const float Distances[] = { ReverseDistance, ReverseDistance * 0.6f };
	const float Sides[] = { ReverseSide, -ReverseSide, ReverseSide * 0.5f, -ReverseSide * 0.5f };
	for (const float Distance : Distances)
	{
		for (const float Side : Sides)
		{
			const FVector Spot = LookPoint + Back * Distance + Across * Side + FVector(0.0f, 0.0f, ReverseHeight);
			if (IsClearView(Spot) && CanSee(Spot, PlayerLookPoint))
			{
				CameraLocation = Spot;
				return true;
			}
		}
	}
	return false;
}

bool UKillCamComponent::PlaceSteady(float PlayerSideYaw)
{
	// High up, SteadyAngle round from the player's side (either way). If nothing's clear there:
	// further round, then in closer, then lower (a low ceiling). Nowhere clear: false.
	const float Heights[] = { SteadyHeight, SteadyHeight * 0.5f };
	const float Distances[] = { SteadyDistance, SteadyDistance * 0.6f };
	const float Signs[] = { 1.0f, -1.0f };
	constexpr float SearchStep = 20.0f;
	for (const float Height : Heights)
	{
		for (const float Distance : Distances)
		{
			for (float Offset = SteadyAngle; Offset <= 180.0f; Offset += SearchStep)
			{
				for (const float Sign : Signs)
				{
					const FVector Spot = LookPoint + FRotator(0.0f, PlayerSideYaw + Sign * Offset, 0.0f).Vector() * Distance
						+ FVector(0.0f, 0.0f, Height);
					if (IsClearView(Spot))
					{
						CameraLocation = Spot;
						return true;
					}
				}
			}
		}
	}
	return false;
}

void UKillCamComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bActive)
	{
		return;
	}
	const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(GetOwner());
	if (!Player || Player->IsDead())
	{
		Stop();
		return;
	}

	// The frame's real time, before the slow motion.
	const float RealDelta = FApp::GetDeltaTime();
	Elapsed += RealDelta;

	// Over, or someone's joined in (the next room, a straggler who heard it): the view goes back.
	if (!bBlendingOut && (Elapsed >= EndAt || IsAnyoneFighting(nullptr)))
	{
		BeginBlendOut();
	}

	if (bBlendingOut)
	{
		BlendOutElapsed += RealDelta;
		const float Out = BlendOutTime > 0.0f ? FMath::Clamp(BlendOutElapsed / BlendOutTime, 0.0f, 1.0f) : 1.0f;
		if (Out >= 1.0f)
		{
			Finish();
			return;
		}
		Weight = BlendOutFrom * (1.0f - FMath::SmoothStep(0.0f, 1.0f, Out));

		// The world's speed comes back with the view.
		if (UFocusComponent* Focus = GetFocus())
		{
			Focus->SetTimeDilationOverride(FMath::Lerp(TimeDilation, Focus->GetBaseTimeDilation(), Out));
		}
	}
	else
	{
		Weight = BlendInTime > 0.0f ? FMath::SmoothStep(0.0f, BlendInTime, Elapsed) : 1.0f;
	}

	UpdateCamera(RealDelta);
	UpdatePlayerAim(RealDelta);
}

void UKillCamComponent::BeginBlendOut()
{
	bBlendingOut = true;
	BlendOutElapsed = 0.0f;
	BlendOutFrom = Weight;
}

void UKillCamComponent::Stop()
{
	if (bActive)
	{
		Finish();
	}
}

void UKillCamComponent::Finish()
{
	bActive = false;
	bBlendingOut = false;
	Weight = 0.0f;
	Target = nullptr;
	if (UFocusComponent* Focus = GetFocus())
	{
		Focus->ClearTimeDilationOverride();
	}
}

bool UKillCamComponent::IsAnyoneFighting(const AEnemyBase* Except) const
{
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		if (*It != Except && !It->IsDead() && It->IsAlerted())
		{
			return true;
		}
	}
	return false;
}

FVector UKillCamComponent::GetTargetPoint() const
{
	const AEnemyBase* Body = Target.Get();
	return Body ? GetBodyPoint(Body) : LastTargetPoint;
}

FVector UKillCamComponent::GetBodyPoint(const ACharacter* Character) const
{
	const USkeletalMeshComponent* Mesh = Character->GetMesh();
	if (Mesh && Mesh->GetBoneIndex(TargetBone) != INDEX_NONE)
	{
		return Mesh->GetBoneLocation(TargetBone);
	}
	return Mesh ? Mesh->Bounds.Origin : Character->GetActorLocation();
}

FVector UKillCamComponent::GetPlayerPoint() const
{
	const ACharacter* Player = Cast<ACharacter>(GetOwner());
	return Player ? GetBodyPoint(Player) : LookPoint;
}

float UKillCamComponent::GetOrbitAngle(float Time) const
{
	// Constant acceleration up to OrbitSpeed over OrbitEaseTime, then steady.
	if (OrbitEaseTime <= 0.0f)
	{
		return OrbitSpeed * Time;
	}
	if (Time < OrbitEaseTime)
	{
		return 0.5f * OrbitSpeed * Time * Time / OrbitEaseTime;
	}
	return OrbitSpeed * (Time - 0.5f * OrbitEaseTime);
}

FVector UKillCamComponent::GetSwingLocation(float Time, float Sign) const
{
	// The first swing pushes in and sinks over MinDuration; the swing back keeps the distance and
	// height it turned at. Both go round all the while, easing up to speed from their start.
	float Radius = BackRadius;
	float Height = BackHeight;
	if (!bSwungBack)
	{
		const float Push = MinDuration > 0.0f ? FMath::SmoothStep(0.0f, MinDuration, Time) : 1.0f;
		Radius = FMath::Lerp(StartRadius, EndDistance, Push);
		Height = FMath::Lerp(StartHeight, EndHeight, Push);
	}
	const float Yaw = StartYaw + Sign * GetOrbitAngle(Time - SwingStartedAt);
	return LookPoint + FRotator(0.0f, Yaw, 0.0f).Vector() * Radius + FVector(0.0f, 0.0f, Height);
}

bool UKillCamComponent::HasRoom(const FVector& Location) const
{
	// Nothing it would touch.
	const FCollisionShape Room = FCollisionShape::MakeSphere(ProbeRadius);
	if (GetWorld()->OverlapBlockingTestByChannel(Location, FQuat::Identity, ECC_Camera, Room, GetProbeParams()))
	{
		return false;
	}

	// The player's left out of that test, so they get one of their own: not through them either.
	const ACharacter* Player = Cast<ACharacter>(GetOwner());
	const UCapsuleComponent* Capsule = Player ? Player->GetCapsuleComponent() : nullptr;
	return !(Capsule && Capsule->OverlapComponent(Location, FQuat::Identity, Room));
}

bool UKillCamComponent::SeesBody(const FVector& Location) const
{
	// A clear line to the body, up to BodyClearance short of it: a wall the body's slumped
	// against doesn't count. Nearer than that, the camera would be in the body.
	const FVector FromBody = Location - LookPoint;
	if (FromBody.Size() <= BodyClearance)
	{
		return false;
	}
	return CanSee(Location, LookPoint + FromBody.GetSafeNormal() * BodyClearance);
}

bool UKillCamComponent::CanSee(const FVector& From, const FVector& To) const
{
	return !GetWorld()->LineTraceTestByChannel(From, To, ECC_Camera, GetProbeParams());
}

FCollisionQueryParams UKillCamComponent::GetProbeParams() const
{
	FCollisionQueryParams Params(SCENE_QUERY_STAT(KillCamProbe), false, GetOwner());
	if (const AEnemyBase* Body = Target.Get())
	{
		Params.AddIgnoredActor(Body);
	}
	return Params;
}

void UKillCamComponent::UpdateCamera(float RealDelta)
{
	LastTargetPoint = GetTargetPoint();
	LookPoint = RealDelta > 0.0f ? FMath::VInterpTo(LookPoint, LastTargetPoint, RealDelta, FollowSpeed) : LastTargetPoint;

	if (Playing == EKillCamStyle::Orbit && !bSpinHeld)
	{
		UpdateSwing(RealDelta);
	}
	else
	{
		UpdateStill(RealDelta);
	}

	// The reverse shot aims between the player and the body, to have both; the others at the body.
	FVector Aim = LookPoint;
	if (Playing == EKillCamStyle::ReverseShot)
	{
		// Smoothed like the body, so the player's recoil doesn't shake it.
		const FVector PlayerPoint = GetPlayerPoint();
		PlayerLookPoint = RealDelta > 0.0f ? FMath::VInterpTo(PlayerLookPoint, PlayerPoint, RealDelta, FollowSpeed) : PlayerPoint;
		Aim = FMath::Lerp(PlayerLookPoint, LookPoint, ReverseFraming);
	}
	CameraRotation = (Aim - CameraLocation).Rotation();
}

void UKillCamComponent::UpdateSwing(float RealDelta)
{
	// On while the next spot has room and sees the body. Anything in the way stops it: the
	// camera holds where it last had a clear view, still watching the body, rather than going
	// through the wall or jumping in close. Swinging back, it may pass where the body's hidden
	// for a while, coming round to where it was seen.
	const FVector Wanted = GetSwingLocation(Elapsed, OrbitSign);
	if (HasRoom(Wanted))
	{
		if (SeesBody(Wanted))
		{
			CameraLocation = Wanted;
			HiddenTime = 0.0f;
			return;
		}
		if (bSwungBack && HiddenTime < SwingBackGrace)
		{
			CameraLocation = Wanted;
			HiddenTime += RealDelta;
			return;
		}
	}
	bSpinHeld = true;
}

void UKillCamComponent::UpdateStill(float RealDelta)
{
	// The body can drop out of sight from here for HiddenTolerance. Any longer, a stopped orbit
	// swings back the other way (once), and anything else is over early.
	HiddenTime = SeesBody(CameraLocation) ? 0.0f : HiddenTime + RealDelta;
	if (bBlendingOut || HiddenTime < HiddenTolerance)
	{
		return;
	}
	if (Playing == EKillCamStyle::Orbit && !bSwungBack)
	{
		SwingBack();
	}
	else
	{
		BeginBlendOut();
	}
}

void UKillCamComponent::SwingBack()
{
	// From where it stopped, at that distance and height round the body, easing up to speed the
	// other way.
	const FVector FromBody = CameraLocation - LookPoint;
	StartYaw = static_cast<float>(FromBody.Rotation().Yaw);
	BackRadius = static_cast<float>(FromBody.Size2D());
	BackHeight = static_cast<float>(FromBody.Z);
	SwingStartedAt = Elapsed;
	OrbitSign = -OrbitSign;
	bSwungBack = true;
	bSpinHeld = false;
	HiddenTime = 0.0f;
}

void UKillCamComponent::UpdatePlayerAim(float RealDelta)
{
	const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(GetOwner());
	AController* Controller = Player ? Player->GetController() : nullptr;
	if (!Controller)
	{
		return;
	}

	// From the player's own camera, so the crosshair is on the body when the view comes back.
	const UCameraComponent* Camera = Player->GetFollowCamera();
	const FVector From = Camera ? Camera->GetComponentLocation() : Player->GetPawnViewLocation();
	const FRotator Wanted = (LastTargetPoint - From).Rotation();
	Controller->SetControlRotation(FMath::RInterpTo(Controller->GetControlRotation(), Wanted, RealDelta, AimFollowSpeed));
}

FVector UKillCamComponent::TakeShotPoint()
{
	if (bActive && !bBlendingOut)
	{
		EndAt = FMath::Min(MaxDuration, FMath::Max(EndAt, Elapsed + ExtendPerShot));
	}
	return GetTargetPoint() + FMath::VRand() * FMath::FRandRange(0.0f, ShotScatter);
}

void UKillCamComponent::BlendView(FMinimalViewInfo& View) const
{
	if (Weight <= 0.0f)
	{
		return;
	}
	View.Location = FMath::Lerp(View.Location, CameraLocation, Weight);
	View.Rotation = FQuat::Slerp(View.Rotation.Quaternion(), CameraRotation.Quaternion(), Weight).Rotator();
	View.FOV = FMath::Lerp(View.FOV, FieldOfView, Weight);
}

UFocusComponent* UKillCamComponent::GetFocus() const
{
	const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(GetOwner());
	return Player ? Player->GetFocus() : nullptr;
}
