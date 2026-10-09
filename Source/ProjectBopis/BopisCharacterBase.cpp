// Copyright Epic Games, Inc. All Rights Reserved.

#include "BopisCharacterBase.h"
#include "ProjectBopisAnimInstance.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequenceBase.h"
#include "PhysicsEngine/PhysicalAnimationComponent.h"
#include "AlphaBlend.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Gameplay/HealthComponent.h"
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

	BoneDamageMultipliers.Add(TEXT("head"), 4.0f);

	// Crouch does nothing at all without this, and fails silently — CanCrouch()
	// just returns false with no warning. It is false by default.
	GetCharacterMovement()->NavAgentProps.bCanCrouch = true;
}

void ABopisCharacterBase::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	TimeUntilWeaponLowered = FMath::Max(0.0f, TimeUntilWeaponLowered - DeltaSeconds);

	UpdateReloadMontage();

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

	return Damage;
}

void ABopisCharacterBase::Die(AController* Killer, const FVector& ShotDirection)
{
	bIsDead = true;

	// Out of the movement system and out of the way. The mesh still blocks bullets, so
	// the dying body can be shot into a ragdoll.
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	PlayDeathAnimation(ShotDirection);
}

bool ABopisCharacterBase::PlayDeathAnimation(const FVector& ShotDirection)
{
	DeathMontage = nullptr;

	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (!AnimInstance)
	{
		return false;
	}

	// Which side the shot came from, in the body's own frame: X forward, Y right.
	const FVector FromShooter = GetActorRotation().UnrotateVector(-ShotDirection);
	const TArray<TObjectPtr<UAnimSequenceBase>>* Options = nullptr;
	if (FMath::Abs(FromShooter.X) >= FMath::Abs(FromShooter.Y))
	{
		Options = FromShooter.X >= 0.0f ? &DeathAnimations.Front : &DeathAnimations.Back;
	}
	else
	{
		Options = FromShooter.Y >= 0.0f ? &DeathAnimations.Right : &DeathAnimations.Left;
	}

	// Fall back to any front death if this side has none.
	if (Options->Num() == 0)
	{
		Options = &DeathAnimations.Front;
	}
	if (Options->Num() == 0)
	{
		return false;
	}

	UAnimSequenceBase* Chosen = (*Options)[FMath::RandRange(0, Options->Num() - 1)];
	if (!Chosen)
	{
		return false;
	}

	// A plain animation sequence wrapped as a montage on the fly, so no montage assets needed.
	DeathMontage = AnimInstance->PlaySlotAnimationAsDynamicMontage(Chosen, DeathSlotName, 0.1f, 0.2f);
	return DeathMontage != nullptr;
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

	// Motors pull each simulated bone toward where the animation has it — world space, so
	// the body holds its place rather than just its shape.
	FPhysicalAnimationData Hold;
	Hold.bIsLocalSimulation = false;
	Hold.OrientationStrength = RiddledHoldStrength;
	Hold.PositionStrength = RiddledHoldStrength;
	Hold.AngularVelocityStrength = RiddledHoldStrength * 0.1f;
	Hold.VelocityStrength = RiddledHoldStrength * 0.1f;

	USkeletalMeshComponent* Body = GetMesh();
	UseRagdollCollision();
	PhysicalAnimation->ApplyPhysicalAnimationSettingsBelow(RiddledRootBone, Hold, true);
	Body->SetAllBodiesBelowSimulatePhysics(RiddledRootBone, true, true);

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

	// The physics asset's bodies take over from the animation.
	USkeletalMeshComponent* Body = GetMesh();
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

	// Deliberately not gated on UsesAnimationDrivenFeedback() — that flag says
	// where the *weapon's* sound and muzzle flash come from. The body animation
	// is the character animating itself, and plays either way. Looked up by the
	// weapon's anim type, so each weapon gets its own without owning the asset.
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

	if (FoundMontage)
	{
		if (UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance())
		{
			AnimInstance->Montage_Play(FoundMontage);
		}
	}

	// Procedural kick on top of the montage. It stacks across rapid shots, where the
	// montage just restarts.
	if (UProjectBopisAnimInstance* BopisAnim = Cast<UProjectBopisAnimInstance>(GetMesh()->GetAnimInstance()))
	{
		BopisAnim->AddRecoil(Weapon->WasLastShotOffhand());
	}
}

void ABopisCharacterBase::PlayReloadAnimation(const AWeaponBase* Weapon)
{
	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (!Weapon || !AnimInstance)
	{
		return;
	}

	const EWeaponAnimType AnimType = Weapon->GetAnimType();

	if (TObjectPtr<UAnimMontage>* FoundMontage = ReloadMontages.Find(AnimType); FoundMontage && *FoundMontage)
	{
		AnimInstance->Montage_Play(*FoundMontage);
		ActiveReloadMontage = *FoundMontage;
	}

	// Dual wield reloads both guns in one beat: the off hand plays its own montage in its
	// own slot group, mirrored onto the left arm by the AnimBP.
	if (Weapon->IsDualWield())
	{
		if (TObjectPtr<UAnimMontage>* FoundOffhand = OffhandReloadMontages.Find(AnimType); FoundOffhand && *FoundOffhand)
		{
			AnimInstance->Montage_Play(*FoundOffhand);
		}
	}
}

void ABopisCharacterBase::PlayEquipAnimation(const AWeaponBase* Weapon)
{
	ActiveEquipMontage = nullptr;

	UAnimInstance* AnimInstance = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	if (!Weapon || !AnimInstance)
	{
		return;
	}

	const EWeaponAnimType AnimType = Weapon->GetAnimType();

	if (const TObjectPtr<UAnimMontage>* Found = EquipMontages.Find(AnimType); Found && *Found)
	{
		// Same slot group as fire/reload, so this also cuts off whatever the previous
		// weapon was still playing.
		ActiveEquipMontage = *Found;
		AnimInstance->Montage_Play(ActiveEquipMontage);
	}

	if (Weapon->IsDualWield())
	{
		if (const TObjectPtr<UAnimMontage>* FoundOffhand = OffhandEquipMontages.Find(AnimType); FoundOffhand && *FoundOffhand)
		{
			AnimInstance->Montage_Play(*FoundOffhand);
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
	// swapped: let the current insert finish, then play End (the rack).
	const AWeaponBase* EquippedWeapon = WeaponHolder ? WeaponHolder->GetEquippedWeapon() : nullptr;
	if (!EquippedWeapon || !EquippedWeapon->IsReloading())
	{
		AnimInstance->Montage_SetNextSection(LoopSection, EndSection, ActiveReloadMontage);
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
			1.0f, EMontagePlayReturnType::MontageLength, LoopStart, true);
	}
}
