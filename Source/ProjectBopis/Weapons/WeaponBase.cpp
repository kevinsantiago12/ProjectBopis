// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/WeaponBase.h"
#include "Kismet/GameplayStatics.h"
#include "Perception/AISense_Hearing.h"
#include "Components/DecalComponent.h"
#include "Weapons/ProjectileBase.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/ImpactEffectsData.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Particles/ParticleSystemComponent.h"
#include "TimerManager.h"
#include "Gameplay/FocusComponent.h"
#include "Gameplay/ShootdodgeComponent.h"
#include "Weapons/ShellCasing.h"
#include "Enemies/EnemyBase.h"
#include "EngineUtils.h"


static TAutoConsoleVariable<bool> CVarShowWeaponTrace(TEXT("Weapon.ShowTrace"),
	true,TEXT("Draw debug trace lines for weapon fire."),ECVF_Cheat);

namespace
{
	/** A gap this much longer than the weapon's rate ends a burst (the trigger let go). */
	constexpr float BurstBreakTime = 0.15f;
}

// Sets default values
AWeaponBase::AWeaponBase()
{
	WeaponMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("WeaponMesh"));
	RootComponent = WeaponMesh;

	// Exists on every weapon so Blueprints can opt in with a checkbox; without a mesh
	// assigned it renders nothing and costs next to nothing.
	OffhandMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("OffhandMesh"));
	OffhandMesh->SetupAttachment(WeaponMesh);

 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

bool AWeaponBase::CanFire() const
{
	return TimeSinceLastShot >= TimeBetweenShots;
}

float AWeaponBase::GetDamageAtDistance(float Distance) const
{
	if (FalloffEndRange <= FalloffStartRange)
	{
		return BaseDamage;
	}

	const float Alpha = FMath::GetMappedRangeValueClamped(
		FVector2D(FalloffStartRange, FalloffEndRange), FVector2D(0.0f, 1.0f), Distance);
	return BaseDamage * FMath::Lerp(1.0f, MinDamageMultiplier, Alpha);
}

bool AWeaponBase::CanReload() const
{
	return !bIsReloading && CanAcceptRound();
}

bool AWeaponBase::CanAcceptRound() const
{
	return CurrentAmmoInMagazine < MagazineSize
		&& (bInfiniteReserve || GetReserveAmmo() > 0);
}

bool AWeaponBase::Reload(float Speed)
{
	if (!CanReload())
	{
		return false;
	}

	bIsReloading = true;
	ReloadSpeed = FMath::Max(Speed, 0.01f);

	if (ReloadStyle == EReloadStyle::PerRound)
	{
		// First round lands after the wind-up; LoadRound re-arms itself for the rest.
		GetWorldTimerManager().SetTimer(ReloadTimerHandle, this,
			&AWeaponBase::LoadRound, (ReloadStartDelay + TimePerRound) / ReloadSpeed, false);
	}
	else
	{
		GetWorldTimerManager().SetTimer(ReloadTimerHandle, this,
			&AWeaponBase::FinishReload, ReloadDuration / ReloadSpeed, false);
	}

	return true;
}

void AWeaponBase::LoadRound()
{
	// One cycle loads a batch, but stops short if the magazine fills or the
	// reserve runs dry partway through.
	for (int32 Loaded = 0; Loaded < RoundsPerLoad && CanAcceptRound(); ++Loaded)
	{
		CurrentAmmoInMagazine += TakeReserve(1);
	}

	if (CanAcceptRound())
	{
		GetWorldTimerManager().SetTimer(ReloadTimerHandle, this,
			&AWeaponBase::LoadRound, TimePerRound / ReloadSpeed, false);
	}
	else
	{
		bIsReloading = false;
	}
}

void AWeaponBase::FinishReload()
{
	// Top up only what's missing and leave the remainder in reserve — a partial
	// magazine is pooled, not discarded.
	const int32 Needed = MagazineSize - CurrentAmmoInMagazine;
	CurrentAmmoInMagazine += TakeReserve(Needed);

	bIsReloading = false;
}

void AWeaponBase::CancelReload()
{
	if (!bIsReloading)
	{
		return;
	}

	GetWorldTimerManager().ClearTimer(ReloadTimerHandle);
	bIsReloading = false;
}

float AWeaponBase::GetReloadProgress() const
{
	if (!bIsReloading)
	{
		return 0.0f;
	}
	const FTimerManager& Timers = GetWorldTimerManager();
	const float Rate = Timers.GetTimerRate(ReloadTimerHandle);
	return Rate > 0.0f ? FMath::Clamp(Timers.GetTimerElapsed(ReloadTimerHandle) / Rate, 0.0f, 1.0f) : 0.0f;
}

void AWeaponBase::CompleteReloadNow()
{
	if (!bIsReloading)
	{
		return;
	}
	GetWorldTimerManager().ClearTimer(ReloadTimerHandle);
	if (ReloadStyle == EReloadStyle::Magazine)
	{
		FinishReload();
	}
	else
	{
		// The cycle under way when it was cut off goes in (a shell carried through a roll),
		// then loading stops.
		for (int32 Loaded = 0; Loaded < RoundsPerLoad && CanAcceptRound(); ++Loaded)
		{
			CurrentAmmoInMagazine += TakeReserve(1);
		}
		bIsReloading = false;
	}
}

float AWeaponBase::GetProjectileSpeed() const
{
	// Read off the projectile class's defaults — the speed is the same for every round.
	const AProjectileBase* Round = (bIsProjectileWeapon && ProjectileClass)
		? ProjectileClass->GetDefaultObject<AProjectileBase>()
		: nullptr;
	return Round ? Round->GetInitialSpeed() : 0.0f;
}

EFireResult AWeaponBase::Fire(const FVector& TraceStart, const FVector& TraceDirection, bool bExact)
{
	if (!CanFire())
	{
		return EFireResult::RateLimited;
	}

	// After the rate check, so a shot that's both too soon and mid-reload reports
	// the more specific reason.
	if (bIsReloading)
	{
		// A tube-fed weapon fires whatever is already loaded. Rounds are committed
		// as they go in, so breaking off costs only the one in the shooter's hand.
		if (ReloadStyle == EReloadStyle::PerRound && CurrentAmmoInMagazine > 0)
		{
			CancelReload();
		}
		else
		{
			return EFireResult::Reloading;
		}
	}

	if (CurrentAmmoInMagazine <= 0)
	{
		if (DryFireSound)
		{
			UGameplayStatics::SpawnSoundAttached(DryFireSound, WeaponMesh, MuzzleSocketName);
		}

		// Reset the cadence clock so the click obeys TimeBetweenShots. Without this
		// CanFire() stays true every frame and a held trigger machine-guns the click.
		TimeSinceLastShot = 0.0f;
		return EFireResult::Empty;
	}

	--CurrentAmmoInMagazine;

	// The shot carries: enemies within NoiseRange hear it, and who fired it.
	if (NoiseRange > 0.0f)
	{
		UAISense_Hearing::ReportNoiseEvent(GetWorld(), GetActorLocation(), 1.0f, GetOwner(), NoiseRange);
	}

	USkeletalMeshComponent* FiringMesh = GetFiringMesh();

	if (!bUseAnimationDrivenFeedback)
	{
		if (FireSound)
		{
			UGameplayStatics::SpawnSoundAttached(FireSound, FiringMesh, MuzzleSocketName);
		}

		if (MuzzleFlash)
		{
			UGameplayStatics::SpawnEmitterAttached(MuzzleFlash, FiringMesh, MuzzleSocketName);
		}
	}
	else if (FireAnimation)
	{
		FiringMesh->PlayAnimation(FireAnimation, false);
	}

	// A burst runs while shots follow at the weapon's rate; a longer gap starts a new one.
	BurstTime = TimeSinceLastShot <= TimeBetweenShots + BurstBreakTime ? BurstTime + TimeSinceLastShot : 0.0f;

	const float SpreadAngle = GetCurrentSpread();
	const FVector SpreadDirection = bExact
		? TraceDirection
		: FMath::VRandCone(TraceDirection, FMath::DegreesToRadians(SpreadAngle));

	// The spread moves the pattern's centre; the pellets fan out around it. One pellet
	// at zero pellet spread skips the second random draw entirely, so every existing
	// weapon behaves exactly as before.
	for (int32 Pellet = 0; Pellet < PelletsPerShot; ++Pellet)
	{
		const FVector PelletDirection = PelletSpreadAngle > 0.0f
			? FMath::VRandCone(SpreadDirection, FMath::DegreesToRadians(PelletSpreadAngle))
			: SpreadDirection;

		if (bIsProjectileWeapon && ProjectileClass)
		{
			FireProjectile(TraceStart, PelletDirection);
		}
		else
		{
			FireHitscan(TraceStart, PelletDirection);
		}
	}

	TimeSinceLastShot = 0.0f;

	// The spent casing: out with the shot, or after a delay (a pump-action racks first).
	if (CasingMesh)
	{
		const bool bOffhand = IsOffhandNext();
		if (CasingEjectDelay > 0.0f)
		{
			FTimerHandle CasingTimer;
			GetWorldTimerManager().SetTimer(CasingTimer,
				FTimerDelegate::CreateUObject(this, &AWeaponBase::EjectCasing, bOffhand), CasingEjectDelay, false);
		}
		else
		{
			EjectCasing(bOffhand);
		}
	}

	// Record which hand this was before flipping, so the holder can animate the right arm.
	bLastShotWasOffhand = IsOffhandNext();
	if (bDualWield)
	{
		bOffhandFiresNext = !bOffhandFiresNext;
	}

	return EFireResult::Fired;
}

float AWeaponBase::GetCurrentSpread() const
{
	const float BurstAlpha = FMath::Clamp(BurstTime / SustainedSpreadTime, 0.0f, 1.0f);
	float Angle = Spread + SustainedSpread * BurstAlpha;

	if (const AActor* Holder = GetOwner())
	{
		// On the move, worse — but a shootdodge flies as true as standing still.
		const UShootdodgeComponent* Dodge = Holder->FindComponentByClass<UShootdodgeComponent>();
		if (!(Dodge && Dodge->IsDodging()))
		{
			const float MoveAlpha = FMath::Clamp(Holder->GetVelocity().Size2D() / MovingSpreadFullSpeed, 0.0f, 1.0f);
			Angle *= FMath::Lerp(1.0f, MovingSpreadMultiplier, MoveAlpha);
		}

		// Focus steadies the hand.
		if (const UFocusComponent* Focus = Holder->FindComponentByClass<UFocusComponent>())
		{
			Angle *= Focus->GetSpreadMultiplier();
		}
	}
	return Angle;
}

void AWeaponBase::FireHitscan(const FVector& TraceStart, const FVector& SpreadDirection)
{
	const FVector TraceEnd = TraceStart + (SpreadDirection * MaxRange);

	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(this);
	QueryParams.AddIgnoredActor(GetOwner());
	QueryParams.bReturnPhysicalMaterial = true;

	TArray<AActor*> Friends;
	GetFriendlyActors(Friends);
	QueryParams.AddIgnoredActors(Friends);

	FHitResult HitResult;
	const bool bHit = GetWorld()->LineTraceSingleByChannel(HitResult, TraceStart, TraceEnd, ECC_Visibility, QueryParams);

	const FVector DebugLineStart = TraceStart + (SpreadDirection * 150.0f);

	if (CVarShowWeaponTrace.GetValueOnGameThread())
	{
		DrawDebugLine(GetWorld(), DebugLineStart, bHit ? HitResult.Location : TraceEnd, bHit ?
			FColor::Green : FColor::Red, false, 2.0f, 0, 1.0f);
	}

	if (bHit)
	{
		if (ImpactEffects)
		{
			ImpactEffects->SpawnImpact(this, HitResult);
		}
		else if (HitDecalMaterial)
		{
			if (UDecalComponent* SpawnedDecal = UGameplayStatics::SpawnDecalAtLocation(this, HitDecalMaterial, DecalSize,
				HitResult.ImpactPoint, HitResult.ImpactNormal.Rotation(), DecalLifeSpan))
			{
				SpawnedDecal->SetFadeScreenSize(0.0f);
			}
		}

		if (HitResult.GetActor())
		{
			UGameplayStatics::ApplyPointDamage(HitResult.GetActor(), GetDamageAtDistance(HitResult.Distance),
				SpreadDirection, HitResult, GetInstigatorController(), this, nullptr);
		}
	}
}

void AWeaponBase::FireProjectile(const FVector& TraceStart, const FVector& SpreadDirection)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// Spawn dead centre on the crosshair and fly straight down it — same origin the
	// hitscan trace uses, so projectile and hitscan weapons agree on where shots go.
	// The firer is ignored in AProjectileBase so this can't detonate on spawn.
	FActorSpawnParameters SpawnParams;
	SpawnParams.Owner = this;
	SpawnParams.Instigator = GetInstigator();

	if (AProjectileBase* Projectile = World->SpawnActor<AProjectileBase>(ProjectileClass, TraceStart,
		SpreadDirection.Rotation(), SpawnParams))
	{
		Projectile->SetDamage(BaseDamage);
		Projectile->SetSourceWeapon(this);

		// Explicit, so the round can't hit whoever fired it even if Instigator is unset.
		Projectile->AddIgnoredActor(GetInstigator());
		Projectile->AddIgnoredActor(GetOwner());
		Projectile->AddIgnoredActor(this);

		// An enemy's rounds pass through the other enemies.
		TArray<AActor*> Friends;
		GetFriendlyActors(Friends);
		for (AActor* Friend : Friends)
		{
			Projectile->AddIgnoredActor(Friend);
		}
	}
}

// Called when the game starts or when spawned
void AWeaponBase::BeginPlay()
{
	Super::BeginPlay();

	// Not in the constructor — MagazineSize is a per-Blueprint default and isn't
	// applied yet at construction time.
	CurrentAmmoInMagazine = MagazineSize;
}

int32 AWeaponBase::GetReserveAmmo() const
{
	return ReserveSource ? ReserveSource->GetReserveAmmo(AmmoType) : 0;
}

int32 AWeaponBase::TakeReserve(int32 Wanted)
{
	if (bInfiniteReserve)
	{
		return Wanted;
	}

	return ReserveSource ? ReserveSource->TakeAmmo(AmmoType, Wanted) : 0;
}

// Called every frame
void AWeaponBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	TimeSinceLastShot += DeltaTime;
}


void AWeaponBase::EjectCasing(bool bOffhand)
{
	USkeletalMeshComponent* Mesh = (bOffhand && OffhandMesh) ? OffhandMesh.Get() : WeaponMesh.Get();
	if (!CasingMesh || !Mesh || !Mesh->DoesSocketExist(CasingSocketName))
	{
		return;
	}

	// Out to the gun's right, a little up and back: the barrel from the muzzle socket (the
	// mesh's own axes aren't reliably the barrel), its right from the world's up.
	const FVector Port = Mesh->GetSocketLocation(CasingSocketName);
	const FVector Barrel = GetMuzzleTransform(bOffhand).GetUnitAxis(EAxis::X);
	const FVector Right = FVector::CrossProduct(FVector::UpVector, Barrel).GetSafeNormal();
	const FVector Up = FVector::CrossProduct(Barrel, Right).GetSafeNormal();
	const FVector Throw = (Right + Up * CasingEjectUp - Barrel * CasingEjectBack).GetSafeNormal();

	// No two alike: a little off in direction, speed and spin.
	const FVector Direction = FMath::VRandCone(Throw, FMath::DegreesToRadians(CasingEjectSpread));
	const float Speed = CasingEjectSpeed * FMath::FRandRange(1.0f - CasingSpeedVariation, 1.0f + CasingSpeedVariation);
	FVector Velocity = Direction * Speed;
	if (const AActor* Holder = GetOwner())
	{
		Velocity += Holder->GetVelocity();
	}
	const FVector Spin = FMath::VRand() * CasingSpin * FMath::FRandRange(0.5f, 1.0f);

	FActorSpawnParameters Params;
	Params.Owner = this;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (AShellCasing* Casing = GetWorld()->SpawnActor<AShellCasing>(AShellCasing::StaticClass(), Port, Barrel.Rotation(), Params))
	{
		Casing->Launch(CasingMesh, CasingScale, CasingImpactSound, Velocity, Spin, CasingLifeSpan);
	}
}

USkeletalMeshComponent* AWeaponBase::GetFiringMesh() const
{
	return IsOffhandNext() ? OffhandMesh.Get() : WeaponMesh.Get();
}

FTransform AWeaponBase::GetMuzzleTransform(bool bOffhand) const
{
	const USkeletalMeshComponent* Mesh = (bOffhand && OffhandMesh) ? OffhandMesh.Get() : WeaponMesh.Get();
	if (Mesh && Mesh->DoesSocketExist(MuzzleSocketName))
	{
		return Mesh->GetSocketTransform(MuzzleSocketName);
	}
	return GetActorTransform();
}

FVector AWeaponBase::GetMuzzleLocation() const
{
	const USkeletalMeshComponent* FiringMesh = GetFiringMesh();
	if (FiringMesh && FiringMesh->DoesSocketExist(MuzzleSocketName))
	{
		return FiringMesh->GetSocketLocation(MuzzleSocketName);
	}

	// Fall back to the actor origin. Returning zero would put every shot at world
	// origin if the socket were ever renamed — a spectacular and confusing bug.
	return GetActorLocation();
}

void AWeaponBase::GetFriendlyActors(TArray<AActor*>& OutFriends) const
{
	// Only enemies spare each other, and only those with friendly fire off; the player's
	// rounds hit everyone.
	const AEnemyBase* Shooter = Cast<AEnemyBase>(GetOwner());
	if (!Shooter || Shooter->HasFriendlyFire())
	{
		return;
	}
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		OutFriends.Add(*It);
	}
}
