// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "BopisCharacterBase.h"
#include "EnemyBase.generated.h"

class AWeaponPickup;
class UStateTree;

/**
 *  An enemy: the shared humanoid (weapon, montages, AnimBP) driven by an AI controller
 *  instead of input. Behaviour, movement and damage get layered on in later steps.
 */
UCLASS(abstract)
class PROJECTBOPIS_API AEnemyBase : public ABopisCharacterBase
{
	GENERATED_BODY()

public:

	AEnemyBase();

	virtual void Tick(float DeltaSeconds) override;

protected:

	virtual void BeginPlay() override;

	virtual void Die(AController* Killer, const FVector& ShotDirection) override;

	/** Knocks the equipped gun out of the hand: it tumbles on physics, then becomes a pickup. */
	void DropWeapon(const FVector& ShotDirection);

	/** What a dropped gun becomes once it lands. Empty: enemies keep their guns. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Weapon Drop")
	TSubclassOf<AWeaponPickup> WeaponPickupClass;

	/** Throw along the killing shot, in cm/s. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Weapon Drop", meta = (ClampMin = "0.0"))
	float WeaponDropSpeed = 250.0f;

	/** Upward part of the throw, in cm/s. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Weapon Drop", meta = (ClampMin = "0.0"))
	float WeaponDropLift = 150.0f;

	/** Hard cap on the throw's total speed, however it's tuned. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Weapon Drop", meta = (ClampMin = "0.0"))
	float MaxWeaponDropSpeed = 400.0f;

	/** Tumble, in degrees per second about a random axis. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Weapon Drop", meta = (ClampMin = "0.0"))
	float WeaponDropSpin = 360.0f;

	/** Starts with the weapon up. For checking the raised pose before any AI drives it. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Debug")
	bool bStartRaised = false;

	/** Walked in order, looping. Any actors will do (Target Points are the usual pick).
	    Empty: stands still. Test behaviour until the StateTree takes over. */
	UPROPERTY(EditInstanceOnly, Category = "Enemy|Test Behaviour")
	TArray<TObjectPtr<AActor>> PatrolPoints;

	/** Seconds to wait at each patrol point before moving on. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Test Behaviour", meta = (ClampMin = "0.0"))
	float PatrolWaitTime = 1.0f;

	/** Starts the level already aware of the player — for pure arena tests. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Awareness")
	bool bStartAlerted = false;

	/** An alerted enemy alerts others within this distance (cm)... */
	UPROPERTY(EditAnywhere, Category = "Enemy|Awareness", meta = (ClampMin = "0.0"))
	float AlertAlliesRadius = 1500.0f;

	/** ...this many seconds after it was alerted itself, so the word spreads as a ripple. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Awareness", meta = (ClampMin = "0.0"))
	float AlertAlliesDelay = 0.5f;

	/** Seconds out of sight before it stops tracking the player and aims at where they
	    were last seen instead — no following them through walls. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Awareness", meta = (ClampMin = "0.0"))
	float TrackThroughCoverTime = 0.3f;

	/** This archetype's behaviour, run by its controller. Empty: none (it stands, or
	    patrols while unaware). */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour")
	TObjectPtr<UStateTree> Behaviour;

	/** The distance from the player (cm) it likes to fight at. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour", meta = (ClampMin = "0.0"))
	float PreferredRangeMin = 600.0f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour", meta = (ClampMin = "0.0"))
	float PreferredRangeMax = 1500.0f;

	/** How far (cm) one reposition can take it. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour", meta = (ClampMin = "100.0"))
	float RepositionRadius = 800.0f;

	/** Spots tried per reposition; the best one wins. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour", meta = (ClampMin = "1"))
	int32 EngageSpotSamples = 12;

	/** Keeps its spots this far (cm) from other enemies. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour", meta = (ClampMin = "0.0"))
	float AllySpacing = 300.0f;

	/** Chance (0..1), each time it repositions, that it rushes in close instead. Random on
	    purpose — mooks charging in are there to be gunned down in style. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Push", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float PushChance = 0.2f;

	/** How close (cm) to the player a push tries to get. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Push", meta = (ClampMin = "0.0"))
	float PushRangeMin = 200.0f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Push", meta = (ClampMin = "0.0"))
	float PushRangeMax = 450.0f;

	/** Walk speed (cm/s) while pushing in, gun up. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Push", meta = (ClampMin = "0.0"))
	float PushSpeed = 450.0f;

	/** Shots held this long (seconds) for an ally in the line of fire, and it moves on to a
	    new spot rather than waiting out its hold (Gunman Check: Line Of Fire Blocked). */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour", meta = (ClampMin = "0.0"))
	float RepositionWhenBlockedAfter = 1.0f;

	/** How wide (cm, radius) a clear line of fire must be: an ally this close to a shot's
	    path counts as in the way, and the shot is held. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour", meta = (ClampMin = "0.0"))
	float LineOfFireRadius = 20.0f;

	/** Searching: this long (seconds) at the last known spot without finding the player and
	    the lead is gone — it roams instead (Gunman Check: Lead Gone). */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Roam", meta = (ClampMin = "0.0"))
	float LeadGoneAfter = 3.0f;

	/** Roaming: chance (0..1) each leg heads for the Target Point furthest from it, across
	    the map; otherwise a random reachable spot within RoamRadius. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Roam", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float RoamToPointChance = 0.5f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Roam", meta = (ClampMin = "100.0"))
	float RoamRadius = 3000.0f;

	/** Max walk speed with the weapon lowered. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Movement", meta = (ClampMin = "0.0"))
	float LoweredSpeed = 300.0f;

	/** Max walk speed with the weapon raised. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Movement", meta = (ClampMin = "0.0"))
	float RaisedSpeed = 250.0f;

	/** How fast the body turns, in degrees per second, toward travel or toward the aim. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Movement", meta = (ClampMin = "0.0"))
	float TurnRate = 360.0f;

	// ---- Shooting ----

	/** Fires at the player once alerted, while able to see them. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting")
	bool bShootAtPlayer = true;

	/** After losing sight of the player, keeps firing at where they were last seen for this
	    long (seconds) — pinning them behind cover. 0: holds fire (trained enemies). */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting", meta = (ClampMin = "0.0"))
	float SuppressFireDuration = 2.0f;

	/** A fresh engagement opens with a warning burst: every round of the first burst misses.
	    Off for trained enemies. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting")
	bool bWarningBurst = true;

	/** Out of sight this long (seconds) and the next engagement is fresh again — warning
	    burst and all. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting", meta = (ClampMin = "0.0"))
	float WarningBurstResetTime = 4.0f;

	/** This enemy's rounds can hurt other enemies. Off: they pass straight through them (it
	    still holds fire with a friend in the way, either way). */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting")
	bool bFriendlyFire = false;

	// ---- Hit chance ----
	// Every shot rolls to hit. A hit goes at the chest (led); a miss is a near miss, cracking
	// past the head or into the wall beside the player. The chance is BaseHitChance × the
	// distance and player-state factors below, capped at MaxHitChance.

	/** This archetype's chance to hit per shot, at MidHitRange against a player standing still. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float BaseHitChance = 0.3f;

	/** No shot is surer than this. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MaxHitChance = 0.9f;

	/** Distance falloff (cm): ×CloseHitMultiplier within CloseHitRange, ×1 at MidHitRange,
	    ×FarHitMultiplier from FarHitRange on — straight lines in between. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float CloseHitRange = 300.0f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float CloseHitMultiplier = 2.3f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float MidHitRange = 1000.0f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float FarHitRange = 2500.0f;

	/** Farther than this (cm) from the player, an enemy doesn't take an attack token: its
	    shots are all near misses, and the token goes to someone close enough to use it. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float AttackTokenRange = 2500.0f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float FarHitMultiplier = 0.4f;

	/** A moving player: ×1 standing still, down to this at MovingSpeedForFullPenalty and up. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float MovingHitMultiplier = 0.6f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "1.0"))
	float MovingSpeedForFullPenalty = 500.0f;

	/** Mid-evasion (a shootdodge's flight; rolls later). */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float EvadingHitMultiplier = 0.1f;

	/** Down after a dive — landing, prone, getting up: the vulnerability window. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float DownHitMultiplier = 1.0f;

	/** Camping: hit chance × (1 + this × the player's camping heat) — at full heat, 1.5
	    makes every shot 2.5× as likely to land. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0"))
	float CampingHitBonus = 1.5f;

	// ---- Shot placement ----

	/** Where hits land on the player's body: bone → relative weight. Each hit picks one at
	    random by weight; bones the player's mesh lacks are skipped. Empty: the chest. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Placement")
	TMap<FName, float> HitBoneWeights;

	/** Hits land within this distance (cm) of the picked bone, so they don't all strike one spot. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Placement", meta = (ClampMin = "0.0"))
	float HitScatter = 5.0f;

	/** Near misses pass this far (cm) to one side of the chest: clear of the body... */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Placement", meta = (ClampMin = "0.0"))
	float NearMissMin = 60.0f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Placement", meta = (ClampMin = "0.0"))
	float NearMissMax = 150.0f;

	/** ...and level with it up to this far (cm) above: past the ear, over the shoulder,
	    never into the ground in front. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Placement", meta = (ClampMin = "0.0"))
	float NearMissHeight = 60.0f;

	/** Leading a moving target with projectile weapons: aims ahead by the player's velocity
	    × the round's flight time × this. 1 = perfect lead. Hits and near misses alike. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Placement", meta = (ClampMin = "0.0", ClampMax = "1.5"))
	float LeadSkill = 1.0f;

	/** This shooter's bursts against its weapon's (the weapon's AIFiring): ×1.5 fires half as
	    many shots again. Weapons that fire single shots stay single. For harder variants. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Bursts", meta = (ClampMin = "0.1"))
	float BurstShotsMultiplier = 1.0f;

	/** This shooter's pauses against its weapon's: ×0.6 waits 40% less between bursts. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Bursts", meta = (ClampMin = "0.0"))
	float BurstPauseMultiplier = 1.0f;

public:

	/** Becomes aware of the player and engages from now on; tells allies nearby after
	    AlertAlliesDelay. Does nothing if already alerted, or dead. */
	void Alert(AActor* Target);

	UFUNCTION(BlueprintPure, Category = "Enemy|Awareness")
	bool IsAlerted() const { return bAlerted; }

	UStateTree* GetBehaviour() const { return Behaviour; }

	bool HasFriendlyFire() const { return bFriendlyFire; }

	/** Picks where to go next: usually an engage spot near itself in the preferred range;
	    now and then (PushChance) a spot right up close, rushed at PushSpeed. False if
	    nowhere reachable was found. */
	bool ChooseNextSpot(FVector& OutSpot);

	/** The move is over (arrived or abandoned): back to normal speed. */
	void EndPush() { bPushingIn = false; }

	/** Its shots have been held for an ally in the way for RepositionWhenBlockedAfter. */
	bool IsLineOfFireBlocked() const { return LineOfFireBlockedTime >= RepositionWhenBlockedAfter; }

	/** A new move has started: the blocked count starts over. */
	void ClearLineOfFireBlocked() { LineOfFireBlockedTime = 0.0f; }

	/** Where the player was last seen (or heard, when alerted by a noise). */
	FVector GetLastKnownPlayerLocation() const { return LastKnownPlayerLocation; }

	float GetTimeSinceSeenPlayer() const { return TimeSinceSeenPlayer; }

	/** Heard the player's gunfire at Location while alerted: the sound becomes where they're
	    believed to be — covered and searched — until they're seen again. */
	void HearPlayer(const FVector& Location);

	/** Alerted, the player lost, and the last known spot searched out: nothing to go on. */
	bool IsLeadGone() const { return bLeadGone; }

	/** Where to roam next: the furthest Target Point (RoamToPointChance), or a random
	    reachable spot within RoamRadius. False if neither was found. */
	bool ChooseRoamSpot(FVector& OutSpot) const;

	/** Being hit alerts it — to whoever fired. */
	virtual float TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
		AController* EventInstigator, AActor* DamageCauser) override;

private:

	/** Alerted: focuses the player and raises the weapon. Otherwise lets go. */
	void UpdateAim();

	/** Raised: turn toward the aim and strafe. Lowered: turn toward travel. */
	void UpdateMovementMode();

	/** Walks the patrol points: waits at each, then moves to the next. */
	void UpdatePatrol(float DeltaSeconds);

	int32 PatrolIndex = 0;
	float PatrolWaitRemaining = 0.0f;

	/** Sight, hit chance, and the trigger. */
	void UpdateShooting(float DeltaSeconds);

	/** The player is in plain sight from this enemy's head, at AimPoint (their chest). */
	bool CanSeePlayer(const APawn* Player, const FVector& AimPoint) const;

	/** One shot at Target: a hit (scattered by HitScatter) or a near miss beside it. True if
	    it fired. */
	bool FireAt(const FVector& Target, bool bHit);

	/** A bone from HitBoneWeights, picked at random by weight. NAME_None if none apply. */
	FName PickHitBone(const USkeletalMeshComponent* PlayerMesh) const;

	int32 BurstShotsLeft = 0;
	float BurstPauseLeft = 0.0f;

	/** Seconds until the next shot of the burst (the weapon's ShotInterval). */
	float ShotIntervalLeft = 0.0f;

	/** The next burst at a seen player is a warning (all misses). */
	bool bWarningBurstPending = true;

	/** The burst under way is a warning. */
	bool bInWarningBurst = false;

	bool bAlerted = false;

	/** Who it was alerted to, to pass on to allies. */
	TWeakObjectPtr<AActor> AlertTarget;

	/** Counting down to telling allies; below 0, nothing to pass on. */
	float AlertAlliesTimeLeft = -1.0f;

	FVector LastKnownPlayerLocation = FVector::ZeroVector;
	float TimeSinceSeenPlayer = 0.0f;


	/** Nothing but the player between Eyes and Target. */
	bool HasClearShot(const FVector& Eyes, const FVector& Target, const APawn* Player) const;

	/** Best of EngageSpotSamples reachable points within SampleRadius of SampleAround, scored
	    on distance to the player (RangeMin..RangeMax), a clear shot and room from allies. */
	bool FindSpot(FVector& OutSpot, float RangeMin, float RangeMax, const FVector& SampleAround, float SampleRadius) const;

	bool bPushingIn = false;

	/** Seconds its shots have been held for an ally in the line of fire. */
	float LineOfFireBlockedTime = 0.0f;

	/** The last known spot has been searched out (see LeadGoneAfter). */
	bool bLeadGone = false;
	float TimeAtLastKnown = 0.0f;

	void AlertAllies();
};
