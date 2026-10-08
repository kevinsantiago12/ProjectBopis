// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Weapons/WeaponBase.h"
#include "AmmoPickup.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class USoundBase;

/**
 *  Ammo lying in the world. Walking over it adds its rounds to the collector's shared
 *  pool for its type, as many as fit under the cap. Whatever doesn't fit stays in the
 *  pickup, which is only destroyed once empty. Never respawns.
 */
UCLASS()
class PROJECTBOPIS_API AAmmoPickup : public AActor
{
	GENERATED_BODY()

public:

	AAmmoPickup();

protected:

	virtual void BeginPlay() override;

	UFUNCTION()
	void OnTriggerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	/** Gives what fits to the collector's ammo pool. */
	void TryGiveAmmo(AActor* Collector);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Pickup")
	TObjectPtr<USphereComponent> TriggerComponent;

	/** The visible box or rounds. Never collides; the trigger does the work. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Pickup")
	TObjectPtr<UStaticMeshComponent> MeshComponent;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pickup")
	EAmmoType AmmoType = EAmmoType::Pistol;

	/** Rounds in this pickup. Counts down as they're taken. Editable per placed
	    instance, so one Blueprint per type covers every box size. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pickup", meta = (ClampMin = "1"))
	int32 Amount = 24;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Pickup")
	TObjectPtr<USoundBase> PickupSound;
};
