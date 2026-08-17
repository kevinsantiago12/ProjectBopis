// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/WeaponBase.h"
#include "Kismet/GameplayStatics.h"

// Sets default values
AWeaponBase::AWeaponBase()
{
	WeaponMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("WeaponMesh"));
	RootComponent = WeaponMesh;

 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

void AWeaponBase::Fire(const FVector& TraceStart, const FVector& TraceDirection)
{
	/*Fire Sound Effect*/
	if (FireSound && !bUseAnimationDrivenFeedback)
	{
		UGameplayStatics::SpawnSoundAttached(FireSound, WeaponMesh, MuzzleSocketName);
	}

	if (MuzzleFlash && !bUseAnimationDrivenFeedback)
	{
		UGameplayStatics::SpawnEmitterAttached(MuzzleFlash, WeaponMesh, MuzzleSocketName);
	}


	// Lerps between Base and Max Bloom Angle based on 0-1 CurrentBloom
	const float SpreadAngle = FMath::Lerp(BaseSpreadAngle, MaxSpreadAngle, CurrentBloom);

	//UE's built in "Cone on this direction" function, set direction offset
	const FVector SpreadDirection = FMath::VRandCone(TraceDirection, FMath::DegreesToRadians(SpreadAngle));

	//Apply Bloom spread to trace angle
	const FVector TraceEnd = TraceStart + (SpreadDirection * MaxRange);

	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(this);
	QueryParams.AddIgnoredActor(GetOwner());

	FHitResult HitResult;
	const bool bHit = GetWorld()->LineTraceSingleByChannel(HitResult, TraceStart, TraceEnd,
		ECC_Visibility, QueryParams);

	const FVector DebugLineStart = TraceStart + (SpreadDirection * 150.0f);

	DrawDebugLine(GetWorld(), DebugLineStart, bHit ? HitResult.Location : TraceEnd, bHit ?
		FColor::Green : FColor::Red, false, 2.0f, 0, 1.0f);

	if (bHit && HitResult.GetActor())
	{

		UGameplayStatics::ApplyPointDamage(HitResult.GetActor(), BaseDamage, SpreadDirection,
			HitResult, GetInstigatorController(), this, nullptr);
	}

	//Apply semi-auto penalty when violating cadence, adds 0-1 bloom per shot based on Cadence violation ratio
	const float MinTimeBetweenShots = 1.0f / IntendedCadence;
	float BloomToAdd = BloomPerShot;

	if (TimeSinceLastShot < MinTimeBetweenShots)
	{
		const float CadenceViolationRatio = 1.0 - (TimeSinceLastShot / MinTimeBetweenShots);
		BloomToAdd += BloomPerShot * CadenceViolationRatio;
	}

	//Apply Bloom
	CurrentBloom = FMath::Min(1.0f, CurrentBloom + BloomToAdd);
	TimeSinceLastShot = 0.0f;
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

