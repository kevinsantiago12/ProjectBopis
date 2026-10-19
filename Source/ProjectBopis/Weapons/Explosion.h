#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Explosion.generated.h"

class UParticleSystem;
class USoundBase;
class UCameraShakeBase;

/** A blast. Spawned where something goes off (a grenade, a launcher round), it hurts everything
    in reach that it can see, throws loose physics, plays its effects and is gone. Set the
    Instigator when spawning, so kills are credited (and the player's kills slow time). */
UCLASS(Blueprintable)
class PROJECTBOPIS_API AExplosion : public AActor
{
	GENERATED_BODY()

public:
	AExplosion();

protected:
	virtual void BeginPlay() override;

	/** Everything within this many cm can be hurt. */
	UPROPERTY(EditDefaultsOnly, Category = "Explosion", meta = (ClampMin = "0.0"))
	float Radius = 600.0f;

	/** Full damage inside this; it falls off from here out to Radius. */
	UPROPERTY(EditDefaultsOnly, Category = "Explosion", meta = (ClampMin = "0.0"))
	float FullDamageRadius = 200.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Explosion", meta = (ClampMin = "0.0"))
	float Damage = 250.0f;

	/** Damage at the very edge of Radius, as a fraction of Damage. */
	UPROPERTY(EditDefaultsOnly, Category = "Explosion", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float EdgeDamageFraction = 0.2f;

	/** Push on loose physics objects at the centre (velocity change, cm/s), less further out. */
	UPROPERTY(EditDefaultsOnly, Category = "Explosion", meta = (ClampMin = "0.0"))
	float PhysicsImpulse = 1500.0f;

	/** Real seconds of slow motion when the player's blast kills someone. 0: none. */
	UPROPERTY(EditDefaultsOnly, Category = "Explosion", meta = (ClampMin = "0.0"))
	float KillSlowMotionDuration = 1.5f;

	/** Bodies it kills (or already dead in it) are thrown: outward speed (cm/s) at the centre... */
	UPROPERTY(EditDefaultsOnly, Category = "Explosion", meta = (ClampMin = "0.0"))
	float ThrowSpeed = 900.0f;

	/** ...and upward (cm/s). Both fall off with distance like the damage. */
	UPROPERTY(EditDefaultsOnly, Category = "Explosion", meta = (ClampMin = "0.0"))
	float LiftSpeed = 800.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Explosion|Effects")
	TObjectPtr<UParticleSystem> ExplosionEffect;

	UPROPERTY(EditDefaultsOnly, Category = "Explosion|Effects", meta = (ClampMin = "0.0"))
	float EffectScale = 1.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Explosion|Effects")
	TObjectPtr<USoundBase> ExplosionSound;

	/** Shakes the camera of anyone within CameraShakeRadius, harder closer in. */
	UPROPERTY(EditDefaultsOnly, Category = "Explosion|Effects")
	TSubclassOf<UCameraShakeBase> CameraShake;

	UPROPERTY(EditDefaultsOnly, Category = "Explosion|Effects", meta = (ClampMin = "0.0"))
	float CameraShakeRadius = 2000.0f;

private:
	void Detonate();

	/** Nothing solid between the blast and Target. Other things caught in it don't shield. */
	bool CanReach(const FVector& Center, const AActor* Target, const TArray<AActor*>& Caught) const;
};
