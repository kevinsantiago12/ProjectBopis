// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/WeaponBase.h"
#include "Kismet/GameplayStatics.h"
#include "Components/DecalComponent.h"
#include "Weapons/ProjectileBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"


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

bool AWeaponBase::Fire(const FVector& TraceStart, const FVector& TraceDirection)
{
	if (!CanFire())
	{
		return false;
	}

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

	if (bIsProjectileWeapon && ProjectileClass)
	{
		FireProjectile(TraceStart, SpreadDirection);
	}
	else
	{
		FireHitscan(TraceStart, SpreadDirection);
	}

	float BloomToAdd = BloomPerShot;

	if (IntendedTimeBetweenShots > 0.0f && TimeSinceLastShot < IntendedTimeBetweenShots)
	{
		const float CadenceViolationRatio = 1.0f - (TimeSinceLastShot / IntendedTimeBetweenShots);
		BloomToAdd += BloomPerShot * CadenceViolationRatio;
	}

	CurrentBloom = FMath::Min(1.0f, CurrentBloom + BloomToAdd);
	TimeSinceLastShot = 0.0f;

	return true;
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
			UGameplayStatics::ApplyPointDamage(HitResult.GetActor(), BaseDamage, SpreadDirection,
				HitResult, GetInstigatorController(), this, nullptr);
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

	const FVector MuzzleLocation = WeaponMesh->DoesSocketExist(MuzzleSocketName)
		? WeaponMesh->GetSocketLocation(MuzzleSocketName)
		: WeaponMesh->GetComponentLocation();

	// Aim from the muzzle toward where the camera-based shot would have landed, so the
	// projectile converges on the reticle instead of flying parallel to the view.
	const FVector AimPoint = TraceStart + (SpreadDirection * MaxRange);
	const FRotator SpawnRotation = (AimPoint - MuzzleLocation).Rotation();

	FActorSpawnParameters SpawnParams;
	SpawnParams.Owner = this;
	SpawnParams.Instigator = GetInstigator();

	if (AProjectileBase* Projectile = World->SpawnActor<AProjectileBase>(ProjectileClass, MuzzleLocation,
		SpawnRotation, SpawnParams))
	{
		Projectile->SetDamage(BaseDamage);
	}
}

// Called when the game starts or when spawned
void AWeaponBase::BeginPlay()
{
	Super::BeginPlay();
	
}

// Called every frame
void AWeaponBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(1, 0.0f, FColor::Yellow, FString::Printf(TEXT("Bloom: %.2f"), CurrentBloom));
	}

	TimeSinceLastShot += DeltaTime;

	if (TimeSinceLastShot >= BloomDecayDelay && CurrentBloom > 0.0f)
	{
		CurrentBloom = FMath::Max(0.0f, CurrentBloom - BloomDecayRate * DeltaTime);
	}
}

