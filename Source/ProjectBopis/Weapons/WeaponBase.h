// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WeaponBase.generated.h"

class USoundBase;
class UParticleSystem;

UENUM(BlueprintType)
enum class EWeaponFireMode : uint8
{
	Semi,
	Auto
};

UCLASS()
class PROJECTBOPIS_API AWeaponBase : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AWeaponBase();

	/** Returns the weapon's mesh component **/
	USkeletalMeshComponent* GetWeaponMesh() const { return WeaponMesh; };

	bool HasZoom() const { return bHasZoom; }
	float GetZoomedFOV() const { return ZoomedFOV; }

	UFUNCTION(BlueprintCallable, Category = "Weapon")
	void Fire(const FVector& TraceStart, const FVector& TraceDirection);

	float GetCurrentBloom() const { return CurrentBloom; }

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<USkeletalMeshComponent> WeaponMesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	EWeaponFireMode FireMode = EWeaponFireMode::Semi;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float BaseDamage = 10.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float MaxRange = 5000.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	bool bHasZoom = false;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float ZoomedFOV = 40.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<USoundBase> FireSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<UParticleSystem> MuzzleFlash;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	FName MuzzleSocketName = TEXT("Muzzle");

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	bool bUseAnimationDrivenFeedback = false;

	/** Accuracy cone at zero bloom - best-case spread, in degrees. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float BaseSpreadAngle = 0.5f;

	/** Accuracy cont at full bloom - worst-case spread, in degress. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float MaxSpreadAngle = 5.0f;

	/** Bloom (0-1) added per shot fired. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float BloomPerShot = 0.15f;

	/** Bloom recovered per second while not firing (after the decay delay). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float BloomDecayRate = 0.6f;

	/** Grace period after the last shot before bloom start decaying. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float BloomDecayDelay = 0.3f;

	/** Shots per second this weapon is "meant" to be fired at - exceeding this adds extra bloom penalty. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float IntendedCadence = 6.0f;

	float CurrentBloom = 0.0f;
	float TimeSinceLastShot = 0.0f;


public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
