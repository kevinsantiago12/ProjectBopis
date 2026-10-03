// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/WeaponBase.h"
#include "Kismet/GameplayStatics.h"
#include "Components/DecalComponent.h"
#include "Weapons/ProjectileBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Particles/ParticleSystemComponent.h"
#include "TimerManager.h"


static TAutoConsoleVariable<bool> CVarShowWeaponTrace(TEXT("Weapon.ShowTrace"),
	true,TEXT("Draw debug trace lines for weapon fire."),ECVF_Cheat);

// Sets default values
AWeaponBase::AWeaponBase()
{
	WeaponMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("WeaponMesh"));
	RootComponent = WeaponMesh;

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
		&& (bInfiniteReserve || CurrentReserveAmmo > 0);
}

bool AWeaponBase::Reload()
{
	if (!CanReload())
	{
		return false;
	}

	bIsReloading = true;

	if (ReloadStyle == EReloadStyle::PerRound)
	{
		// First round lands after the wind-up; LoadRound re-arms itself for the rest.
		GetWorldTimerManager().SetTimer(ReloadTimerHandle, this,
			&AWeaponBase::LoadRound, ReloadStartDelay + TimePerRound, false);
	}
	else
	{
		GetWorldTimerManager().SetTimer(ReloadTimerHandle, this,
			&AWeaponBase::FinishReload, ReloadDuration, false);
	}

	return true;
}

void AWeaponBase::LoadRound()
{
	++CurrentAmmoInMagazine;

	if (!bInfiniteReserve)
	{
		--CurrentReserveAmmo;
	}

	if (CanAcceptRound())
	{
		GetWorldTimerManager().SetTimer(ReloadTimerHandle, this,
			&AWeaponBase::LoadRound, TimePerRound, false);
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
	const int32 Transfer = bInfiniteReserve ? Needed : FMath::Min(Needed, CurrentReserveAmmo);

	CurrentAmmoInMagazine += Transfer;

	if (!bInfiniteReserve)
	{
		CurrentReserveAmmo -= Transfer;
	}

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

EFireResult AWeaponBase::Fire(const FVector& TraceStart, const FVector& TraceDirection)
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

	if (!bUseAnimationDrivenFeedback)
	{
		if (FireSound)
		{
			UGameplayStatics::SpawnSoundAttached(FireSound, WeaponMesh, MuzzleSocketName);
		}

		if (MuzzleFlash)
		{
			UGameplayStatics::SpawnEmitterAttached(MuzzleFlash, WeaponMesh, MuzzleSocketName);
		}
	}
	else if (FireAnimation)
	{
		WeaponMesh->PlayAnimation(FireAnimation, false);
	}

	const float SpreadAngle = FMath::Lerp(BaseSpreadAngle, MaxSpreadAngle, CurrentBloom);
	const FVector SpreadDirection = FMath::VRandCone(TraceDirection, FMath::DegreesToRadians(SpreadAngle));

	// Bloom displaces the pattern centre; the pellets fan out around it. One pellet
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

	float BloomToAdd = BloomPerShot;

	if (IntendedTimeBetweenShots > 0.0f && TimeSinceLastShot < IntendedTimeBetweenShots)
	{
		const float CadenceViolationRatio = 1.0f - (TimeSinceLastShot / IntendedTimeBetweenShots);
		BloomToAdd += BloomPerShot * CadenceViolationRatio;
	}

	CurrentBloom = FMath::Min(1.0f, CurrentBloom + BloomToAdd);
	TimeSinceLastShot = 0.0f;

	return EFireResult::Fired;
}

void AWeaponBase::FireHitscan(const FVector& TraceStart, const FVector& SpreadDirection)
{
	const FVector TraceEnd = TraceStart + (SpreadDirection * MaxRange);

	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(this);
	QueryParams.AddIgnoredActor(GetOwner());

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
		if (HitDecalMaterial)
		{
			if (UDecalComponent* SpawnedDecal = UGameplayStatics::SpawnDecalAtLocation(this, HitDecalMaterial, DecalSize,
				HitResult.Location, HitResult.ImpactNormal.Rotation(), DecalLifeSpan))
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

		// Explicit, so the round can't hit whoever fired it even if Instigator is unset.
		Projectile->AddIgnoredActor(GetInstigator());
		Projectile->AddIgnoredActor(GetOwner());
		Projectile->AddIgnoredActor(this);
	}
}

// Called when the game starts or when spawned
void AWeaponBase::BeginPlay()
{
	Super::BeginPlay();

	// Not in the constructor — MagazineSize is a per-Blueprint default and isn't
	// applied yet at construction time.
	CurrentAmmoInMagazine = MagazineSize;
	CurrentReserveAmmo = StartingReserveAmmo;
}

// Called every frame
void AWeaponBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(1, 0.0f, FColor::Yellow, FString::Printf(TEXT("Bloom: %.2f"), CurrentBloom));
		GEngine->AddOnScreenDebugMessage(2, 0.0f, FColor::Cyan, FString::Printf(TEXT("Ammo: %d / %d%s"),
			CurrentAmmoInMagazine, CurrentReserveAmmo, bIsReloading ? TEXT("  [RELOADING]") : TEXT("")));
	}

	TimeSinceLastShot += DeltaTime;

	if (TimeSinceLastShot >= BloomDecayDelay && CurrentBloom > 0.0f)
	{
		CurrentBloom = FMath::Max(0.0f, CurrentBloom - BloomDecayRate * DeltaTime);
	}
}


FVector AWeaponBase::GetMuzzleLocation() const
{
	if (WeaponMesh && WeaponMesh->DoesSocketExist(MuzzleSocketName))
	{
		return WeaponMesh->GetSocketLocation(MuzzleSocketName);
	}

	// Fall back to the actor origin. Returning zero would put every shot at world
	// origin if the socket were ever renamed — a spectacular and confusing bug.
	return GetActorLocation();
}
