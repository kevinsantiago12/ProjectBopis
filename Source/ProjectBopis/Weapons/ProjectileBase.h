// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProjectileBase.generated.h"

class USphereComponent;
class UProjectileMovementComponent;
class UMaterialInterface;

UCLASS()
class PROJECTBOPIS_API AProjectileBase : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AProjectileBase();

	void SetDamage(float InDamage) { Damage = InDamage; }

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

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile")
	float FragmentRadius = 150.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Projectile")
	float FragmentDamage = 10.0f;

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

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
