// Copyright Epic Games, Inc. All Rights Reserved.

#include "BopisCharacterBase.h"
#include "ProjectBopisAnimInstance.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequenceBase.h"
#include "PhysicsEngine/PhysicalAnimationComponent.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "AlphaBlend.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Gameplay/HealthComponent.h"
#include "Gameplay/FootstepEffectsData.h"
#include "Engine/DamageEvents.h"
#include "ProjectBopis.h"

ABopisCharacterBase::ABopisCharacterBase()
{
	// The lowering timer and the looping reload montage are driven per frame.
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(34.0f, 96.0f);

	WeaponHolder = CreateDefaultSubobject<UWeaponHolderComponent>(TEXT("WeaponHolder"));
	Health = CreateDefaultSubobject<UHealthComponent>(TEXT("Health"));
	PhysicalAnimation = CreateDefaultSubobject<UPhysicalAnimationComponent>(TEXT("PhysicalAnimation"));

	// Bullets hit the body bone by bone, not the capsule around it — the capsule is only
	// for walking. That's what gives every hit a bone name (headshots, ragdoll shoves).
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Projectile, ECR_Ignore);
	GetMesh()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	GetMesh()->SetCollisionResponseToChannel(ECC_Projectile, ECR_Block);

	// When hit reactions put the upper body on physics, its bones must not collide with
	// the character's own capsule (a Pawn) — they'd be shoved out of it.
	GetMesh()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);

	BoneDamageMultipliers.Add(TEXT("head"), 4.0f);

	// Crouch does nothing at all without this, and fails silently — CanCrouch()
	// just returns false with no warning. It is false by default.
	GetCharacterMovement()->NavAgentProps.bCanCrouch = true;
}

void ABopisCharacterBase::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	TimeUntilWeaponLowered = FMath::Max(0.0f, TimeUntilWeaponLowered - DeltaSeconds);
	SilentEquipTimeLeft = FMath::Max(0.0f, SilentEquipTimeLeft - DeltaSeconds);
	UpdateWeaponBlocked();

	UpdateReloadMontage();

	if (bLegsSimulating && LegsFadeTime > 0.0f)
	{
		// Ease the legs back into the animation, then let go of physics.
		LegsFadeLeft -= DeltaSeconds;
		const float Weight = LegsWeight * FMath::Clamp(LegsFadeLeft / LegsFadeTime, 0.0f, 1.0f);
		for (const FName Root : SimulatedLimbs)
		{
			GetMesh()->SetAllBodiesBelowPhysicsBlendWeight(Root, Weight, false, true);
		}
		if (LegsFadeLeft <= 0.0f)
		{
			StopSimulatingLegs();
		}
	}

	UpdateFreeArmPhysics(DeltaSeconds);

	if (bIsStaggered)
	{
		// Settle back into the animation over the stagger's last HitReactDuration.
		StaggerTimeLeft -= DeltaSeconds;
		const float FadeTime = FMath::Max(HitReactDuration, KINDA_SMALL_NUMBER);
		GetMesh()->SetAllBodiesBelowPhysicsBlendWeight(RiddledRootBone,
			FMath::Clamp(StaggerTimeLeft / FadeTime, 0.0f, 1.0f), false, true);

		if (StaggerTimeLeft <= 0.0f)
		{
			EndHitReactions();
		}
	}
	else if (bIsHitReacting)
	{
		// Fade the physics out over the whole reaction, so the bones ease back into the animation.
		HitReactTimeLeft -= DeltaSeconds;
		GetMesh()->SetAllBodiesBelowPhysicsBlendWeight(RiddledRootBone,
			FMath::Clamp(HitReactTimeLeft / FMath::Max(HitReactDuration, KINDA_SMALL_NUMBER), 0.0f, 1.0f), false, true);

		if (HitReactTimeLeft <= 0.0f)
		{
			EndHitReactions();
		}
	}

	if (bIsRiddled)
	{
		// Hold the stagger short of its end, so it never blends back out into the living pose.
		UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
		if (DeathMontage && AnimInstance
			&& AnimInstance->Montage_GetPosition(DeathMontage) >= DeathMontage->GetPlayLength() - 0.15f)
		{
			AnimInstance->Montage_Pause(DeathMontage);
		}

		RiddledTimeLeft -= DeltaSeconds;
		if (RiddledTimeLeft <= 0.0f)
		{
			// Collapse, carrying everything it soaked: unload a magazine, and it flies.
			StartRagdoll(RiddledLastHit, RiddledLastDirection, RiddledDamage);
		}
	}
	else if (bIsDead && !bIsRagdoll)
	{
		// A death animation that runs out, or gets cut off, ends in a ragdoll. Caught just
		// before its end, so it never blends back out into the living pose.
		const UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
		const bool bStillPlaying = DeathMontage && AnimInstance && AnimInstance->Montage_IsPlaying(DeathMontage)
			&& AnimInstance->Montage_GetPosition(DeathMontage) < DeathMontage->GetPlayLength() - 0.1f;

		if (!bStillPlaying)
		{
			StartRagdoll(FHitResult(), FVector::ZeroVector, 0.0f);
		}
	}
}

float ABopisCharacterBase::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
	AController* EventInstigator, AActor* DamageCauser)
{
	// Point damage (every bullet) knows the bone it hit and the way it was travelling.
	FHitResult Hit;
	FVector ShotDirection = FVector::ZeroVector;
	if (DamageEvent.IsOfType(FPointDamageEvent::ClassID))
	{
		const FPointDamageEvent& PointEvent = static_cast<const FPointDamageEvent&>(DamageEvent);
		Hit = PointEvent.HitInfo;
		ShotDirection = PointEvent.ShotDirection;
	}

	float Damage = DamageAmount;
	if (const float* Multiplier = BoneDamageMultipliers.Find(Hit.BoneName))
	{
		Damage *= *Multiplier;
	}

	// Hits still inside the killing burst (pellets of the same blast) add to its overkill;
	// enough of it skips straight to ragdoll from any stage.
	const bool bInBurst = bIsDead && !bIsRagdoll
		&& GetWorld()->GetTimeSeconds() - DeathTime <= OverkillWindow;
	if (bInBurst)
	{
		BurstOverkill += Damage;
	}
	const bool bOverkilled = bInBurst && BurstOverkill >= InstantRagdollOverkill;

	// Already limp: no more damage, every bullet just throws the body.
	if (bIsRagdoll)
	{
		LaunchBody(Hit, ShotDirection, Damage);
		return 0.0f;
	}

	// Riddled: still on its feet, every bullet jerks the bone it hit and builds the final launch.
	if (bIsRiddled)
	{
		RiddledDamage += Damage;
		RiddledLastHit = Hit;
		RiddledLastDirection = ShotDirection;

		// A fresh window opens once the last one has passed; hits inside it add up.
		const float Now = GetWorld()->GetTimeSeconds();
		if (Now - RiddledBurstStart > OverkillWindow)
		{
			RiddledBurstStart = Now;
			RiddledBurstDamage = 0.0f;
		}
		RiddledBurstDamage += Damage;

		if (bOverkilled || RiddledBurstDamage >= RiddledBreakDamage)
		{
			StartRagdoll(Hit, ShotDirection, RiddledDamage);
		}
		else
		{
			KickBone(Hit.BoneName, ShotDirection, Damage, RiddledKickScale);
		}
		return 0.0f;
	}

	// Dying: the death animation plays until enough extra damage knocks it into the riddled
	// phase, or the killing burst overkills it straight into a ragdoll.
	if (bIsDead)
	{
		PostDeathDamage += Damage;
		if (bOverkilled)
		{
			StartRagdoll(Hit, ShotDirection, Damage);
		}
		else if (PostDeathDamage >= RagdollDamageThreshold)
		{
			StartRiddled(Hit, ShotDirection, Damage);
		}
		return 0.0f;
	}

	// Alive. Super runs the engine's checks (e.g. CanBeDamaged) — only while alive, since on
	// a simulating body it would also add its own physics impulse on top of ours.
	Damage *= Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser) / FMath::Max(DamageAmount, KINDA_SMALL_NUMBER);

	const float HealthBefore = Health ? Health->GetHealth() : 0.0f;
	if (Health && Health->ApplyDamage(Damage))
	{
		Die(EventInstigator, ShotDirection);

		// The burst starts with the killing blow's spare damage; the rest of the blast may add to it.
		DeathTime = GetWorld()->GetTimeSeconds();
		BurstOverkill = Damage - HealthBefore;
		PostDeathDamage = 0.0f;

		if (BurstOverkill >= InstantRagdollOverkill || !DeathMontage)
		{
			StartRagdoll(Hit, ShotDirection, Damage);
		}
	}
	else if (Damage > 0.0f)
	{
		// Survived: hits within StaggerWindow add up, and enough of them stagger (again, if
		// already staggered). Anything less is a light reaction, or a jolt to a staggered body.
		const float Now = GetWorld()->GetTimeSeconds();
		if (Now - StaggerWindowStart > StaggerWindow)
		{
			StaggerWindowStart = Now;
			StaggerWindowDamage = 0.0f;
		}
		StaggerWindowDamage += Damage;

		if (StaggerDuration > 0.0f && StaggerWindowDamage >= StaggerDamage)
		{
			// Each stagger needs a fresh StaggerDamage, so stun-locking takes sustained fire.
			StaggerWindowDamage = 0.0f;
			StartStagger(Hit, ShotDirection, Damage);
		}
		else if (bIsStaggered)
		{
			KickBone(Hit.BoneName, ShotDirection, Damage, StaggerKickScale);
		}
		else
		{
			StartHitReaction(Hit, ShotDirection, Damage);
		}
	}

	return Damage;
}

void ABopisCharacterBase::Die(AController* Killer, const FVector& ShotDirection)
{
	bIsDead = true;

	// Any hit reaction or stagger ends here; the death animation needs the bones back.
	EndHitReactions();

	// Out of the movement system and out of the way. The mesh still blocks bullets, so
	// the dying body can be shot into a ragdoll.
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	PlayDeathAnimation(ShotDirection);
}

bool ABopisCharacterBase::PlayDeathAnimation(const FVector& ShotDirection)
{
	DeathMontage = PlayDirectionalAnimation(DeathAnimations, ShotDirection);
	return DeathMontage != nullptr;
}

UAnimMontage* ABopisCharacterBase::PlayDirectionalAnimation(const FDirectionalAnimSet& Set, const FVector& ShotDirection)
{
	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (!AnimInstance)
	{
		return nullptr;
	}

	// Which side the shot came from, in the body's own frame: X forward, Y right.
	const FVector FromShooter = GetActorRotation().UnrotateVector(-ShotDirection);
	const TArray<TObjectPtr<UAnimSequenceBase>>* Options = nullptr;
	if (FMath::Abs(FromShooter.X) >= FMath::Abs(FromShooter.Y))
	{
		Options = FromShooter.X >= 0.0f ? &Set.Front : &Set.Back;
	}
	else
	{
		Options = FromShooter.Y >= 0.0f ? &Set.Right : &Set.Left;
	}

	// Fall back to the front set if this side has none.
	if (Options->Num() == 0)
	{
		Options = &Set.Front;
	}
	if (Options->Num() == 0)
	{
		return nullptr;
	}

	UAnimSequenceBase* Chosen = (*Options)[FMath::RandRange(0, Options->Num() - 1)];
	if (!Chosen)
	{
		return nullptr;
	}

	// A plain animation sequence wrapped as a montage on the fly, so no montage assets needed.
	return AnimInstance->PlaySlotAnimationAsDynamicMontage(Chosen, DeathSlotName, 0.1f, 0.2f);
}

void ABopisCharacterBase::SimulateUpperBody(float HoldStrength)
{
	WaitForAnimEvaluation();

	// Motors pull each simulated bone toward where the animation has it — world space, so
	// the body holds its place rather than just its shape.
	FPhysicalAnimationData Hold;
	Hold.bIsLocalSimulation = false;
	Hold.OrientationStrength = HoldStrength;
	Hold.PositionStrength = HoldStrength;
	Hold.AngularVelocityStrength = HoldStrength * 0.1f;
	Hold.VelocityStrength = HoldStrength * 0.1f;

	USkeletalMeshComponent* Body = GetMesh();
	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(RiddledRootBone, Hold, true);
	Body->SetAllBodiesBelowSimulatePhysics(RiddledRootBone, true, true);
	Body->SetAllBodiesBelowPhysicsBlendWeight(RiddledRootBone, 1.0f, false, true);
}

namespace
{
	/** World-space leg motors at HoldStrength (velocity terms a tenth of it). */
	FPhysicalAnimationData MakeLegHold(float HoldStrength)
	{
		FPhysicalAnimationData Hold;
		Hold.bIsLocalSimulation = false;
		Hold.OrientationStrength = HoldStrength;
		Hold.PositionStrength = HoldStrength;
		Hold.AngularVelocityStrength = HoldStrength * 0.1f;
		Hold.VelocityStrength = HoldStrength * 0.1f;
		return Hold;
	}

	const FName ThighL(TEXT("thigh_l"));
	const FName ThighR(TEXT("thigh_r"));
	const FName LeftArmRoot(TEXT("upperarm_l"));
}

void ABopisCharacterBase::SimulateLegs(float HoldStrength, bool bWithLeftArm, float ArmHoldStrength)
{
	WaitForAnimEvaluation();

	// The left arm left out this time (the gun changed mid-dive, say): back to the animation.
	if (!bWithLeftArm && SimulatedLimbs.Contains(LeftArmRoot))
	{
		StopLimb(LeftArmRoot);
	}

	// Physics needs physics collision; the living mesh is normally query-only.
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);

	// Same world-space motors as the upper body: the legs keep to the animation unless
	// something solid — the floor — is in the way.
	SimulatedLimbs = { ThighL, ThighR };
	StartLimb(ThighL, MakeLegHold(HoldStrength));
	StartLimb(ThighR, MakeLegHold(HoldStrength));
	if (bWithLeftArm)
	{
		SimulatedLimbs.Add(LeftArmRoot);
		StartLimb(LeftArmRoot, MakeLegHold(ArmHoldStrength));
		LeftArmHoldStrength = ArmHoldStrength;
	}

	bLegsSimulating = true;
	LegsFadeTime = 0.0f;
	LegsFadeLeft = 0.0f;
	LegsWeight = 1.0f;
}

void ABopisCharacterBase::SetLegHoldStrength(float HoldStrength, float ArmHoldStrength)
{
	if (!bLegsSimulating || LegsFadeTime > 0.0f)
	{
		return;
	}

	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(ThighL, MakeLegHold(HoldStrength), true);
	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(ThighR, MakeLegHold(HoldStrength), true);
	if (SimulatedLimbs.Contains(LeftArmRoot))
	{
		PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(LeftArmRoot, MakeLegHold(ArmHoldStrength), true);
		LeftArmHoldStrength = ArmHoldStrength;
	}
}

void ABopisCharacterBase::SetLeftArmSimulating(bool bSimulate, float ArmHoldStrength)
{
	if (!bLegsSimulating || LegsFadeTime > 0.0f || bSimulate == SimulatedLimbs.Contains(LeftArmRoot))
	{
		return;
	}
	WaitForAnimEvaluation();

	if (bSimulate)
	{
		SimulatedLimbs.Add(LeftArmRoot);
		StartLimb(LeftArmRoot, MakeLegHold(ArmHoldStrength));
		LeftArmHoldStrength = ArmHoldStrength;
	}
	else
	{
		StopLimb(LeftArmRoot);
		SimulatedLimbs.Remove(LeftArmRoot);
	}
}

void ABopisCharacterBase::StartLimb(FName Root, const FPhysicalAnimationData& Hold)
{
	WaitForAnimEvaluation();

	USkeletalMeshComponent* Body = GetMesh();
	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(Root, Hold, true);
	Body->SetAllBodiesBelowSimulatePhysics(Root, true, true);
	Body->SetAllBodiesBelowPhysicsBlendWeight(Root, 1.0f, false, true);
}

void ABopisCharacterBase::StopLimb(FName Root)
{
	WaitForAnimEvaluation();

	USkeletalMeshComponent* Body = GetMesh();
	Body->SetAllBodiesBelowPhysicsBlendWeight(Root, 0.0f, false, true);
	Body->SetAllBodiesBelowSimulatePhysics(Root, false, true);
	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(Root, FPhysicalAnimationData(), true);
}

void ABopisCharacterBase::UpdateWeaponBlocked()
{
	const AWeaponBase* Weapon = WeaponHolder ? WeaponHolder->GetEquippedWeapon() : nullptr;
	if (!Weapon || bIsDead || !IsWeaponRaised())
	{
		bWeaponBlocked = false;
		return;
	}

	// From the chest along the aim, judged on the aim alone (not where the gun is drawn), so
	// lowering it can't clear the wall and bring it straight back up.
	// The bones are written by the worker-thread animation evaluation: wait for it before reading.
	WaitForAnimEvaluation();
	const USkeletalMeshComponent* Body = GetMesh();
	const FVector Chest = (Body && Body->GetComponentSpaceTransforms().Num() > 0 && Body->DoesSocketExist(TEXT("spine_05")))
		? Body->GetSocketLocation(TEXT("spine_05"))
		: GetActorLocation() + FVector(0.0f, 0.0f, 50.0f);
	const FVector Aim = Controller ? GetControlRotation().Vector() : GetActorForwardVector();
	const float Reach = (IsPistolAnimType(Weapon->GetAnimType()) ? PistolWallDistance : LongGunWallDistance)
		+ (bWeaponBlocked ? WallClearMargin : 0.0f);

	// Walls and props only: someone standing close isn't a reason to lower the gun.
	FCollisionObjectQueryParams Objects;
	Objects.AddObjectTypesToQuery(ECC_WorldStatic);
	Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(WeaponWall), false, this);
	Params.AddIgnoredActor(Weapon);
	// Everything along the line, kept only if it's solid to bullets and sight (not a trigger box,
	// not a casing) and faces the gun rather than up (a wall, not the floor you're aiming at).
	TArray<FHitResult> Hits;
	GetWorld()->LineTraceMultiByObjectType(Hits, Chest, Chest + Aim * Reach, Objects, Params);
	bWeaponBlocked = Hits.ContainsByPredicate([](const FHitResult& Hit)
	{
		const UPrimitiveComponent* Component = Hit.GetComponent();
		return Component && Component->GetCollisionResponseToChannel(ECC_Visibility) == ECR_Block
			&& Hit.ImpactNormal.Z < 0.7f;
	});
}

void ABopisCharacterBase::WaitForAnimEvaluation()
{
	if (USkeletalMeshComponent* Body = GetMesh())
	{
		Body->HandleExistingParallelEvaluationTask(true, true);
	}
}

bool ABopisCharacterBase::WantsFreeArmPhysics() const
{
	const AWeaponBase* Weapon = WeaponHolder ? WeaponHolder->GetEquippedWeapon() : nullptr;
	return bFreeArmPhysics && Weapon && Weapon->GetAnimType() == EWeaponAnimType::PistolOneHanded
		&& IsWeaponRaised() && !IsReloadAnimating() && !IsEquipAnimating();
}

void ABopisCharacterBase::UpdateFreeArmPhysics(float DeltaSeconds)
{
	// Something else has the arm (a dive's loose limbs, a hit reaction, the ragdoll): leave it
	// to them. When they let go they reset it, so it starts fresh from here.
	if (SimulatedLimbs.Contains(LeftArmRoot) || bIsHitReacting || bIsStaggered || bIsDead)
	{
		bFreeArmSimulating = false;
		FreeArmWeight = 0.0f;
		return;
	}

	// Eased on and off, so raising or lowering the gun doesn't pop the arm.
	const float Target = WantsFreeArmPhysics() ? 1.0f : 0.0f;
	const float Rate = FreeArmBlendTime > 0.0f ? 1.0f / FreeArmBlendTime : 1000.0f;
	FreeArmWeight = FMath::FInterpConstantTo(FreeArmWeight, Target, DeltaSeconds, Rate);

	if (FreeArmWeight > 0.0f)
	{
		if (!bFreeArmSimulating)
		{
			// Physics needs physics collision; the living mesh is normally query-only.
			WaitForAnimEvaluation();
			GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
			StartLimb(LeftArmRoot, MakeLegHold(FreeArmHoldStrength));
			bFreeArmSimulating = true;
		}
		GetMesh()->SetAllBodiesBelowPhysicsBlendWeight(LeftArmRoot, FreeArmWeight, false, true);
	}
	else if (bFreeArmSimulating)
	{
		StopLimb(LeftArmRoot);
		bFreeArmSimulating = false;
		if (!bLegsSimulating)
		{
			GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		}
	}
}

void ABopisCharacterBase::EndSimulatedLegs(float BlendOutTime)
{
	if (!bLegsSimulating || LegsFadeTime > 0.0f)
	{
		return;
	}

	if (BlendOutTime <= 0.0f)
	{
		StopSimulatingLegs();
		return;
	}

	// Tick fades the blend weight down over this, then stops the simulation.
	LegsFadeTime = BlendOutTime;
	LegsFadeLeft = BlendOutTime;
}

void ABopisCharacterBase::StopSimulatingLegs()
{
	WaitForAnimEvaluation();

	bLegsSimulating = false;
	LegsFadeTime = 0.0f;

	// Dead, the ragdoll owns every bone now; leave them be.
	if (bIsDead)
	{
		return;
	}

	for (const FName Root : SimulatedLimbs)
	{
		StopLimb(Root);
	}
	SimulatedLimbs.Reset();

	// The upper body may still be reacting to a hit, which needs physics collision too.
	if (!bIsHitReacting && !bIsStaggered)
	{
		GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	}
}

void ABopisCharacterBase::StartHitReaction(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage)
{
	WaitForAnimEvaluation();

	if (HitReactDuration <= 0.0f)
	{
		return;
	}

	if (!bIsHitReacting)
	{
		// Physics needs physics collision; the living mesh is normally query-only.
		GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		SimulateUpperBody(HitReactHoldStrength);
		bIsHitReacting = true;
	}

	// Every hit restarts the fade at full physics.
	HitReactTimeLeft = HitReactDuration;
	GetMesh()->SetAllBodiesBelowPhysicsBlendWeight(RiddledRootBone, 1.0f, false, true);

	KickBone(Hit.BoneName, ShotDirection, BulletDamage, HitReactKickScale);
}

void ABopisCharacterBase::StartStagger(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage)
{
	WaitForAnimEvaluation();

	GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);

	// Looser motors than a hit reaction, so the body reels. Restarting refreshes everything.
	bIsHitReacting = false;
	bIsStaggered = true;
	StaggerTimeLeft = StaggerDuration;
	SimulateUpperBody(StaggerHoldStrength);

	// Rooted to the spot: no walking out of it.
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();

	PlayDirectionalAnimation(StaggerAnimations, ShotDirection);

	KickBone(Hit.BoneName, ShotDirection, BulletDamage, StaggerKickScale);
}

void ABopisCharacterBase::EndHitReactions()
{
	WaitForAnimEvaluation();

	if (!bIsHitReacting && !bIsStaggered)
	{
		return;
	}

	const bool bWasStaggered = bIsStaggered;
	bIsHitReacting = false;
	bIsStaggered = false;

	// Bones back to the animation, motors off, mesh back to query-only.
	USkeletalMeshComponent* Body = GetMesh();
	Body->SetAllBodiesBelowPhysicsBlendWeight(RiddledRootBone, 0.0f, false, true);
	Body->SetAllBodiesBelowSimulatePhysics(RiddledRootBone, false, true);
	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(RiddledRootBone, FPhysicalAnimationData(), true);

	// The left arm sits under the upper body, so that reset took it too: if a dive had it
	// loose, it goes straight back on.
	if (SimulatedLimbs.Contains(LeftArmRoot) && LegsFadeTime <= 0.0f)
	{
		StartLimb(LeftArmRoot, MakeLegHold(LeftArmHoldStrength));
	}

	if (!bLegsSimulating)
	{
		Body->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	}

	if (bWasStaggered && !bIsDead)
	{
		GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	}
}

void ABopisCharacterBase::BeginPlay()
{
	Super::BeginPlay();

	PhysicalAnimation->SetSkeletalMeshComponent(GetMesh());
}

void ABopisCharacterBase::UseRagdollCollision()
{
	USkeletalMeshComponent* Body = GetMesh();
	Body->SetCollisionProfileName(TEXT("Ragdoll"));
	Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	Body->SetCollisionResponseToChannel(ECC_Projectile, ECR_Block);
}

void ABopisCharacterBase::StartRiddled(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage)
{
	if (RiddledDuration <= 0.0f)
	{
		StartRagdoll(Hit, ShotDirection, BulletDamage);
		return;
	}

	bIsRiddled = true;
	RiddledTimeLeft = RiddledDuration;
	RiddledDamage = BulletDamage;
	RiddledBurstStart = GetWorld()->GetTimeSeconds();
	RiddledBurstDamage = BulletDamage;
	RiddledLastHit = Hit;
	RiddledLastDirection = ShotDirection;

	// The death animation becomes a slow stagger the legs keep following.
	if (UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance(); AnimInstance && DeathMontage)
	{
		AnimInstance->Montage_SetPlayRate(DeathMontage, RiddledAnimRate);
	}

	UseRagdollCollision();
	SimulateUpperBody(RiddledHoldStrength);

	// The bullet that started it lands too.
	KickBone(Hit.BoneName, ShotDirection, BulletDamage, RiddledKickScale);
}

void ABopisCharacterBase::KickBone(FName BoneName, const FVector& ShotDirection, float BulletDamage, float Scale)
{
	USkeletalMeshComponent* Body = GetMesh();
	if (BoneName == NAME_None || ShotDirection.IsNearlyZero())
	{
		return;
	}

	// AddImpulse on an animated (kinematic) bone does nothing and logs an error.
	const FBodyInstance* BoneBody = Body->GetBodyInstance(BoneName);
	if (!BoneBody || !BoneBody->IsInstanceSimulatingPhysics())
	{
		BoneName = RiddledRootBone;
		BoneBody = Body->GetBodyInstance(BoneName);
		if (!BoneBody || !BoneBody->IsInstanceSimulatingPhysics())
		{
			return;
		}
	}

	const float Speed = FMath::Min(BulletDamage * LaunchSpeedPerDamage, MaxLaunchSpeedPerHit);
	Body->AddImpulse(ShotDirection.GetSafeNormal() * Speed * Scale, BoneName, true);
}

void ABopisCharacterBase::BlastLaunch(const FVector& Velocity)
{
	if (!bIsDead)
	{
		return;
	}
	if (!bIsRagdoll)
	{
		// Out of the death animation or the riddled stage at once: a blast doesn't wait.
		WaitForAnimEvaluation();
		StartRagdoll(FHitResult(), FVector::ZeroVector, 0.0f);
	}
	GetMesh()->AddImpulseToAllBodiesBelow(Velocity, NAME_None, true, true);
}

void ABopisCharacterBase::StartRagdoll(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage)
{
	if (bIsRagdoll)
	{
		return;
	}
	bIsRagdoll = true;
	bIsRiddled = false;

	// Motors off, or the corpse would stay stiffly posed.
	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(RiddledRootBone, FPhysicalAnimationData(), true);
	DeathMontage = nullptr;

	// The physics asset's bodies take over from the animation. A corpse asset of its own (the
	// CC bodies: CC's constraints) goes in first, so the bodies are built from it; after the
	// motors above, which belonged to the old asset's bodies.
	USkeletalMeshComponent* Body = GetMesh();
	if (RagdollPhysicsAsset && Body->GetPhysicsAsset() != RagdollPhysicsAsset)
	{
		Body->SetPhysicsAsset(RagdollPhysicsAsset, true);
	}
	UseRagdollCollision();
	Body->SetSimulatePhysics(true);

	LaunchBody(Hit, ShotDirection, BulletDamage);
}

void ABopisCharacterBase::LaunchBody(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage)
{
	USkeletalMeshComponent* Body = GetMesh();
	if (!bIsRagdoll || !Body || BulletDamage <= 0.0f || ShotDirection.IsNearlyZero())
	{
		return;
	}

	const FVector Direction = ShotDirection.GetSafeNormal();
	const float Speed = FMath::Min(BulletDamage * LaunchSpeedPerDamage, MaxLaunchSpeedPerHit);

	// The whole body rides the bullet, lifted so it leaves the ground. Velocity changes,
	// not forces: the result doesn't depend on how much each bone weighs.
	const FVector Launch = Direction * Speed + FVector::UpVector * (Speed * LaunchLift);
	Body->AddImpulseToAllBodiesBelow(Launch, NAME_None, true, true);

	// The struck bone gets extra, so the body twists around the hit.
	if (Hit.BoneName != NAME_None)
	{
		Body->AddImpulse(Direction * Speed * BoneKickScale, Hit.BoneName, true);
	}
}

void ABopisCharacterBase::PlayFireAnimation(const AWeaponBase* Weapon)
{
	if (!Weapon)
	{
		return;
	}

	// The body animation is the character animating itself, separate from the gun's own fire
	// animation (which moves the gun and makes its sounds). Looked up by the weapon's anim
	// type, so each weapon gets its own without owning the asset.
	const EWeaponAnimType AnimType = Weapon->GetAnimType();
	UAnimMontage* FoundMontage = nullptr;

	// Most specific map first; each lookup only runs while nothing usable is found yet.
	auto TryMap = [&FoundMontage, AnimType](const TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>>& Map)
	{
		if (!FoundMontage)
		{
			const TObjectPtr<UAnimMontage>* Entry = Map.Find(AnimType);
			FoundMontage = Entry ? Entry->Get() : nullptr;
		}
	};

	if (Weapon->WasLastShotOffhand())
	{
		if (bIsAiming)
		{
			TryMap(AimOffhandFireMontages);
		}
		TryMap(OffhandFireMontages);
	}

	if (bIsAiming)
	{
		TryMap(AimFireMontages);
	}
	TryMap(FireMontages);

	// Fast guns: the montage keeps pace, so each shot's kick and return fit before the next
	// (a montage restarted mid-kick holds the gun up for the whole burst).
	const float Interval = Weapon->GetTimeBetweenShots();
	if (FoundMontage)
	{
		if (UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance())
		{
			const float Length = FoundMontage->GetPlayLength();
			const float Rate = Interval > 0.0f ? FMath::Clamp(Length / Interval, 1.0f, MaxFireMontageRate) : 1.0f;
			AnimInstance->Montage_Play(FoundMontage, Rate);
		}
	}

	// Procedural kick on top, in proportion to the fire rate: full for slow guns, lighter
	// per shot for fast ones, so a burst shakes the gun instead of holding it up.
	if (UProjectBopisAnimInstance* BopisAnim = Cast<UProjectBopisAnimInstance>(GetMesh()->GetAnimInstance()))
	{
		const float Strength = Interval > 0.0f ? FMath::Clamp(Interval / FullKickInterval, 0.25f, 1.0f) : 1.0f;
		BopisAnim->AddRecoil(Weapon->WasLastShotOffhand(), Strength);
	}
}

void ABopisCharacterBase::PlayReloadAnimation(const AWeaponBase* Weapon, float PlayRate)
{
	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (!Weapon || !AnimInstance)
	{
		return;
	}

	const EWeaponAnimType AnimType = Weapon->GetAnimType();

	if (TObjectPtr<UAnimMontage>* FoundMontage = ReloadMontages.Find(AnimType); FoundMontage && *FoundMontage)
	{
		AnimInstance->Montage_Play(*FoundMontage, PlayRate);
		ActiveReloadMontage = *FoundMontage;
		ActiveReloadPlayRate = PlayRate;
	}

	// Dual wield reloads both guns in one beat: the off hand plays its own montage in its
	// own slot group, mirrored onto the left arm by the AnimBP.
	if (Weapon->IsDualWield())
	{
		if (TObjectPtr<UAnimMontage>* FoundOffhand = OffhandReloadMontages.Find(AnimType); FoundOffhand && *FoundOffhand)
		{
			AnimInstance->Montage_Play(*FoundOffhand, PlayRate);
		}
	}
}

void ABopisCharacterBase::PlayFootstep(bool bLeft)
{
	USkeletalMeshComponent* Body = GetMesh();
	if (!FootstepEffects || !Body || bIsRagdoll)
	{
		return;
	}

	// Whatever is under the foot, with its physical material. From a little above the sole —
	// on a step up, the foot can already be inside the ground.
	const FVector Foot = Body->GetSocketLocation(bLeft ? LeftFootBone : RightFootBone);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(Footstep), false, this);
	Params.bReturnPhysicalMaterial = true;
	FHitResult Hit;
	if (!GetWorld()->LineTraceSingleByChannel(Hit, Foot + FVector::UpVector * 10.0f,
		Foot - FVector::UpVector * FootstepTraceDistance, ECC_Visibility, Params))
	{
		return;
	}

	const float Volume = FootstepEffects->GaitVolume(GetVelocity().Size2D(), bIsCrouched);
	LastFootstepSound = FootstepEffects->PlayFootstep(this, Hit, Volume, LastFootstepSound);
}

void ABopisCharacterBase::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);

	// Onto the feet: a thud by how hard. The dive lands on the body and makes its own.
	if (!LandsOnTheBody())
	{
		PlayFallThud(-GetVelocity().Z);
	}
}

void ABopisCharacterBase::PlayDiveLandingThud()
{
	if (FootstepEffects)
	{
		PlayGroundThud(ThudBone, 100.0f, FootstepEffects->GetDiveLandingVolume(), true);
	}
}

void ABopisCharacterBase::PlayRollThud()
{
	if (FootstepEffects)
	{
		PlayGroundThud(ThudBone, 100.0f, FootstepEffects->GetRollVolume(), true);
	}
}

void ABopisCharacterBase::PlayFallThud(float FallSpeed)
{
	const float Volume = FootstepEffects ? FootstepEffects->FallVolume(FallSpeed) : 0.0f;
	if (Volume > 0.0f)
	{
		PlayGroundThud(LeftFootBone, FootstepTraceDistance + 20.0f, Volume, false);
	}
}

void ABopisCharacterBase::PlayGroundThud(FName Bone, float TraceDistance, float Volume, bool bBody)
{
	USkeletalMeshComponent* Body = GetMesh();
	if (!FootstepEffects || !Body || bIsRagdoll || Volume <= 0.0f)
	{
		return;
	}

	const FVector From = Body->GetSocketLocation(Bone);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(GroundThud), false, this);
	Params.bReturnPhysicalMaterial = true;
	FHitResult Hit;
	if (!GetWorld()->LineTraceSingleByChannel(Hit, From + FVector::UpVector * 10.0f,
		From - FVector::UpVector * TraceDistance, ECC_Visibility, Params))
	{
		return;
	}
	LastFootstepSound = FootstepEffects->PlayThud(this, Hit, Volume, LastFootstepSound, bBody);
}

void ABopisCharacterBase::PlayEquipAnimation(const AWeaponBase* Weapon)
{
	ActiveEquipMontage = nullptr;

	UAnimInstance* AnimInstance = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	if (!Weapon || !AnimInstance)
	{
		return;
	}

	// Mid-roll (or anything else that owns the body): the gun is simply in the hand now. The
	// equip montage shares the slot group, and starting it would cut the move off.
	if (ShouldSkipEquipAnimation())
	{
		return;
	}

	const EWeaponAnimType AnimType = Weapon->GetAnimType();
	const float PlayRate = GetEquipPlayRate();

	// Face-down (or wherever the draw has no room): the gun's simply in the hand, but it takes
	// the draw's time to be ready, and the pose eases over in that time.
	if (ShouldSilentEquip())
	{
		const TObjectPtr<UAnimMontage>* Found = EquipMontages.Find(AnimType);
		SilentEquipDuration = (Found && *Found) ? (*Found)->GetPlayLength() / FMath::Max(PlayRate, 0.01f) : 0.5f;
		SilentEquipTimeLeft = SilentEquipDuration;
		return;
	}

	if (const TObjectPtr<UAnimMontage>* Found = EquipMontages.Find(AnimType); Found && *Found)
	{
		// Same slot group as fire/reload, so this also cuts off whatever the previous
		// weapon was still playing.
		ActiveEquipMontage = *Found;
		AnimInstance->Montage_Play(ActiveEquipMontage, PlayRate);
	}

	if (Weapon->IsDualWield())
	{
		if (const TObjectPtr<UAnimMontage>* FoundOffhand = OffhandEquipMontages.Find(AnimType); FoundOffhand && *FoundOffhand)
		{
			AnimInstance->Montage_Play(*FoundOffhand, PlayRate);
		}
	}
}

bool ABopisCharacterBase::IsEquipAnimating() const
{
	const UAnimInstance* AnimInstance = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	return ActiveEquipMontage && AnimInstance && AnimInstance->Montage_IsPlaying(ActiveEquipMontage);
}

void ABopisCharacterBase::UpdateReloadMontage()
{
	if (!ActiveReloadMontage)
	{
		return;
	}

	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (!AnimInstance || !AnimInstance->Montage_IsPlaying(ActiveReloadMontage))
	{
		// Finished, or cut off — firing plays a montage in the same slot group.
		ActiveReloadMontage = nullptr;
		return;
	}

	static const FName LoopSection(TEXT("Loop"));
	static const FName EndSection(TEXT("End"));

	if (AnimInstance->Montage_GetCurrentSection(ActiveReloadMontage) != LoopSection)
	{
		return; // Start, End, or a magazine-style reload with no Loop at all.
	}

	// Loading stops when the magazine fills, the reserve runs dry, or the weapon is
	// swapped: let the current insert finish, then play End (the rack) — or, without
	// bPlayReloadEnd, nothing: the montage ends with that insert and blends out.
	const AWeaponBase* EquippedWeapon = WeaponHolder ? WeaponHolder->GetEquippedWeapon() : nullptr;
	if (!EquippedWeapon || !EquippedWeapon->IsReloading())
	{
		AnimInstance->Montage_SetNextSection(LoopSection, bPlayReloadEnd ? EndSection : NAME_None, ActiveReloadMontage);
		return;
	}

	// Section jumps inside a montage don't blend, and Loop's first and last poses don't
	// match, so letting it wrap snaps. Instead, a blend-time before Loop ends, start a
	// fresh copy at Loop's start: it crossfades in while the old one fades out.
	float LoopStart = 0.0f;
	float LoopEnd = 0.0f;
	ActiveReloadMontage->GetSectionStartAndEndTime(
		ActiveReloadMontage->GetSectionIndex(LoopSection), LoopStart, LoopEnd);

	if (AnimInstance->Montage_GetPosition(ActiveReloadMontage) >= LoopEnd - ReloadLoopBlendTime)
	{
		// bStopAllMontages = true stops the montages already in this slot group — here,
		// the copy we're replacing — blending it out over the new copy's blend-in. That
		// is the crossfade. (False would leave the old copy looping underneath.)
		AnimInstance->Montage_PlayWithBlendIn(ActiveReloadMontage, FAlphaBlendArgs(ReloadLoopBlendTime),
			ActiveReloadPlayRate, EMontagePlayReturnType::MontageLength, LoopStart, true);
	}
}
