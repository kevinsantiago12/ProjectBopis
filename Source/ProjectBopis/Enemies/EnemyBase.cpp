// Copyright Epic Games, Inc. All Rights Reserved.

#include "Enemies/EnemyBase.h"
#include "Enemies/BopisAIController.h"
#include "Enemies/BarkSubsystem.h"
#include "AIController.h"
#include "BrainComponent.h"
#include "EngineUtils.h"
#include "Engine/TargetPoint.h"
#include "NavigationSystem.h"
#include "Components/CapsuleComponent.h"
#include "Navigation/PathFollowingComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "ProjectBopis.h"
#include "ProjectBopisGameMode.h"
#include "Pickups/WeaponDrop.h"
#include "Pickups/WeaponPickup.h"
#include "Weapons/WeaponHolderComponent.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/FocusComponent.h"
#include "Gameplay/ShootdodgeComponent.h"
#include "Weapons/WeaponBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"

AEnemyBase::AEnemyBase()
{
	// Possessed whether placed in the level or spawned at runtime — without this an
	// enemy dropped into the level has no controller, and nothing can ever move it.
	AIControllerClass = ABopisAIController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	// The movement component turns the body (see UpdateMovementMode); the controller
	// never snaps it directly.
	bUseControllerRotationYaw = false;

	// Mostly the torso, sometimes a limb, rarely the head.
	HitBoneWeights.Add(TEXT("spine_03"), 25.0f);
	HitBoneWeights.Add(TEXT("spine_05"), 20.0f);
	HitBoneWeights.Add(TEXT("pelvis"), 15.0f);
	HitBoneWeights.Add(TEXT("upperarm_l"), 4.0f);
	HitBoneWeights.Add(TEXT("upperarm_r"), 4.0f);
	HitBoneWeights.Add(TEXT("lowerarm_l"), 3.5f);
	HitBoneWeights.Add(TEXT("lowerarm_r"), 3.5f);
	HitBoneWeights.Add(TEXT("thigh_l"), 6.0f);
	HitBoneWeights.Add(TEXT("thigh_r"), 6.0f);
	HitBoneWeights.Add(TEXT("calf_l"), 4.0f);
	HitBoneWeights.Add(TEXT("calf_r"), 4.0f);
	HitBoneWeights.Add(TEXT("head"), 5.0f);

	// Enemies may crouch (holding a spot crouched, see bCrouchWhileHolding).
	GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch = true;
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

	// Passing the word on, once the delay is up.
	if (AlertAlliesTimeLeft >= 0.0f)
	{
		AlertAlliesTimeLeft -= DeltaSeconds;
		if (AlertAlliesTimeLeft < 0.0f)
		{
			AlertAllies();
		}
	}

	UpdateAim();
	UpdateMovementMode();
	UpdateCrouch();
	UpdatePatrol(DeltaSeconds);
	UpdateFacing(DeltaSeconds);
	UpdateShooting(DeltaSeconds);
}

void AEnemyBase::BeginPlay()
{
	Super::BeginPlay();

	HomeLocation = GetActorLocation();

	if (bStartAlerted)
	{
		Alert(UGameplayStatics::GetPlayerPawn(this, 0));
	}
}

void AEnemyBase::UpdateShooting(float DeltaSeconds)
{
	APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Player)
	{
		return;
	}

	// Aimed at the chest; the capsule centre would be the hips, and low when they dive.
	// The character's own body mesh — not just any skeletal mesh on it (modular characters have several).
	const ACharacter* PlayerCharacter = Cast<ACharacter>(Player);
	const USkeletalMeshComponent* PlayerMesh = PlayerCharacter ? PlayerCharacter->GetMesh() : nullptr;
	const FVector AimPoint = (PlayerMesh && PlayerMesh->DoesSocketExist(TEXT("spine_03")))
		? PlayerMesh->GetSocketLocation(TEXT("spine_03"))
		: Player->GetActorLocation();
	// A dead player is out of sight as far as shooting goes: no more rounds into the body.
	const ABopisCharacterBase* PlayerBody = Cast<ABopisCharacterBase>(Player);
	const bool bSeesPlayer = bAlerted && !(PlayerBody && PlayerBody->IsDead()) && CanSeePlayer(Player, AimPoint);

	// Memory, for searching: where it last laid eyes on them, and how long ago.
	if (bSeesPlayer)
	{
		LastKnownPlayerLocation = Player->GetActorLocation();
		TimeSinceSeenPlayer = 0.0f;
		// First sight of them: call it out.
		if (!bSightingCalled)
		{
			bSightingCalled = true;
			Bark(EBarkType::Spotted);
		}
		bSeenSinceAlert = true;
		bLeadGone = false;
		TimeAtLastKnown = 0.0f;
	}
	else
	{
		TimeSinceSeenPlayer += DeltaSeconds;

		// Lost them long enough: finding them again is a fresh engagement.
		if (TimeSinceSeenPlayer >= WarningBurstResetTime)
		{
			// Lost them for good: a taunt (once, and only if he'd actually seen them).
			if (bSightingCalled && !(PlayerBody && PlayerBody->IsDead()))
			{
				Bark(EBarkType::LostSight);
			}
			bSightingCalled = false;
			bWarningBurstPending = true;
		}
	}

	// A lead goes cold: standing at the last known spot a while without finding them.
	if (bAlerted && !bSeesPlayer && !bLeadGone
		&& FVector::Dist2D(GetActorLocation(), LastKnownPlayerLocation) < 250.0f)
	{
		TimeAtLastKnown += DeltaSeconds;
		bLeadGone = TimeAtLastKnown >= LeadGoneAfter;
	}

	// What the player is doing, for the hit chance.
	const AProjectBopisCharacter* PlayerHero = Cast<AProjectBopisCharacter>(Player);
	const UShootdodgeComponent* PlayerDodge = PlayerHero ? PlayerHero->GetShootdodge() : nullptr;
	const bool bPlayerEvading = PlayerHero && PlayerHero->IsEvading();
	const bool bPlayerDown = PlayerDodge
		&& ((PlayerDodge->IsBodyDown() && !PlayerDodge->IsAirborne()) || PlayerDodge->IsGettingUp());
	const float PlayerSpeed = Player->GetVelocity().Size2D();

	// Distance: surer up close, worse far out.
	const float Distance = FVector::Dist(GetActorLocation(), AimPoint);
	const float DistanceFactor = Distance <= MidHitRange
		? FMath::GetMappedRangeValueClamped(FVector2D(CloseHitRange, MidHitRange), FVector2D(CloseHitMultiplier, 1.0f), Distance)
		: FMath::GetMappedRangeValueClamped(FVector2D(MidHitRange, FarHitRange), FVector2D(1.0f, FarHitMultiplier), Distance);

	// The player's state: diving beats everything, lying down (and getting up) is the
	// vulnerability window, otherwise the faster they move the harder they are to hit.
	const float StateFactor = bPlayerEvading ? EvadingHitMultiplier
		: bPlayerDown ? DownHitMultiplier
		: FMath::Lerp(1.0f, MovingHitMultiplier, FMath::Clamp(PlayerSpeed / MovingSpeedForFullPenalty, 0.0f, 1.0f));

	// Within the cap, by distance; then camping: the longer the player stays put, the surer
	// the shot, climbing to CampedHitChance at full heat — a target that won't move gets
	// hit. The player's state comes last, so moving or diving out of it still counts.
	const float NormalChance = FMath::Min(MaxHitChance, BaseHitChance * DistanceFactor);
	const float Heat = PlayerHero ? PlayerHero->GetCampingHeat() : 0.0f;
	const float HitChance = FMath::Lerp(NormalChance, FMath::Max(NormalChance, CampedHitChance), Heat) * StateFactor;

	// The trigger: the player in sight — or only just lost, while it keeps firing at where
	// they went (SuppressFireDuration) — and the gun up and ready. A sound alone is searched,
	// not shot at.
	const bool bSuppressing = bAlerted && bSeenSinceAlert && !bSeesPlayer && TimeSinceSeenPlayer <= SuppressFireDuration;
	UWeaponHolderComponent* Holder = GetWeaponHolder();
	AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr;

	// Just alerted: a beat to react before the first shot. It still turns and tracks meanwhile.
	if (ReactionTimeLeft > 0.0f)
	{
		ReactionTimeLeft -= DeltaSeconds;
		return;
	}

	if (!bShootAtPlayer || !bAlerted || !(bSeesPlayer || bSuppressing) || !Weapon || !IsWeaponRaised()
		|| IsEquipAnimating() || Weapon->IsReloading())
	{
		return;
	}

	// Bursts in the weapon's own pattern, as this shooter fires it: a burst at the weapon's
	// spacing, then a pause.
	const FAIFiringPattern& Pattern = Weapon->GetAIFiring();
	if (BurstPauseLeft > 0.0f)
	{
		BurstPauseLeft -= DeltaSeconds;
		return;
	}
	if (ShotIntervalLeft > 0.0f)
	{
		ShotIntervalLeft -= DeltaSeconds;
		return;
	}
	if (BurstShotsLeft <= 0)
	{
		const int32 Shots = FMath::RandRange(Pattern.BurstShotsMin, FMath::Max(Pattern.BurstShotsMin, Pattern.BurstShotsMax));
		// A tougher shooter holds the trigger down longer; a single-shot weapon stays single.
		BurstShotsLeft = Pattern.BurstShotsMax > 1 ? FMath::Max(1, FMath::RoundToInt(Shots * BurstShotsMultiplier)) : 1;

		// A fresh engagement opens with a warning: this whole burst misses. A burst fired
		// blind (suppressing) doesn't use the warning up.
		bInWarningBurst = bWarningBurst && bWarningBurstPending && bSeesPlayer;
		if (bInWarningBurst)
		{
			bWarningBurstPending = false;
		}
	}

	// Out of rounds: reload if there's reserve, otherwise just top up — enemies don't run dry.
	if (Weapon->GetAmmoInMagazine() <= 0)
	{
		if (Holder->ReloadEquippedWeapon())
		{
			PlayReloadAnimation(Weapon);
			Bark(EBarkType::Reloading);
		}
		else
		{
			Weapon->SetAmmoInMagazine(Weapon->GetMagazineSize());
		}
		return;
	}

	// Each shot rolls to hit. In sight: a hit goes at a body part picked by HitBoneWeights,
	// a miss cracks past the chest — both led, since a round takes time to arrive (hitscan
	// needs none). Suppressing: near misses around where they were last seen.
	const bool bInHitGrace = PlayerHero && PlayerHero->IsInHitGrace();
	const bool bHit = bSeesPlayer && !bInWarningBurst && !bInHitGrace
		&& FMath::FRand() < HitChance;
	FVector Target = LastKnownPlayerLocation + FVector(0.0f, 0.0f, 40.0f);
	if (bSeesPlayer)
	{
		const FName HitBone = bHit ? PickHitBone(PlayerMesh) : NAME_None;
		Target = HitBone != NAME_None ? PlayerMesh->GetSocketLocation(HitBone) : AimPoint;
		if (const float RoundSpeed = Weapon->GetProjectileSpeed(); RoundSpeed > 0.0f)
		{
			const float FlightTime = FVector::Dist(Weapon->GetMuzzleLocation(), Target) / RoundSpeed;
			Target += Player->GetVelocity() * (FlightTime * LeadSkill);
		}
	}

	if (Weapon->CanFire() && FireAt(Target, bHit))
	{
		if (--BurstShotsLeft <= 0)
		{
			BurstPauseLeft = FMath::FRandRange(Pattern.BurstPauseMin, FMath::Max(Pattern.BurstPauseMin, Pattern.BurstPauseMax))
				* BurstPauseMultiplier;
		}
		else
		{
			ShotIntervalLeft = Pattern.ShotInterval;
		}
	}
}

bool AEnemyBase::CanSeePlayer(const APawn* Player, const FVector& AimPoint) const
{
	// From the head to the player's chest; anything else in the way (cover, walls, other
	// enemies) blocks the view. The player's capsule ignores this channel, their mesh doesn't.
	const FVector Eyes = GetMesh()->DoesSocketExist(TEXT("head"))
		? GetMesh()->GetSocketLocation(TEXT("head"))
		: GetPawnViewLocation();
	return HasClearShot(Eyes, AimPoint, Player);
}

bool AEnemyBase::HasClearShot(const FVector& Eyes, const FVector& Target, const APawn* Player) const
{
	FCollisionQueryParams Params(SCENE_QUERY_STAT(EnemySight), false, this);
	if (const UWeaponHolderComponent* Holder = GetWeaponHolder(); Holder && Holder->GetEquippedWeapon())
	{
		Params.AddIgnoredActor(Holder->GetEquippedWeapon());
	}

	// Allies don't block the view — it sees past a friend (it just won't shoot through him,
	// see FireAt). Their guns, held out in front, don't either.
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		Params.AddIgnoredActor(*It);
		if (const UWeaponHolderComponent* AllyHolder = It->GetWeaponHolder(); AllyHolder && AllyHolder->GetEquippedWeapon())
		{
			Params.AddIgnoredActor(AllyHolder->GetEquippedWeapon());
		}
	}

	FHitResult Hit;
	if (!GetWorld()->LineTraceSingleByChannel(Hit, Eyes, Target, ECC_Visibility, Params))
	{
		return true;
	}
	return Hit.GetActor() == Player;
}

bool AEnemyBase::ChooseNextSpot(FVector& OutSpot)
{
	// Set off by its trigger: the first move is the ambush's — out to its point, or a charge.
	if (bAmbushMovePending)
	{
		bAmbushMovePending = false;
		if (AmbushPoint)
		{
			OutSpot = AmbushPoint->GetActorLocation();
			HomeLocation = OutSpot;
			bPushingIn = false;
			PendingAmbushAcceptance = AmbushAcceptanceRadius;
			return true;
		}
		if (bRushOnTrigger && FindSpot(OutSpot, PushRangeMin, PushRangeMax, LastKnownPlayerLocation, PushRangeMax))
		{
			bPushingIn = true;
			return true;
		}
	}

	// Holding an area: a new spot within reach of its post, never a rush.
	if (bHoldsPosition)
	{
		bPushingIn = false;
		return FindSpot(OutSpot, PreferredRangeMin, PreferredRangeMax, HomeLocation, HoldRadius);
	}

	// Now and then, at random, it rushes in: somewhere right up close to where it believes
	// the player is. Not tactics — a mook charging is a target for a stylish kill.
	bPushingIn = FMath::FRand() < PushChance
		&& FindSpot(OutSpot, PushRangeMin, PushRangeMax, LastKnownPlayerLocation, PushRangeMax);
	if (bPushingIn)
	{
		return true;
	}
	return FindSpot(OutSpot, PreferredRangeMin, PreferredRangeMax, GetActorLocation(), RepositionRadius);
}

bool AEnemyBase::FindSpot(FVector& OutSpot, float RangeMin, float RangeMax, const FVector& SampleAround, float SampleRadius) const
{
	const UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	const APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Nav || !Player)
	{
		return false;
	}

	// Judged against where it believes the player is; chest height for the line of fire.
	const FVector PlayerSpot = LastKnownPlayerLocation;
	const FVector PlayerChest = PlayerSpot + FVector(0.0f, 0.0f, 40.0f);
	const float EyesAboveFloor = GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + BaseEyeHeight;

	float BestScore = -MAX_flt;
	bool bFound = false;
	for (int32 Sample = 0; Sample < EngageSpotSamples; ++Sample)
	{
		FNavLocation Candidate;
		if (!Nav->GetRandomReachablePointInRadius(SampleAround, SampleRadius, Candidate))
		{
			continue;
		}
		const FVector Spot = Candidate.Location;

		// Outside the range costs a point per cm; a clear shot is worth 10 m of
		// that; each ally crowding the spot costs 5 m.
		const float Range = FVector::Dist2D(Spot, PlayerSpot);
		float Score = -FMath::Max(0.0f, RangeMin - Range) - FMath::Max(0.0f, Range - RangeMax);
		if (HasClearShot(Spot + FVector(0.0f, 0.0f, EyesAboveFloor), PlayerChest, Player))
		{
			Score += 1000.0f;
		}
		for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
		{
			if (*It != this && !It->IsDead() && FVector::Dist2D(It->GetActorLocation(), Spot) < AllySpacing)
			{
				Score -= 500.0f;
			}
		}

		if (Score > BestScore)
		{
			BestScore = Score;
			OutSpot = Spot;
			bFound = true;
		}
	}
	return bFound;
}

FName AEnemyBase::PickHitBone(const USkeletalMeshComponent* PlayerMesh) const
{
	if (!PlayerMesh)
	{
		return NAME_None;
	}

	// A weighted draw over the bones this mesh actually has.
	float Total = 0.0f;
	for (const TPair<FName, float>& Entry : HitBoneWeights)
	{
		if (Entry.Value > 0.0f && PlayerMesh->DoesSocketExist(Entry.Key))
		{
			Total += Entry.Value;
		}
	}

	float Roll = FMath::FRand() * Total;
	for (const TPair<FName, float>& Entry : HitBoneWeights)
	{
		if (Entry.Value > 0.0f && PlayerMesh->DoesSocketExist(Entry.Key))
		{
			Roll -= Entry.Value;
			if (Roll <= 0.0f)
			{
				return Entry.Key;
			}
		}
	}
	return NAME_None;
}

bool AEnemyBase::FireAt(const FVector& Target, bool bHit)
{
	if (IsWeaponBlocked())
	{
		return false;
	}
	AWeaponBase* Weapon = GetWeaponHolder()->GetEquippedWeapon();
	const FVector Muzzle = Weapon->GetMuzzleLocation();
	const FVector Aim = (Target - Muzzle).GetSafeNormal();

	FVector Right = FVector::CrossProduct(Aim, FVector::UpVector).GetSafeNormal();
	if (Right.IsZero())
	{
		Right = FVector::RightVector;
	}
	const FVector Up = FVector::CrossProduct(Right, Aim);

	// Where the round passes the target: on it for a hit; for a miss, off to one side clear
	// of the body, level or high — past the ear, over the shoulder.
	FVector Offset;
	if (bHit)
	{
		Offset = FMath::VRand() * FMath::FRandRange(0.0f, HitScatter);
	}
	else
	{
		const float Side = FMath::FRandRange(NearMissMin, FMath::Max(NearMissMin, NearMissMax));
		Offset = Right * (FMath::RandBool() ? Side : -Side)
			+ Up * (FMath::FRandRange(-0.25f, 1.0f) * NearMissHeight);
	}
	const FVector Direction = (Target + Offset - Muzzle).GetSafeNormal();

	// Never through a friend: if a live ally's body is in the tube from the muzzle to the
	// player (LineOfFireRadius wide), hold every shot — hit or near miss — and try again next
	// tick; the burst isn't used up. Pawn bodies only: an ally's gun, held out in front,
	// mustn't hide the ally behind it.
	{
		FCollisionQueryParams Params(SCENE_QUERY_STAT(EnemyLineOfFire), false, this);
		// To the player (the point this shot is built around), not the round's own path: a
		// near miss offset past a friend is still firing through him.
		const FVector End = Target;
		TArray<FHitResult> Hits;
		GetWorld()->SweepMultiByObjectType(Hits, Muzzle, End, FQuat::Identity,
			FCollisionObjectQueryParams(ECC_Pawn), FCollisionShape::MakeSphere(LineOfFireRadius), Params);

		const bool bAllyInTheWay = Hits.ContainsByPredicate([](const FHitResult& Hit)
		{
			const AEnemyBase* Ally = Cast<AEnemyBase>(Hit.GetActor());
			return Ally && !Ally->IsDead();
		});

		if (bAllyInTheWay)
		{
			LineOfFireBlockedTime += GetWorld()->GetDeltaSeconds();
			return false;
		}
	}

	// Exact: the shot is placed already, so the gun's own bloom stays out of it.
	if (Weapon->Fire(Muzzle, Direction, true) != EFireResult::Fired)
	{
		return false;
	}
	PlayFireAnimation(Weapon);
	LineOfFireBlockedTime = 0.0f;
	return true;
}

void AEnemyBase::Die(AController* Killer, const FVector& ShotDirection)
{
	Super::Die(Killer, ShotDirection);

	Bark(EBarkType::Death);
	BarkAllyDown();

	DropWeapon(ShotDirection);

	// Stop the StateTree while it can still see its pawn: unpossessing first would stop it
	// with the pawn gone, and it warns ("Context Requirements … failed") on every death.
	if (const AAIController* AIController = Cast<AAIController>(GetController()))
	{
		if (UBrainComponent* Brain = AIController->GetBrainComponent())
		{
			Brain->StopLogic(TEXT("Died"));
		}
	}

	// The brain goes with the body: unpossess, and the AI controller is destroyed.
	DetachFromControllerPendingDestroy();

	// Counted toward the corpse limit; the oldest body goes once there are too many.
	if (AProjectBopisGameMode* GameMode = GetWorld()->GetAuthGameMode<AProjectBopisGameMode>())
	{
		GameMode->RegisterCorpse(this);
	}

	// A kill by the player tops up their Focus meter.
	const APawn* KillerPawn = Killer ? Killer->GetPawn() : nullptr;
	if (const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(KillerPawn))
	{
		if (UFocusComponent* Focus = Player->GetFocus())
		{
			Focus->AddMeter(Focus->KillRefill);
		}
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
	Drop->Launch(Weapon->GetDropClass(), WeaponPickupClass, Velocity, FMath::VRand() * WeaponDropSpin);

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

	APawn* Player = bAlerted ? UGameplayStatics::GetPlayerPawn(this, 0) : nullptr;
	if (!Player)
	{
		// With no focus, the controller follows the body's facing, so the aim offset rests at zero.
		AI->ClearFocus(EAIFocusPriority::Gameplay);
		SetAiming(bStartRaised);
		return;
	}

	// Out of sight long enough, and searching rather than holding a spot: the gun comes down.
	// The lowered stance turns the body to where it's going; the head does the looking.
	if (LowerGunAfter > 0.0f && !bHoldsPosition && TimeSinceSeenPlayer >= LowerGunAfter)
	{
		bGunLowered = true;
		SetAiming(false);
		AI->ClearFocus(EAIFocusPriority::Gameplay);
		return;
	}
	if (bGunLowered)
	{
		// Coming back up: a beat to react before it fires, as when first alerted.
		bGunLowered = false;
		ReactionTimeLeft = FMath::FRandRange(ReactionTimeMin, FMath::Max(ReactionTimeMin, ReactionTimeMax));
	}

	SetAiming(true);
	if (TimeSinceSeenPlayer <= TrackThroughCoverTime)
	{
		// In sight (or only just lost): track them. Focus drives the control rotation, pitch
		// included when the focus is a pawn, so the aim offset follows with no extra work.
		AI->SetFocus(Player);
	}
	else if (bLeadGone)
	{
		// Nothing to go on (roaming): look where it's going, gun still up.
		AI->ClearFocus(EAIFocusPriority::Gameplay);
	}
	else if (FVector::Dist2D(GetActorLocation(), LastKnownPlayerLocation) > 200.0f)
	{
		// Out of sight: covers where they were last seen, not where they are now.
		AI->SetFocalPoint(LastKnownPlayerLocation + FVector(0.0f, 0.0f, 40.0f));
	}
	else
	{
		// Standing on the spot itself (searching): look where it's going instead.
		AI->ClearFocus(EAIFocusPriority::Gameplay);
	}
}

bool AEnemyBase::GetHeadLookTarget(FVector& OutLocation) const
{
	// In a scripted event, calm: eyes on the spot it's been turned to face.
	if (!bAlerted && !IsDead() && bHasFacePoint)
	{
		OutLocation = FacePoint;
		return true;
	}

	// Searching with the gun down: eyes on where the player was last seen, until it gets there.
	// Roaming with nothing to go on, it looks where it's going.
	if (!bAlerted || IsDead() || IsWeaponRaised() || bLeadGone
		|| FVector::Dist2D(GetActorLocation(), LastKnownPlayerLocation) < HeadLookMinDistance)
	{
		return false;
	}

	// The last known spot is their capsule centre; up to head height.
	OutLocation = LastKnownPlayerLocation + FVector(0.0f, 0.0f, 60.0f);
	return true;
}

void AEnemyBase::UpdateCrouch()
{
	// Down whenever it's holding its spot; up to move — a crouched body moves slowly, and
	// a move between spots should read as a dash between covers.
	const AAIController* AI = Cast<AAIController>(GetController());
	const bool bMoving = AI && AI->GetMoveStatus() == EPathFollowingStatus::Moving;
	const bool bWantsCrouch = bHoldsPosition && bCrouchWhileHolding && !bMoving;

	if (bWantsCrouch && !bIsCrouched)
	{
		Crouch();
	}
	else if (!bWantsCrouch && bIsCrouched)
	{
		UnCrouch();
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
	const bool bPatrolling = !bAlerted && PatrolPoints.Num() > 0;
	Movement->MaxWalkSpeed = bPushingIn ? PushSpeed
		: bRaised ? RaisedSpeed
		: bScriptedMove ? (bScriptedRun ? LoweredSpeed : PatrolSpeed)
		: bPatrolling ? PatrolSpeed
		: LoweredSpeed;
}

void AEnemyBase::BarkAllyDown()
{
	AEnemyBase* Witness = nullptr;
	float Nearest = AllyDownRadius;
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		AEnemyBase* Ally = *It;
		const float Distance = FVector::Dist(Ally->GetActorLocation(), GetActorLocation());
		if (Ally == this || Ally->IsDead() || !Ally->IsAlerted() || Distance > Nearest)
		{
			continue;
		}
		// Saw it: nothing between their eyes.
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(AllyDownSight), false, this);
		Params.AddIgnoredActor(Ally);
		if (!GetWorld()->LineTraceSingleByChannel(Hit, Ally->GetPawnViewLocation(), GetPawnViewLocation(),
			ECC_Visibility, Params))
		{
			Witness = Ally;
			Nearest = Distance;
		}
	}
	if (Witness)
	{
		Witness->Bark(EBarkType::AllyDown);
	}
}

bool AEnemyBase::Bark(EBarkType Type)
{
	UWorld* World = GetWorld();
	UBarkSubsystem* Barks = World ? World->GetSubsystem<UBarkSubsystem>() : nullptr;
	return Barks && BarkVoice && Barks->TryBark(this, BarkVoice, Type);
}

void AEnemyBase::ReportUnreachable(const FVector& Destination)
{
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now - LastUnreachableReportTime < 3.0f)
	{
		return;
	}
	LastUnreachableReportTime = Now;
	UE_LOG(LogProjectBopis, Warning, TEXT("%s can't reach %s from %s: no path. Is the NavMesh (P in the editor) covering both?"),
		*GetName(), *Destination.ToCompactString(), *GetActorLocation().ToCompactString());
}

void AEnemyBase::UpdatePatrol(float DeltaSeconds)
{
	AAIController* AI = Cast<AAIController>(GetController());
	if (!AI || PatrolPoints.Num() == 0 || bAlerted || bScriptedMove)
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

bool AEnemyBase::ScriptedMoveTo(AActor* Target, bool bRun, float AcceptanceRadius)
{
	AAIController* AI = Cast<AAIController>(GetController());
	if (!AI || !Target || bAlerted || IsDead())
	{
		return false;
	}
	// Walking: faces where it's going, not what it was looking at.
	bHasFacePoint = false;
	bScriptedMove = true;
	bScriptedRun = bRun;
	if (AI->MoveToActor(Target, AcceptanceRadius) == EPathFollowingRequestResult::Failed)
	{
		ReportUnreachable(Target->GetActorLocation());
		bScriptedMove = false;
		return false;
	}
	return true;
}

bool AEnemyBase::IsScriptedMoveDone() const
{
	const AAIController* AI = Cast<AAIController>(GetController());
	return !AI || bAlerted || IsDead() || AI->GetMoveStatus() == EPathFollowingStatus::Idle;
}

void AEnemyBase::EndScripted()
{
	bScriptedMove = false;
	bScriptedRun = false;
	bHasFacePoint = false;
}

void AEnemyBase::SetFaceTarget(AActor* Target)
{
	bHasFacePoint = Target != nullptr;
	if (!Target)
	{
		return;
	}
	// The spot it's at now, at its eye height (a pawn) or ours (a point on the floor).
	const APawn* FacePawn = Cast<APawn>(Target);
	FacePoint = FacePawn ? FacePawn->GetPawnViewLocation()
		: FVector(Target->GetActorLocation().X, Target->GetActorLocation().Y, GetPawnViewLocation().Z);
}

void AEnemyBase::UpdateFacing(float DeltaSeconds)
{
	const AAIController* AI = Cast<AAIController>(GetController());
	if (!bHasFacePoint || bAlerted || !AI || AI->GetMoveStatus() == EPathFollowingStatus::Moving)
	{
		return;
	}
	const FVector ToFace = FacePoint - GetActorLocation();
	if (ToFace.SizeSquared2D() < 1.0f)
	{
		return;
	}
	// Standing, so the movement component isn't turning it: a steady turn, half the combat rate.
	const FRotator Wanted(0.0f, ToFace.Rotation().Yaw, 0.0f);
	SetActorRotation(FMath::RInterpConstantTo(GetActorRotation(), Wanted, DeltaSeconds, TurnRate * 0.5f));
}

void AEnemyBase::Alert(AActor* Target)
{
	if (bAlerted || IsDead() || !Target || bWaitingForTrigger)
	{
		return;
	}
	bAlerted = true;

	// Whatever a scripted event had it doing is over: the fight takes it.
	EndScripted();
	ReactionTimeLeft = FMath::FRandRange(ReactionTimeMin, FMath::Max(ReactionTimeMin, ReactionTimeMax));
	AlertTarget = Target;
	AlertAlliesTimeLeft = AlertAlliesDelay;

	// Heard, not seen: the noise is where to look.
	LastKnownPlayerLocation = Target->GetActorLocation();
	TimeSinceSeenPlayer = 0.0f;
	bSeenSinceAlert = false;
	bSightingCalled = false;
}

void AEnemyBase::TriggerAmbush(AActor* Target)
{
	// Only the first time: walking back into a repeat trigger doesn't replay the ambush.
	if (bWaitingForTrigger)
	{
		bWaitingForTrigger = false;
		bAmbushMovePending = AmbushPoint || bRushOnTrigger;
	}
	Alert(Target);
}

void AEnemyBase::HearPlayer(const FVector& Location)
{
	if (!bAlerted || IsDead())
	{
		return;
	}
	// Heard, not seen: the sound is the best guess at where they are now.
	LastKnownPlayerLocation = Location;

	// A fresh lead.
	bLeadGone = false;
	TimeAtLastKnown = 0.0f;
}

bool AEnemyBase::ChooseRoamSpot(FVector& OutSpot) const
{
	// Now and then across the map: the Target Point furthest from here (spawn points and
	// the like), so a roam sweeps the arena rather than milling about one corner.
	if (FMath::FRand() < RoamToPointChance)
	{
		const AActor* Furthest = nullptr;
		float FurthestDistance = -1.0f;
		for (TActorIterator<ATargetPoint> It(GetWorld()); It; ++It)
		{
			const float Distance = FVector::Dist2D(It->GetActorLocation(), GetActorLocation());
			if (Distance > FurthestDistance)
			{
				FurthestDistance = Distance;
				Furthest = *It;
			}
		}
		if (Furthest)
		{
			OutSpot = Furthest->GetActorLocation();
			return true;
		}
	}

	// Otherwise somewhere reachable nearby.
	const UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	FNavLocation Spot;
	if (Nav && Nav->GetRandomReachablePointInRadius(GetActorLocation(), RoamRadius, Spot))
	{
		OutSpot = Spot.Location;
		return true;
	}
	return false;
}

void AEnemyBase::AlertAllies()
{
	AActor* Target = AlertTarget.Get();
	if (!Target || IsDead())
	{
		return;
	}
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		AEnemyBase* Ally = *It;
		if (Ally != this && FVector::Dist(Ally->GetActorLocation(), GetActorLocation()) <= AlertAlliesRadius)
		{
			Ally->Alert(Target);
		}
	}
}

float AEnemyBase::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
	AController* EventInstigator, AActor* DamageCauser)
{
	const float Result = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
	if (EventInstigator && EventInstigator->GetPawn())
	{
		bWaitingForTrigger = false;
		Alert(EventInstigator->GetPawn());
	}

	// Hit and still standing (a killing hit gets the death bark instead).
	if (Result > 0.0f && !IsDead())
	{
		Bark(EBarkType::Hurt);
	}
	return Result;
}
