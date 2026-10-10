// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WeaponDrop.generated.h"

class AWeaponBase;
class AWeaponPickup;
class UBoxComponent;
class USkeletalMeshComponent;

/**
 *  A gun knocked out of a dead hand: tumbles on physics, then turns into a pickup where it
 *  comes to rest. Separate from AWeaponPickup so placed pickups keep their trigger as root.
 */
UCLASS()
class PROJECTBOPIS_API AWeaponDrop : public AActor
{
	GENERATED_BODY()

public:

	AWeaponDrop();

	/** Sets which gun this is and throws it. Call right after spawning. */
	void Launch(TSubclassOf<AWeaponBase> InWeaponClass, TSubclassOf<AWeaponPickup> InPickupClass,
		const FVector& Velocity, const FVector& AngularVelocityDegrees);

	virtual void Tick(float DeltaSeconds) override;

protected:

	/** Physics body, fitted to the gun's bounds at launch. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Drop")
	TObjectPtr<UBoxComponent> Body;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Drop")
	TObjectPtr<USkeletalMeshComponent> MeshComponent;

	/** Below this speed (cm/s) the gun counts as landed and becomes a pickup. */
	UPROPERTY(EditAnywhere, Category = "Drop", meta = (ClampMin = "0.0"))
	float SettleSpeed = 20.0f;

	/** Seconds it must stay below SettleSpeed before it counts as landed, so the top of a
	    bounce isn't mistaken for rest. */
	UPROPERTY(EditAnywhere, Category = "Drop", meta = (ClampMin = "0.0"))
	float SettleTime = 0.25f;

	/** How far below the gun to look for the floor when it becomes a pickup. */
	UPROPERTY(EditAnywhere, Category = "Drop", meta = (ClampMin = "0.0"))
	float FloorSnapDistance = 150.0f;

	/** Seconds in the air before it may settle, so it isn't caught at the top of its arc. */
	UPROPERTY(EditAnywhere, Category = "Drop", meta = (ClampMin = "0.0"))
	float MinFlightTime = 0.3f;

	/** Becomes a pickup after this long regardless, in case it never quite stops. */
	UPROPERTY(EditAnywhere, Category = "Drop", meta = (ClampMin = "0.0"))
	float MaxFlightTime = 3.0f;

private:

	void BecomePickup();

	TSubclassOf<AWeaponBase> WeaponClass;
	TSubclassOf<AWeaponPickup> PickupClass;
	float FlightTime = 0.0f;
	float SlowTime = 0.0f;
};
