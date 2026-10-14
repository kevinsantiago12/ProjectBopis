// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/EncounterDirector.h"
#include "Enemies/EnemyBase.h"
#include "Weapons/WeaponBase.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Components/CapsuleComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"

AEncounterDirector::AEncounterDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.2f;
}

void AEncounterDirector::BeginPlay()
{
	Super::BeginPlay();

	// The fight starts full.
	for (int32 Index = 0; Index < MaxAlive; ++Index)
	{
		if ((TotalEnemies > 0 && SpawnedCount >= TotalEnemies) || !TrySpawnOne())
		{
			break;
		}
	}
}

void AEncounterDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// The fallen (and the cleaned-up) drop out of the count.
	Alive.RemoveAll([](const TWeakObjectPtr<AEnemyBase>& Enemy) { return !Enemy.IsValid() || Enemy->IsDead(); });

	const bool bMoreToCome = TotalEnemies <= 0 || SpawnedCount < TotalEnemies;
	if (!bMoreToCome || Alive.Num() >= MaxAlive)
	{
		RespawnAt = -1.0f;
		return;
	}

	// One short: a replacement comes in after a moment — and keeps trying if no point is free.
	const float Now = GetWorld()->GetTimeSeconds();
	if (RespawnAt < 0.0f)
	{
		RespawnAt = Now + FMath::FRandRange(RespawnDelayMin, FMath::Max(RespawnDelayMin, RespawnDelayMax));
	}
	else if (Now >= RespawnAt && TrySpawnOne())
	{
		RespawnAt = -1.0f;
	}
}

AActor* AEncounterDirector::PickSpawnPoint() const
{
	const APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	const APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	FVector ViewLocation = FVector::ZeroVector;
	FRotator ViewRotation = FRotator::ZeroRotator;
	if (PlayerController)
	{
		PlayerController->GetPlayerViewPoint(ViewLocation, ViewRotation);
	}

	TArray<AActor*> Usable;
	TArray<AActor*> OutOfView;
	for (AActor* Point : SpawnPoints)
	{
		if (!Point)
		{
			continue;
		}
		const FVector Location = Point->GetActorLocation();

		// Not right next to the player, and not on top of someone already standing there.
		if (Player && FVector::Dist(Location, Player->GetActorLocation()) < MinSpawnDistance)
		{
			continue;
		}
		const bool bCrowded = Alive.ContainsByPredicate([&Location](const TWeakObjectPtr<AEnemyBase>& Enemy)
		{
			return Enemy.IsValid() && FVector::Dist(Enemy->GetActorLocation(), Location) < 150.0f;
		});
		if (bCrowded)
		{
			continue;
		}

		Usable.Add(Point);
		// Outside about 60° either side of where the player is looking.
		if (PlayerController && (ViewRotation.Vector() | (Location - ViewLocation).GetSafeNormal()) < 0.5f)
		{
			OutOfView.Add(Point);
		}
	}

	const TArray<AActor*>& Choices = (bPreferOutOfView && OutOfView.Num() > 0) ? OutOfView : Usable;
	return Choices.Num() > 0 ? Choices[FMath::RandRange(0, Choices.Num() - 1)] : nullptr;
}

bool AEncounterDirector::TrySpawnOne()
{
	AActor* Point = PickSpawnPoint();
	if (!EnemyClass || !Point)
	{
		return false;
	}

	// Stood on the point, not sunk into the floor: lifted by the class's capsule half-height.
	const AEnemyBase* Defaults = EnemyClass->GetDefaultObject<AEnemyBase>();
	const float HalfHeight = Defaults->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FTransform SpawnTransform(FRotator(0.0f, Point->GetActorRotation().Yaw, 0.0f),
		Point->GetActorLocation() + FVector(0.0f, 0.0f, HalfHeight));

	// Deferred, so its gun can be chosen before it begins play and equips one.
	AEnemyBase* Enemy = GetWorld()->SpawnActorDeferred<AEnemyBase>(EnemyClass, SpawnTransform, nullptr, nullptr,
		ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding);
	if (!Enemy)
	{
		return false;
	}
	if (WeaponPool.Num() > 0)
	{
		if (UWeaponHolderComponent* Holder = Enemy->GetWeaponHolder())
		{
			Holder->SetStartingWeaponClass(WeaponPool[FMath::RandRange(0, WeaponPool.Num() - 1)]);
		}
	}
	Enemy->FinishSpawning(SpawnTransform);
	if (!IsValid(Enemy))
	{
		return false;
	}

	Alive.Add(Enemy);
	++SpawnedCount;
	if (bSpawnAlerted)
	{
		Enemy->Alert(UGameplayStatics::GetPlayerPawn(this, 0));
	}
	return true;
}
