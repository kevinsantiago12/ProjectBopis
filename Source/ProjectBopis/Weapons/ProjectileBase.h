// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProjectileBase.generated.h"

class USphereComponent;
class UProjectileMovementComponent;
class UMaterialInterface;
class AWeaponBase;

UCLASS()
class PROJECTBOPIS_API AProjectileBase : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AProjectileBase();

	void SetDamage(float InDamage) { Damage = InDamage; }

	/** The weapon that fired this round. Damage at impact comes from its falloff curve,
	    measured from where the round spawned — so shotgun pellets keep their falloff. */
	void SetSourceWeapon(AWeaponBase* Weapon) { SourceWeapon = Weapon; }

	/** Permanently stops this projectile colliding with or damaging the given actor.
	    Used for whoever fired it, since the round spawns inside their own collision. */
	UFUNCTION(BlueprintCallable, Category = "Projectile")
	void AddIgnoredActor(AActor* ActorToIgnore);

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnHit(UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComponent,
		FVector NormalImpulse, const FHitResult& Hit);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
	TObjectPtr<USphereComponent> CollisionComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
	TObjectPtr<UProjectileMovementComponent> ProjectileMovement;

	/** Splash radius on impact. 0 = no splash: ordinary bullets leave this at 0. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile|Fragment", meta = (ClampMin = "0.0"))
	float FragmentRadius = 0.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile|Fragment", meta = (ClampMin = "0.0"))
	float FragmentDamage = 0.0f;

	/** Hide the round's visuals at normal speed and show them only while world time is
	    slowed (Focus). Collision is never affected. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile|Visibility")
	bool bShowOnlyInSlowMotion = true;

	/** Time dilation below which the round becomes visible. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile|Visibility", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float SlowMotionThreshold = 0.9f;

	/** Keep particle effects (tracers, trails) visible at normal speed — only meshes hide.
	    Off by default: the whole round is a Focus-only sight. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile|Visibility")
	bool bKeepEffectsVisible = false;

	void UpdateVisibility();

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile|Impact")
	TObjectPtr<UMaterialInterface> HitDecalMaterial;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile|Impact")
	FVector DecalSize = FVector(5.0f, 5.0f, 5.0f);

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile|Impact")
	float DecalLifeSpan = 10.0f;

	float Damage = 20.0f;

	/** Actors this projectile must never collide with or damage — the firer and their weapon. */
	UPROPERTY()
	TArray<TObjectPtr<AActor>> IgnoredActors;

	TWeakObjectPtr<AWeaponBase> SourceWeapon;
	FVector SpawnLocation = FVector::ZeroVector;
	bool bVisualsShown = true;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
