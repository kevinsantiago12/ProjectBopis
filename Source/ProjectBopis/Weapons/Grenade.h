#pragma once

#include "CoreMinimal.h"
#include "Weapons/ProjectileBase.h"
#include "Grenade.generated.h"

class AExplosion;
class UStaticMeshComponent;
class USoundBase;

/** A grenade: thrown (bounces, goes off on a fuse) or launched (goes off on impact). Either
    can be shot, which sets it off on the spot; another explosion sets it off a beat later. */
UCLASS()
class PROJECTBOPIS_API AGrenade : public AProjectileBase
{
	GENERATED_BODY()

public:
	AGrenade();

	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
		AController* EventInstigator, AActor* DamageCauser) override;

	/** Sets it off now: spawns the explosion (credited to the Instigator) and goes. */
	void Explode();

	/** Sends it off at this velocity (cm/s), in place of its launch speed. */
	void Launch(const FVector& Velocity);

protected:
	virtual void BeginPlay() override;

	virtual void OnHit(UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComponent,
		FVector NormalImpulse, const FHitResult& Hit) override;

	UFUNCTION()
	void OnBounce(const FHitResult& ImpactResult, const FVector& ImpactVelocity);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Grenade")
	TObjectPtr<UStaticMeshComponent> Mesh;

	/** What it sets off. */
	UPROPERTY(EditDefaultsOnly, Category = "Grenade")
	TSubclassOf<AExplosion> ExplosionClass;

	/** Seconds from spawn to going off. 0: no fuse (impact rounds). */
	UPROPERTY(EditDefaultsOnly, Category = "Grenade", meta = (ClampMin = "0.0"))
	float FuseTime = 2.5f;

	/** Goes off on the first thing it hits (launcher rounds) instead of bouncing. */
	UPROPERTY(EditDefaultsOnly, Category = "Grenade")
	bool bExplodeOnImpact = false;

	/** Caught in another blast: goes off this many seconds later, so chains ripple. */
	UPROPERTY(EditDefaultsOnly, Category = "Grenade", meta = (ClampMin = "0.0"))
	float ChainDelay = 0.15f;

	UPROPERTY(EditDefaultsOnly, Category = "Grenade|Sound")
	TObjectPtr<USoundBase> BounceSound;

	/** Bounces slower than this (cm/s) are silent, so a rolling grenade doesn't rattle. */
	UPROPERTY(EditDefaultsOnly, Category = "Grenade|Sound", meta = (ClampMin = "0.0"))
	float MinBounceSoundSpeed = 150.0f;

	/** On first landing, the nearest enemy in the fight within this (cm) shouts a warning. */
	UPROPERTY(EditDefaultsOnly, Category = "Grenade", meta = (ClampMin = "0.0"))
	float WarnRadius = 800.0f;

private:
	bool bExploded = false;
	bool bWarned = false;
	FTimerHandle FuseTimer;
};
