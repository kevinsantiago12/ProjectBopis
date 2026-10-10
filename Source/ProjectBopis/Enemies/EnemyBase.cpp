// Copyright Epic Games, Inc. All Rights Reserved.

#include "Enemies/EnemyBase.h"
#include "AIController.h"
#include "Navigation/PathFollowingComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "ProjectBopis.h"
#include "ProjectBopisGameMode.h"
#include "Pickups/WeaponDrop.h"
#include "Pickups/WeaponPickup.h"
#include "Weapons/WeaponHolderComponent.h"

AEnemyBase::AEnemyBase()
{
	// Possessed whether placed in the level or spawned at runtime — without this an
	// enemy dropped into the level has no controller, and nothing can ever move it.
	AIControllerClass = AAIController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	// The movement component turns the body (see UpdateMovementMode); the controller
	// never snaps it directly.
	bUseControllerRotationYaw = false;
}

void AEnemyBase::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (IsDead())
	{
		return;
	}

	// Staggered: rooted to the spot — no aiming, turning or patrolling until it passes.
	if (IsStaggered())
	{
		if (AAIController* AI = Cast<AAIController>(GetController()))
		{
			AI->StopMovement();
		}
		return;
	}

	UpdateAim();
	UpdateMovementMode();
	UpdatePatrol(DeltaSeconds);
}

void AEnemyBase::Die(AController* Killer, const FVector& ShotDirection)
{
	Super::Die(Killer, ShotDirection);

	DropWeapon(ShotDirection);

	// The brain goes with the body: unpossess, and the AI controller is destroyed.
	DetachFromControllerPendingDestroy();

	// Counted toward the corpse limit; the oldest body goes once there are too many.
	if (AProjectBopisGameMode* GameMode = GetWorld()->GetAuthGameMode<AProjectBopisGameMode>())
	{
		GameMode->RegisterCorpse(this);
	}
}

void AEnemyBase::DropWeapon(const FVector& ShotDirection)
{
	UWeaponHolderComponent* Holder = GetWeaponHolder();
	AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr;
	if (!Weapon || !WeaponPickupClass)
	{
		return;
	}

	// From the gun's current place in the hand, so it doesn't jump.
	const FTransform GunTransform = Weapon->GetWeaponMesh()->GetComponentTransform();
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AWeaponDrop* Drop = GetWorld()->SpawnActor<AWeaponDrop>(AWeaponDrop::StaticClass(),
		FTransform(GunTransform.GetRotation(), GunTransform.GetLocation()), Params);
	if (!Drop)
	{
		return;
	}

	// Thrown along the killing shot with a little lift, capped so no hit can fling it far.
	const FVector Velocity = (ShotDirection.GetSafeNormal() * WeaponDropSpeed
		+ FVector::UpVector * WeaponDropLift).GetClampedToMaxSize(MaxWeaponDropSpeed);
	Drop->Launch(Weapon->GetClass(), WeaponPickupClass, Velocity, FMath::VRand() * WeaponDropSpin);

	// The gun has left the hand. The weapon actor itself stays with the corpse until cleanup.
	Weapon->SetActorHiddenInGame(true);
}

void AEnemyBase::UpdateAim()
{
	AAIController* AI = Cast<AAIController>(GetController());
	if (!AI)
	{
		return;
	}

	APawn* Player = bAimAtPlayer ? UGameplayStatics::GetPlayerPawn(this, 0) : nullptr;
	if (Player)
	{
		// Focus drives the control rotation, pitch included when the focus is a pawn,
		// so the AnimBP's aim offset tracks the player with no extra work.
		AI->SetFocus(Player);
		SetAiming(true);
	}
	else
	{
		// With no focus, the controller follows the body's facing, so the aim offset rests at zero.
		AI->ClearFocus(EAIFocusPriority::Gameplay);
		SetAiming(bStartRaised);
	}
}

void AEnemyBase::UpdateMovementMode()
{
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	if (!Movement)
	{
		return;
	}

	// The player's two stances, but turning at a rate: an AI's control rotation jumps
	// straight to its focus, which would otherwise snap the body round in one frame.
	const bool bRaised = IsWeaponRaised();
	Movement->bUseControllerDesiredRotation = bRaised;
	Movement->bOrientRotationToMovement = !bRaised;
	Movement->RotationRate = FRotator(0.0f, TurnRate, 0.0f);
	Movement->MaxWalkSpeed = bRaised ? RaisedSpeed : LoweredSpeed;
}

void AEnemyBase::UpdatePatrol(float DeltaSeconds)
{
	AAIController* AI = Cast<AAIController>(GetController());
	if (!AI || PatrolPoints.Num() == 0)
	{
		return;
	}

	// Still walking to the current point.
	if (AI->GetMoveStatus() != EPathFollowingStatus::Idle)
	{
		return;
	}

	// Arrived, or just started: wait, then head for the next point.
	if (PatrolWaitRemaining > 0.0f)
	{
		PatrolWaitRemaining -= DeltaSeconds;
		return;
	}

	AActor* Target = PatrolPoints[PatrolIndex];
	PatrolIndex = (PatrolIndex + 1) % PatrolPoints.Num();
	PatrolWaitRemaining = PatrolWaitTime;

	if (!Target)
	{
		return;
	}

	// bCanStrafe (true by default) leaves the focus alone, so aiming at the player
	// survives the move instead of being replaced by "look where you're going".
	if (AI->MoveToActor(Target, 50.0f) == EPathFollowingRequestResult::Failed)
	{
		UE_LOG(LogProjectBopis, Warning, TEXT("%s: no path to %s — is the level covered by a NavMeshBoundsVolume?"),
			*GetName(), *Target->GetName());
	}
}
