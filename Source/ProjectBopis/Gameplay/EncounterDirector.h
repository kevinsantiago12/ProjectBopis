// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EncounterDirector.generated.h"

class AEnemyBase;
class AWeaponBase;

/**
 *  Runs a fight: keeps MaxAlive enemies alive at once, bringing in a replacement a moment
 *  after each one falls, at spawn points away from (and preferably out of view of) the
 *  player, each with a random weapon from the pool. Place one per arena.
 */
UCLASS()
class PROJECTBOPIS_API AEncounterDirector : public AActor
{
	GENERATED_BODY()

public:

	AEncounterDirector();

	virtual void Tick(float DeltaSeconds) override;

protected:

	virtual void BeginPlay() override;

	/** What comes in. */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	TSubclassOf<AEnemyBase> EnemyClass;

	/** Where enemies come in: any actors (Target Points are the usual pick). */
	UPROPERTY(EditInstanceOnly, Category = "Encounter")
	TArray<TObjectPtr<AActor>> SpawnPoints;

	/** Each spawn gets one of these at random. Empty: the enemy class's own weapon. */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	TArray<TSubclassOf<AWeaponBase>> WeaponPool;

	/** Enemies alive at once. */
	UPROPERTY(EditAnywhere, Category = "Encounter", meta = (ClampMin = "1"))
	int32 MaxAlive = 6;

	/** Seconds (random in range) before a fallen enemy's replacement comes in. */
	UPROPERTY(EditAnywhere, Category = "Encounter", meta = (ClampMin = "0.0"))
	float RespawnDelayMin = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Encounter", meta = (ClampMin = "0.0"))
	float RespawnDelayMax = 3.0f;

	/** Enemies to spawn in all before it stops. 0: endless. */
	UPROPERTY(EditAnywhere, Category = "Encounter", meta = (ClampMin = "0"))
	int32 TotalEnemies = 0;

	/** Spawn points closer than this (cm) to the player aren't used. */
	UPROPERTY(EditAnywhere, Category = "Encounter", meta = (ClampMin = "0.0"))
	float MinSpawnDistance = 1200.0f;

	/** Prefer spawn points the player isn't looking toward, so no one pops in on screen. */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bPreferOutOfView = true;

	/** Spawned enemies start alerted, knowing where the player is. */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bSpawnAlerted = true;

private:

	/** Spawns one enemy at a suitable point. False if none is free (or the spawn failed). */
	bool TrySpawnOne();

	/** A spawn point far enough from the player and not crowded, out of view if possible. */
	AActor* PickSpawnPoint() const;

	TArray<TWeakObjectPtr<AEnemyBase>> Alive;
	int32 SpawnedCount = 0;

	/** World time the next replacement comes in; below 0, none pending. */
	float RespawnAt = -1.0f;
};
