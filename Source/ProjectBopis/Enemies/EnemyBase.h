// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "BopisCharacterBase.h"
#include "EnemyBase.generated.h"

class AWeaponPickup;
class UStateTree;
class UBarkVoice;
enum class EBarkType : uint8;

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

	/** On being alerted, a beat before the first shot (random in range, seconds) — time for
	    the player's entrance. 0–0: fires at once. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Awareness", meta = (ClampMin = "0.0"))
	float ReactionTimeMin = 0.3f;

	UPROPERTY(EditAnywhere, Category = "Enemy|Awareness", meta = (ClampMin = "0.0"))
	float ReactionTimeMax = 0.8f;

	/** Its voice for barks (call-outs in a fight). Empty: it never speaks. A trigger spawn can
	    give it another. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Barks")
	TObjectPtr<UBarkVoice> BarkVoice;

	/** Its death is called out by the nearest ally in the fight within this (cm) who can see it. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Barks", meta = (ClampMin = "0.0"))
	float AllyDownRadius = 1500.0f;

	/** Holds an area instead of hunting (room encounters in a linear level): once alerted, it
	    only moves within HoldRadius of where it was placed, never pushes in, and never leaves
	    to search or roam — out of sight, it covers the last place it saw the player. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Hold Position")
	bool bHoldsPosition = false;

	/** How far (cm) from its placed spot a holding enemy may move. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Hold Position", meta = (ClampMin = "0.0", EditCondition = "bHoldsPosition"))
	float HoldRadius = 400.0f;

	/** A holding enemy that crouches whenever it's at its spot — waiting, and fighting from
	    the crouch — and stands only to move within its area. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Hold Position", meta = (EditCondition = "bHoldsPosition"))
	bool bCrouchWhileHolding = false;

	/** Where it goes the moment its trigger fires: out of its room, round the corner. A holder
	    then holds there. None: it starts from where it stands. */
	UPROPERTY(EditInstanceOnly, Category = "Enemy|Behaviour|Ambush")
	TObjectPtr<AActor> AmbushPoint;

	/** Set off by its trigger (and no AmbushPoint), its first move is a charge straight at the player. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Ambush")
	bool bRushOnTrigger = false;

	/** How close (cm) to its AmbushPoint counts as arrived, measured to its centre: 0–30 puts it
	    right on the point. Every other move uses the StateTree move's own radius. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour|Ambush", meta = (ClampMin = "0.0"))
	float AmbushAcceptanceRadius = 20.0f;

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

	/** Seconds out of sight before the gun comes down and it searches in the lowered stance:
	    jogging, turned to where it's going, its head toward the last known spot. Seeing the
	    player again raises it, after a reaction beat. 0: never lowers. Holders keep theirs up. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Awareness", meta = (ClampMin = "0.0"))
	float LowerGunAfter = 4.0f;

	/** Lowered and searching, it looks toward the last known spot only while further from it
	    than this (cm), so it doesn't stare at its own feet once there. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Awareness", meta = (ClampMin = "0.0"))
	float HeadLookMinDistance = 300.0f;

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

	/** A miss carries on past the player: this far beyond him (cm) its own path is checked for
	    allies too, and it's sent past his other side, or held, if one is on it. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Behaviour", meta = (ClampMin = "0.0"))
	float MissCarryDistance = 1500.0f;

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

	/** Max walk speed while patrolling (not alerted, with PatrolPoints): a walk, not a jog. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Movement", meta = (ClampMin = "0.0"))
	float PatrolSpeed = 180.0f;

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
	float BaseHitChance = 0.12f;

	/** No shot is surer than this. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MaxHitChance = 0.5f;

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

	/** Hit chance against a player at full camping heat — reached over CampTimeToFullHeat
	    from the normal chance. 1: a target that won't move gets hit. The player's moving
	    or evading still scales it down. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Shooting|Hit Chance", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float CampedHitChance = 1.0f;

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

	/** Puts a just-spawned enemy to sleep in an encounter's reserve: hidden, no collision,
	    nothing ticking, its gun hidden too, and no alerts reach it. It has no AI yet (the
	    director spawns it without a controller); Wake brings it into play. */
	void Sleep();

	/** Brings a sleeping enemy into play at Where: shown, colliding and ticking again, its
	    hold area centred there, and its AI controller spawned (which starts its behaviour). */
	void Wake(const FTransform& Where);

	bool IsAsleep() const { return bAsleep; }

	/** Asleep, it stays hidden whoever asks: the Character Customizer shows its character once
	    the outfit has loaded, which would otherwise show a sleeper where it waits. */
	virtual void SetActorHiddenInGame(bool bNewHidden) override;

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

	bool HoldsPosition() const { return bHoldsPosition; }

	/** Waiting in ambush for its encounter trigger: blind and deaf to the player (and to allies'
	    alerts) until the trigger sets it off. Being shot still wakes it. Set by AEncounterTrigger. */
	void SetWaitingForTrigger(bool bWait) { bWaitingForTrigger = bWait; }

	/** Settings for an enemy spawned by a trigger (placed ones are set in the level). */
	void SetAmbush(AActor* Point, bool bRush, float AcceptanceRadius)
	{
		AmbushPoint = Point;
		bRushOnTrigger = bRush;
		AmbushAcceptanceRadius = AcceptanceRadius;
	}

	/** The move just chosen is the trip to the AmbushPoint: its arrival radius (centre-measured).
	    False for any other move. Asking clears it. */
	bool ConsumeAmbushAcceptance(float& OutRadius)
	{
		if (PendingAmbushAcceptance < 0.0f)
		{
			return false;
		}
		OutRadius = PendingAmbushAcceptance;
		PendingAmbushAcceptance = -1.0f;
		return true;
	}

	void SetHold(bool bHold, float Radius, bool bCrouch)
	{
		bHoldsPosition = bHold;
		HoldRadius = Radius;
		bCrouchWhileHolding = bCrouch;
	}

	void SetPatrolPoints(const TArray<TObjectPtr<AActor>>& Points) { PatrolPoints = Points; }

	void SetBarkVoice(UBarkVoice* Voice);

	/** Its own pitch for every line it says, handed out once by the bark subsystem. */
	float GetVoicePitch() const { return VoicePitch; }

	/** A scripted event walks (or runs) it to Target while it's calm; patrolling waits until the
	    event lets it go (EndScripted). False if it can't (alerted, dead, no path). */
	bool ScriptedMoveTo(AActor* Target, bool bRun, float AcceptanceRadius);

	/** The scripted move is over: arrived, or given up. */
	bool IsScriptedMoveDone() const;

	/** A scripted event turns it toward where Target is now (body, then head), and it keeps
	    facing that spot while calm and standing, even if Target moves off. None: stops. */
	void SetFaceTarget(AActor* Target);

	/** The event is over: back to its own business (patrolling, standing). */
	void EndScripted();

	/** Calls out, if the level's bark coordinator lets it through (UBarkSubsystem). */
	bool Bark(EBarkType Type);

	/** For the editor's link lines. */
	AActor* GetAmbushPoint() const { return AmbushPoint; }
	const TArray<TObjectPtr<AActor>>& GetPatrolPoints() const { return PatrolPoints; }

	/** A move couldn't be made (no path): says so in the log, at most every few seconds, so a
	    hole in the NavMesh shows up instead of an enemy silently standing still. */
	void ReportUnreachable(const FVector& Destination);

	/** Set off by its encounter trigger: wakes, alerts, and makes its ambush move first. */
	void TriggerAmbush(AActor* Target);

	virtual bool GetHeadLookTarget(FVector& OutLocation) const override;

	/** Where to roam next: the furthest Target Point (RoamToPointChance), or a random
	    reachable spot within RoamRadius. False if neither was found. */
	bool ChooseRoamSpot(FVector& OutSpot) const;

	/** Being hit alerts it — to whoever fired. */
	virtual float TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
		AController* EventInstigator, AActor* DamageCauser) override;

private:

	/** Alerted: focuses the player and raises the weapon. Otherwise lets go. */
	void UpdateAim();

	/** Has the nearest ally who saw it die call it out. */
	void BarkAllyDown();

	/** Raised: turn toward the aim and strafe. Lowered: turn toward travel. */
	void UpdateMovementMode();

	/** Crouched while holding a spot (bCrouchWhileHolding), standing to move. */
	void UpdateCrouch();

	/** Walks the patrol points: waits at each, then moves to the next. */
	void UpdatePatrol(float DeltaSeconds);

	/** Calm and standing, with a FaceTarget: turns to it. */
	void UpdateFacing(float DeltaSeconds);

	/** In a scripted event's hands: a Move To, so it doesn't patrol off. */
	bool bScriptedMove = false;
	bool bScriptedRun = false;

	/** Where a scripted event has it facing: the spot, and the height its eyes rest at. */
	bool bHasFacePoint = false;
	FVector FacePoint = FVector::ZeroVector;

	int32 PatrolIndex = 0;
	float PatrolWaitRemaining = 0.0f;

	/** Sight, hit chance, and the trigger. */
	void UpdateShooting(float DeltaSeconds);

	/** The player is in plain sight from this enemy's head, at AimPoint (their chest). */
	bool CanSeePlayer(const APawn* Player, const FVector& AimPoint) const;

	/** One shot at Target: a hit (scattered by HitScatter) or a near miss beside it. True if
	    it fired. */
	bool FireAt(const FVector& Target, bool bHit);

	/** A live ally within LineOfFireRadius of the line From → To. */
	bool IsAllyAlong(const FVector& From, const FVector& To) const;

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

	/** Seen the player since being alerted. Suppressing fire needs a sighting to lose; an alert
	    from a sound (or an ally, or the level) is searched, not shot at. */
	bool bSeenSinceAlert = false;

	/** This sighting has been called out ("there he is"): once per alert, and again after
	    losing the player long enough for a fresh engagement. */
	bool bSightingCalled = false;

	/** Gets VoicePitch from the bark subsystem (1 without a voice). */
	void RollVoicePitch();
	float VoicePitch = 1.0f;

	bool bWaitingForTrigger = false;

	/** The trigger has fired and the ambush move (AmbushPoint or charge) hasn't been made yet. */
	bool bAmbushMovePending = false;

	/** Set when ChooseNextSpot picks the AmbushPoint; read once by the move task. Below 0: none. */
	float PendingAmbushAcceptance = -1.0f;

	/** World time of the last unreachable-move warning (ReportUnreachable). */
	float LastUnreachableReportTime = -1000.0f;


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

	/** Where it was placed: the centre of its hold area. */
	FVector HomeLocation = FVector::ZeroVector;

	/** Asleep in an encounter's reserve (see Sleep). */
	bool bAsleep = false;

	/** The components that were ticking when it fell asleep, restarted on waking. */
	TArray<TWeakObjectPtr<UActorComponent>> SleepingTickers;

	/** Seconds left of the reaction beat after being alerted. */
	float ReactionTimeLeft = 0.0f;

	/** The gun is down from searching too long (LowerGunAfter): raising it again costs a reaction beat. */
	bool bGunLowered = false;
	float TimeAtLastKnown = 0.0f;

	void AlertAllies();
};
