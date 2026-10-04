// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Weapons/WeaponBase.h"
#include "WeaponHolderComponent.generated.h"

class AWeaponBase;

UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class PROJECTBOPIS_API UWeaponHolderComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UWeaponHolderComponent();

	/** Adds a weapon to the carried list; auto-equips it if nothing is currently equipped.
	Returns false if at capacity. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Holder")
	bool AddWeapon(AWeaponBase* NewWeapon);

	/** Equips an already-carried weapon. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Holder")
	void EquipWeapon(AWeaponBase* WeaponToEquip);

	/** Fires the equipped weapon. See EFireResult for why a shot may not have happened. */
	UFUNCTION(BlueprintCallable, Category = "WeaponHolder")
	EFireResult FireEquippedWeapon();

	/** Reloads the equipped weapon. Returns false if it couldn't start. */
	UFUNCTION(BlueprintCallable, Category = "WeaponHolder")
	bool ReloadEquippedWeapon();

	/** Return the currently equipped weapon, if any. */
	AWeaponBase* GetEquippedWeapon() const { return EquippedWeapon;  }

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	/** Attaches the equipped weapon to the owner's hand socket and applies its grip offsets. */
	void AttachWeaponToHand();

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	int32 MaxCarriedWeapons = 2;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon Holder")
	TArray<TObjectPtr<AWeaponBase>> CarriedWeapons;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon Holder")
	TObjectPtr<AWeaponBase> EquippedWeapon;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	FName WeaponAttachSocketName = TEXT("hand_r");

	/** Socket the off-hand weapon of a dual-wield pair attaches to. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	FName OffhandAttachSocketName = TEXT("hand_l");

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	TSubclassOf<AWeaponBase> StartingWeaponClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	float CrosshairViewportPositionY = 0.5f;

	/** Shots never converge on anything nearer than this. Against a close wall the
	    muzzle can sit past the hit point, and converging would aim the shot backwards. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	float MinConvergenceDistance = 200.0f;

	/** Blocks the shot when the muzzle has clipped through geometry — stops the player
	    firing through a wall they're pressed against. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	bool bBlockShotWhenMuzzleObstructed = true;

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

		
};
