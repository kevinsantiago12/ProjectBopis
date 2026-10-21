#include "Weapons/Grenade.h"

#include "Components/SphereComponent.h"
#include "EngineUtils.h"
#include "Enemies/BarkSet.h"
#include "Enemies/EnemyBase.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Weapons/Explosion.h"
#include "Weapons/WeaponBase.h"

AGrenade::AGrenade()
{
	CollisionComponent->InitSphereRadius(6.0f);

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(CollisionComponent);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	// A thrown arc: gravity, bounces that lose energy, and a roll that slows to a stop.
	ProjectileMovement->InitialSpeed = 1500.0f;
	ProjectileMovement->MaxSpeed = 4000.0f;
	ProjectileMovement->ProjectileGravityScale = 1.0f;
	ProjectileMovement->bShouldBounce = true;
	ProjectileMovement->Bounciness = 0.35f;
	ProjectileMovement->Friction = 0.4f;

	// Always seen, and never a near miss.
	bShowOnlyInSlowMotion = false;
	NearMissRadius = 0.0f;

	// The fuse decides; this is only a backstop for a round that never hits anything.
	InitialLifeSpan = 20.0f;
}

void AGrenade::BeginPlay()
{
	Super::BeginPlay();

	ProjectileMovement->OnProjectileBounce.AddDynamic(this, &AGrenade::OnBounce);

	if (FuseTime > 0.0f)
	{
		GetWorldTimerManager().SetTimer(FuseTimer, this, &AGrenade::Explode, FuseTime, false);
	}
}

void AGrenade::OnHit(UPrimitiveComponent* HitComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit)
{
	// Never on the thrower (the same backstop as a bullet's). A fused grenade just bounces.
	if (OtherActor && IgnoredActors.Contains(OtherActor))
	{
		return;
	}
	if (bExplodeOnImpact)
	{
		Explode();
	}
}

void AGrenade::OnBounce(const FHitResult& ImpactResult, const FVector& ImpactVelocity)
{
	if (BounceSound && ImpactVelocity.Size() >= MinBounceSoundSpeed)
	{
		UGameplayStatics::PlaySoundAtLocation(this, BounceSound, ImpactResult.ImpactPoint);
	}

	// First landing of a fused grenade: the nearest enemy in the fight shouts a warning.
	if (bWarned || bExplodeOnImpact)
	{
		return;
	}
	bWarned = true;
	AEnemyBase* Nearest = nullptr;
	float NearestDistance = WarnRadius;
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		const float Distance = FVector::Dist(It->GetActorLocation(), GetActorLocation());
		if (!It->IsDead() && It->IsAlerted() && Distance <= NearestDistance)
		{
			Nearest = *It;
			NearestDistance = Distance;
		}
	}
	if (Nearest)
	{
		Nearest->Bark(EBarkType::Grenade);
	}
}

float AGrenade::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
	AController* EventInstigator, AActor* DamageCauser)
{
	if (bExploded || DamageAmount <= 0.0f)
	{
		return 0.0f;
	}

	// Another blast: a beat later, so a chain ripples rather than going off as one.
	if (Cast<AExplosion>(DamageCauser))
	{
		GetWorldTimerManager().SetTimer(FuseTimer, this, &AGrenade::Explode, FMath::Max(ChainDelay, 0.01f), false);
		return DamageAmount;
	}

	// Shot: it goes off now, and whoever shot it owns the blast (an enemy's grenade shot
	// mid-air by the player counts as the player's kill).
	if (EventInstigator && EventInstigator->GetPawn())
	{
		SetInstigator(EventInstigator->GetPawn());
	}
	Explode();
	return DamageAmount;
}

void AGrenade::Launch(const FVector& Velocity)
{
	ProjectileMovement->Velocity = Velocity;
}

void AGrenade::Explode()
{
	if (bExploded)
	{
		return;
	}
	bExploded = true;
	GetWorldTimerManager().ClearTimer(FuseTimer);

	if (ExplosionClass)
	{
		FActorSpawnParameters SpawnParams;
		SpawnParams.Instigator = GetInstigator();
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		GetWorld()->SpawnActor<AExplosion>(ExplosionClass, GetActorLocation(), FRotator::ZeroRotator, SpawnParams);
	}
	Destroy();
}
