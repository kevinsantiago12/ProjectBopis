// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EncounterTrigger.generated.h"

class UBoxComponent;
class UTextRenderComponent;
class UBillboardComponent;
class AEnemyBase;
class AWeaponBase;
class AEncounterTrigger;
class AEncounterEvent;
class UBarkVoice;

/** One enemy a trigger brings in when it fires. */
USTRUCT(BlueprintType)
struct FEncounterSpawn
{
	GENERATED_BODY()

	/** What comes in. None: the trigger's DefaultEnemyClass. */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	TSubclassOf<AEnemyBase> EnemyClass;

	/** Where it appears: any actor (a Target Point), out of the player's view — behind a door,
	    round a corner. */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	TObjectPtr<AActor> SpawnPoint;

	/** Its gun. None: the class's own. */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	TSubclassOf<AWeaponBase> Weapon;

	/** Where it runs first (out of the room, round the corner). None: from where it appears. */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	TObjectPtr<AActor> AmbushPoint;

	/** How close (cm) to the AmbushPoint counts as arrived, measured to its centre. */
	UPROPERTY(EditAnywhere, Category = "Spawn", meta = (ClampMin = "0.0"))
	float AmbushAcceptanceRadius = 20.0f;

	/** No AmbushPoint: its first move is a charge at the player. */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	bool bRushOnTrigger = false;

	/** Holds its ground (at its AmbushPoint, or where it appears) rather than roaming in. */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	bool bHoldsPosition = false;

	/** How far (cm) from its spot a holder may move. */
	UPROPERTY(EditAnywhere, Category = "Spawn", meta = (ClampMin = "0.0", EditCondition = "bHoldsPosition"))
	float HoldRadius = 400.0f;

	/** A holder that waits and fights crouched, standing only to move. */
	UPROPERTY(EditAnywhere, Category = "Spawn", meta = (EditCondition = "bHoldsPosition"))
	bool bCrouchWhileHolding = false;

	/** A patroller (no AmbushPoint, no rush, not holding) walks these in a loop with its senses on
	    until it spots the player or its trigger sets it off. Empty: it stands where it appears. */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	TArray<TObjectPtr<AActor>> PatrolPoints;

	/** A name for the spawned enemy (an actor tag), so a scripted event can use it as a speaker
	    (its steps' SpeakerTag). */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	FName Tag;

	/** Its bark voice instead of the class's own. None: the class's. */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	TObjectPtr<UBarkVoice> Voice;

	/** Seconds after the trigger fires (in a wave: after the wave starts): a stagger, so a doorway
	    pours out one by one. */
	UPROPERTY(EditAnywhere, Category = "Spawn", meta = (ClampMin = "0.0"))
	float Delay = 0.0f;

	/** Joins this other trigger's enemies, to be set off by it (a spawn-ahead line before the
	    room): asleep until then, or patrolling with its senses on if it's a patroller. None: it
	    comes in set off now (a patroller: just patrols). */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	TObjectPtr<AEncounterTrigger> WaitForTrigger;
};

/** More enemies a trigger brings in after its first Spawns, once the room has thinned out. */
USTRUCT(BlueprintType)
struct FEncounterWave
{
	GENERATED_BODY()

	/** Who comes in: entries as in the trigger's Spawns, each on its own Delay from the wave's start. */
	UPROPERTY(EditAnywhere, Category = "Wave")
	TArray<FEncounterSpawn> Spawns;

	/** It's due once the room is down to this many standing (0: everyone before it down),
	    counted only after the wave before it is all in. */
	UPROPERTY(EditAnywhere, Category = "Wave", meta = (ClampMin = "0"))
	int32 StartWhenAliveAtMost = 0;

	/** Seconds from due to coming in: a breather. */
	UPROPERTY(EditAnywhere, Category = "Wave", meta = (ClampMin = "0.0"))
	float Delay = 2.0f;

	/** Scripted events it starts as it comes in (a shout for backup, say). */
	UPROPERTY(EditAnywhere, Category = "Wave")
	TArray<TObjectPtr<AEncounterEvent>> EventsToStart;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FEncounterClearedSignature, AEncounterTrigger*, Trigger);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FEncounterWaveSignature, AEncounterTrigger*, Trigger, int32, WaveIndex);

/**
 *  A room's start line: when the player walks into the box, every linked enemy is set off at
 *  once (each still takes its reaction beat before shooting), and its Spawns come in. Place it
 *  at the doorway, midway down a hallway, or before a room as a spawn-ahead line. Its Waves
 *  follow as the room thins out; once every enemy it set off or brought in is down, the room's
 *  cleared, and what waits on that goes.
 */
UCLASS()
class PROJECTBOPIS_API AEncounterTrigger : public AActor
{
	GENERATED_BODY()

public:
	AEncounterTrigger();

	virtual void OnConstruction(const FTransform& Transform) override;

	/** Editor only: ticks in the level viewport to draw its link lines. */
	virtual void Tick(float DeltaSeconds) override;
	virtual bool ShouldTickIfViewportsOnly() const override { return true; }

	/** Hands this trigger an enemy to set off (one spawned ahead by another trigger). If this one
	    has already fired, it's set off now. */
	void AddEnemy(AEnemyBase* Enemy, bool bWait = true);

	/** Goes off as if the player had walked in (a scripted event's Set Off Encounter step). */
	void Fire();

	/** Every enemy it set off or brought in is down, with no one (and no wave) left to come. */
	UFUNCTION(BlueprintPure, Category = "Encounter")
	bool IsCleared() const { return bCleared; }

	/** Its enemies still standing, spawns on their way included (not waves still to come). */
	UFUNCTION(BlueprintPure, Category = "Encounter")
	int32 GetAliveCount() const;

	/** Goes off once, when the room's cleared: for a level script (music, a door). */
	UPROPERTY(BlueprintAssignable, Category = "Encounter")
	FEncounterClearedSignature OnCleared;

	/** Goes off as each wave comes in (WaveIndex: its place in Waves, from 0). */
	UPROPERTY(BlueprintAssignable, Category = "Encounter")
	FEncounterWaveSignature OnWaveStarted;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnVolumeOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, Category = "Encounter")
	TObjectPtr<UBoxComponent> Volume;

	/** Editor-only text: name, enemies and spawns. */
	UPROPERTY(VisibleAnywhere, Category = "Encounter")
	TObjectPtr<UTextRenderComponent> Label;

#if WITH_EDITORONLY_DATA
	/** Editor-only icon at the centre: something to click instead of the box's edges. */
	UPROPERTY()
	TObjectPtr<UBillboardComponent> Icon;
#endif

	/** The enemies this sets off. */
	UPROPERTY(EditInstanceOnly, Category = "Encounter")
	TArray<TObjectPtr<AEnemyBase>> Enemies;

	/** Goes off once. Off: every time the player walks in (already-alerted enemies just stay alerted). */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bTriggerOnce = true;

	/** Its enemies wait for it: they don't see, hear or take allies' alerts until the player walks
	    in (being shot still wakes them). Off: they can start on their own; the trigger just makes
	    sure the whole room goes at once. */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bEnemiesWaitForTrigger = true;

	/** Enemies brought in when it fires (the first time only): set off now, or asleep in place for
	    another trigger (WaitForTrigger). */
	UPROPERTY(EditInstanceOnly, Category = "Encounter")
	TArray<FEncounterSpawn> Spawns;

	/** More enemies after the first Spawns, in order, each once the room has thinned out (the
	    first, only after the trigger's fired). The room isn't cleared till the last is in and down. */
	UPROPERTY(EditInstanceOnly, Category = "Encounter|Waves")
	TArray<FEncounterWave> Waves;

	/** The enemy class for spawns that don't name one. */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	TSubclassOf<AEnemyBase> DefaultEnemyClass;

	/** Scripted events it starts when it fires (the first time): an overheard conversation as
	    the player comes near, say. */
	UPROPERTY(EditInstanceOnly, Category = "Encounter")
	TArray<TObjectPtr<AEncounterEvent>> EventsToStart;

	/** Scripted events it starts once the room's cleared. */
	UPROPERTY(EditInstanceOnly, Category = "Encounter|Cleared")
	TArray<TObjectPtr<AEncounterEvent>> EventsOnCleared;

	/** Triggers it sets off once the room's cleared (the next room's ambush, say). */
	UPROPERTY(EditInstanceOnly, Category = "Encounter|Cleared")
	TArray<TObjectPtr<AEncounterTrigger>> TriggersOnCleared;

	/** Editor only: lines to everything it's linked to (enemies orange, spawn points red — a
	    wave's pink — ambush points yellow, patrol routes green, the trigger a spawn waits for
	    cyan, what it sets going once cleared white). */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bDrawLinks = true;

private:
	void DrawLinks() const;
public:

private:
	/** Brings in a list's entries, each on its own Delay: the first Spawns (WaveIndex INDEX_NONE)
	    or a wave's. */
	void BringIn(int32 WaveIndex);

	/** Brings in Spawns[Index] (WaveIndex INDEX_NONE) or Waves[WaveIndex].Spawns[Index]. */
	void SpawnOne(int32 WaveIndex, int32 Index);

	/** Polled: brings in the next wave when it's due, and once the room's cleared, sets going
	    what waits on it. */
	void UpdateRoom();

	/** Builds a list's entries asleep at the start (Spawns: WaveIndex INDEX_NONE), so bringing
	    one in only wakes it and nothing is built mid-fight. */
	void BuildReserves(int32 WaveIndex, const TArray<FEncounterSpawn>& List);

	/** Spawns an enemy, deferred so its gun is chosen first; asleep (hidden, no AI) or set going. */
	AEnemyBase* BuildEnemy(TSubclassOf<AEnemyBase> Class, TSubclassOf<AWeaponBase> Weapon,
		const FTransform& Where, bool bAsleep);

	bool bTriggered = false;

	bool bCleared = false;

	/** Delayed spawns that haven't come in yet: the room isn't cleared without them. */
	int32 PendingSpawns = 0;

	/** The wave to come next (an index into Waves), and the world time it comes (below 0: not
	    due yet). */
	int32 NextWave = 0;
	double NextWaveAt = -1.0;

	FTimerHandle RoomTimer;

	/** The sleeping enemies, by (WaveIndex, Index): one for each spawn still to come. */
	TMap<FIntPoint, TWeakObjectPtr<AEnemyBase>> Reserves;
};
