// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WeaponBase.generated.h"

class USoundBase;
class UParticleSystem;
class UMaterialInterface;
class UAnimSequence;
class AProjectileBase;

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

	EWeaponFireMode GetFireMode() const { return FireMode; }
	bool HasZoom() const { return bHasZoom; }
	float GetZoomedFOV() const { return ZoomedFOV; }
	bool UsesAnimationDrivenFeedback() const { return bUseAnimationDrivenFeedback; }
	FVector GetGripLocationOffset() const { return GripLocationOffset; }
	FRotator GetGripRotationOffset() const { return GripRotationOffset; }

	/** Whether enough time has passed since the last shot for this weapon to fire again. */
	UFUNCTION(BlueprintCallable, Category = "Weapon")
	bool CanFire() const;

	/** Fires the weapon. Returns false if the shot was blocked by the fire-rate cap. */
	UFUNCTION(BlueprintCallable, Category = "Weapon")
	bool Fire(const FVector& TraceStart, const FVector& TraceDirection);
	void FireHitscan(const FVector& TraceStart, const FVector& SpreadDirection);
	void FireProjectile(const FVector& TraceStart, const FVector& SpreadDirection);

	float GetCurrentBloom() const { return CurrentBloom; }

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<USkeletalMeshComponent> WeaponMesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	EWeaponFireMode FireMode = EWeaponFireMode::Semi;

	/** Minimum seconds between shots — a hard mechanical cap; tapping faster than this does nothing.
	    Should be shorter than IntendedTimeBetweenShots, which is the softer accuracy-based limit.
	    Set to 0 to disable the cap entirely. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float TimeBetweenShots = 0.125f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float BaseDamage = 10.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float MaxRange = 5000.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	bool bHasZoom = false;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float ZoomedFOV = 40.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	bool bIsProjectileWeapon = false;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TSubclassOf<AProjectileBase> ProjectileClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	FVector GripLocationOffset = FVector::ZeroVector;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	FRotator GripRotationOffset = FRotator::ZeroRotator;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<USoundBase> FireSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<UParticleSystem> MuzzleFlash;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	FName MuzzleSocketName = TEXT("Muzzle");

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	bool bUseAnimationDrivenFeedback = false;

	/** Played on the weapon's own mesh when firing, if this weapon uses animation-driven feedback. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<UAnimSequence> FireAnimation;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<UMaterialInterface> HitDecalMaterial;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	FVector DecalSize = FVector(5.0f, 5.0, 5.0f);

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	float DecalLifeSpan = 10.0f;

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

	/** Seconds between shots this weapon is "meant" to be fired at - firing sooner adds extra bloom penalty.
	    Should be longer than TimeBetweenShots, which is the hard mechanical cap. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float IntendedTimeBetweenShots = 0.167f;

	float CurrentBloom = 0.0f;
	float TimeSinceLastShot = 0.0f;


public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
