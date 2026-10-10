// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WeaponPickup.generated.h"

class AWeaponBase;
class USphereComponent;
class USkeletalMeshComponent;
class USoundBase;

UENUM(BlueprintType)
enum class EPickupAmmoMode : uint8
{
	/** Exactly FixedRounds. */
	Fixed,
	/** Between half a magazine and a full magazine of the weapon, rolled on spawn. */
	Random
};

/**
 *  A weapon lying in the world (placed, or later dropped by an enemy). Walking over it:
 *  - not carried: the weapon joins the backpack with these rounds in its magazine;
 *  - carried, with a dual version not yet carried: the dual version is unlocked;
 *  - otherwise: the rounds go to the shared ammo pool, and what doesn't fit stays here.
 */
UCLASS()
class PROJECTBOPIS_API AWeaponPickup : public AActor
{
	GENERATED_BODY()

public:

	AWeaponPickup();

	/** Which weapon this is. For pickups spawned at runtime (drops), before FinishSpawning. */
	void SetWeaponClass(TSubclassOf<AWeaponBase> InWeaponClass) { WeaponClass = InWeaponClass; }

	virtual void OnConstruction(const FTransform& Transform) override;

protected:

	virtual void BeginPlay() override;

	UFUNCTION()
	void OnTriggerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	void TryGive(AActor* Collector);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Pickup")
	TObjectPtr<USphereComponent> TriggerComponent;

	/** Shows the weapon's own mesh, taken from WeaponClass — no per-pickup mesh setup. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Pickup")
	TObjectPtr<USkeletalMeshComponent> MeshComponent;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pickup")
	TSubclassOf<AWeaponBase> WeaponClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pickup")
	EPickupAmmoMode AmmoMode = EPickupAmmoMode::Random;

	/** Rounds when AmmoMode is Fixed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pickup",
		meta = (ClampMin = "0", EditCondition = "AmmoMode == EPickupAmmoMode::Fixed"))
	int32 FixedRounds = 12;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Pickup")
	TObjectPtr<USoundBase> PickupSound;

private:

	/** Rounds still in this pickup. Set in BeginPlay, counts down as ammo is taken. */
	int32 RoundsRemaining = 0;

	void Consume();
};
