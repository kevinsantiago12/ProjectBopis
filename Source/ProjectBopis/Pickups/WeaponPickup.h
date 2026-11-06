// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WeaponPickup.generated.h"

class AWeaponBase;
class USphereComponent;
class USkeletalMeshComponent;
class USoundBase;
class UWeaponHolderComponent;

UENUM(BlueprintType)
enum class EPickupAmmoMode : uint8
{
	/** Exactly FixedRounds. */
	Fixed,
	/** BaseMagazines of the weapon's magazine, plus 0 to RandomExtraMagazines more, rolled on spawn. */
	Random
};

/**
 *  A weapon lying in the world (placed, or later dropped by an enemy). Walking over it:
 *  - not carried: the weapon joins the backpack with a magazine from these rounds, the rest to the pool;
 *  - carried, with a dual version not yet carried: the dual version is unlocked;
 *  - otherwise: the rounds go to the shared ammo pool, up to its maximum, and the pickup goes.
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

	/** Random mode: magazines this always holds. 1 = a full magazine. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pickup",
		meta = (ClampMin = "0.0", EditCondition = "AmmoMode == EPickupAmmoMode::Random"))
	float BaseMagazines = 1.0f;

	/** Random mode: up to this many magazines on top, rolled on spawn. 0.5 = up to half a magazine. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pickup",
		meta = (ClampMin = "0.0", EditCondition = "AmmoMode == EPickupAmmoMode::Random"))
	float RandomExtraMagazines = 0.5f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Pickup")
	TObjectPtr<USoundBase> PickupSound;

private:

	/** Rounds in this pickup. Set in BeginPlay. */
	int32 RoundsRemaining = 0;

	/** Gives a weapon the holder doesn't carry: a magazine from this pickup's rounds, the rest to the pool. */
	void GiveNewWeapon(UWeaponHolderComponent* Holder, TSubclassOf<AWeaponBase> NewClass);

	void Consume();
};
