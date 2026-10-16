// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Subsystems/WorldSubsystem.h"
#include "ShellCasing.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class UStaticMesh;
class USoundBase;

/**
 *  A spent casing thrown from a gun's ejection port: a small physics body that bounces,
 *  rolls and settles, then goes after its life span. The world keeps at most
 *  UShellCasingSubsystem::MaxCasings; the oldest go first.
 */
UCLASS()
class PROJECTBOPIS_API AShellCasing : public AActor
{
	GENERATED_BODY()

public:
	AShellCasing();

	/** Takes the casing's mesh and bounce sound, sizes its body to the mesh, and throws it. */
	void Launch(UStaticMesh* Mesh, float Scale, USoundBase* InImpactSound, const FVector& Velocity,
		const FVector& AngularVelocityDegrees, float LifeSpan);

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnBodyHit(UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
		FVector NormalImpulse, const FHitResult& Hit);

private:
	UPROPERTY(VisibleAnywhere, Category = "Casing")
	TObjectPtr<UBoxComponent> Body;

	UPROPERTY(VisibleAnywhere, Category = "Casing")
	TObjectPtr<UStaticMeshComponent> MeshComponent;

	UPROPERTY(Transient)
	TObjectPtr<USoundBase> ImpactSound;

	float LastImpactSoundTime = -1000.0f;
	int32 ImpactSoundsLeft = 3;
};

/** Keeps the number of casings in the world down: past MaxCasings, the oldest goes. */
UCLASS()
class PROJECTBOPIS_API UShellCasingSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	static constexpr int32 MaxCasings = 64;

	void Register(AShellCasing* Casing);

private:
	/** Oldest first. Weak, so casings that run out their life span simply drop out. */
	TArray<TWeakObjectPtr<AShellCasing>> Casings;
};
