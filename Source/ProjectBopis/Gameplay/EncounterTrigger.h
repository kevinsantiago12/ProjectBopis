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

	/** Seconds after the trigger fires: a stagger, so a doorway pours out one by one. */
	UPROPERTY(EditAnywhere, Category = "Spawn", meta = (ClampMin = "0.0"))
	float Delay = 0.0f;

	/** Joins this other trigger's enemies, to be set off by it (a spawn-ahead line before the
	    room): asleep until then, or patrolling with its senses on if it's a patroller. None: it
	    comes in set off now (a patroller: just patrols). */
	UPROPERTY(EditAnywhere, Category = "Spawn")
	TObjectPtr<AEncounterTrigger> WaitForTrigger;
};

/**
 *  A room's start line: when the player walks into the box, every linked enemy is set off at
 *  once (each still takes its reaction beat before shooting), and its Spawns come in. Place it
 *  at the doorway, midway down a hallway, or before a room as a spawn-ahead line.
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

	/** The enemy class for spawns that don't name one. */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	TSubclassOf<AEnemyBase> DefaultEnemyClass;

	/** Scripted events it starts when it fires (the first time): an overheard conversation as
	    the player comes near, say. */
	UPROPERTY(EditInstanceOnly, Category = "Encounter")
	TArray<TObjectPtr<AEncounterEvent>> EventsToStart;

	/** Editor only: lines to everything it's linked to (enemies orange, spawn points red, ambush
	    points yellow, patrol routes green, the trigger a spawn waits for cyan). */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bDrawLinks = true;

private:
	void DrawLinks() const;
public:

private:
	/** Brings in Spawns[Index]. */
	void SpawnOne(int32 Index);

	bool bTriggered = false;
};
