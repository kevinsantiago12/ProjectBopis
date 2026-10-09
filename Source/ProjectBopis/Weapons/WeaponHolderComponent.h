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
	    No carry limit (magic backpack). bAddStartingReserve puts the weapon's
	    StartingReserveAmmo into the pool (pickups pass false: they bring their own rounds).
	    Returns false if it's null or already carried. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Holder")
	bool AddWeapon(AWeaponBase* NewWeapon, bool bAddStartingReserve = true);

	/** Equips an already-carried weapon. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Holder")
	void EquipWeapon(AWeaponBase* WeaponToEquip);

	/** Equips the next carried weapon in Slot: the first one if another slot is equipped,
	    otherwise the one after the equipped weapon, wrapping round. Returns false if
	    nothing is carried in that slot. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Holder")
	bool SelectSlot(int32 Slot);

	/** The carried weapon of exactly this class, or null. */
	UFUNCTION(BlueprintPure, Category = "Weapon Holder")
	AWeaponBase* FindCarriedWeapon(TSubclassOf<AWeaponBase> WeaponClass) const;

	/** Spawns a weapon of this class with RoundsInMagazine loaded, adds it to the backpack,
	    and equips it if bAutoEquipOnPickup is on. Returns the new weapon. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Holder")
	AWeaponBase* GiveWeapon(TSubclassOf<AWeaponBase> WeaponClass, int32 RoundsInMagazine);

	/** Fires the equipped weapon. See EFireResult for why a shot may not have happened. */
	UFUNCTION(BlueprintCallable, Category = "WeaponHolder")
	EFireResult FireEquippedWeapon();

	/** Reloads the equipped weapon. Returns false if it couldn't start. */
	UFUNCTION(BlueprintCallable, Category = "WeaponHolder")
	bool ReloadEquippedWeapon();

	/** Rounds of Type in the shared reserve. Every carried weapon that takes Type reloads
	    from this one pool, so single and dual pistols share their rounds (Max Payne style). */
	UFUNCTION(BlueprintPure, Category = "Weapon Holder|Ammo")
	int32 GetReserveAmmo(EAmmoType Type) const;

	/** Adds up to Amount rounds of Type, capped at that type's maximum. Returns how many
	    were taken, so a pickup can keep the rest. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Holder|Ammo")
	int32 AddAmmo(EAmmoType Type, int32 Amount);

	/** Removes up to Wanted rounds of Type, for a reload. Returns how many it got. */
	int32 TakeAmmo(EAmmoType Type, int32 Wanted);

	/** Return the currently equipped weapon, if any. */
	AWeaponBase* GetEquippedWeapon() const { return EquippedWeapon;  }

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	/** Attaches the equipped weapon to the owner's hand socket and applies its grip offsets. */
	void AttachWeaponToHand();


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

	/** More weapons to start with, after StartingWeaponClass (which is the one equipped).
	    Weapons already carried — e.g. the single a dual implies — are skipped. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	TArray<TSubclassOf<AWeaponBase>> StartingLoadout;

	/** Fill every carried ammo type to its maximum at start. A testing convenience for now. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder|Ammo")
	bool bStartWithFullAmmo = false;

	/** Switch to a weapon as soon as it's picked up. A player option; on by default. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon Holder")
	bool bAutoEquipOnPickup = true;

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

	/** Most rounds carried per ammo type. Types with no entry use DefaultMaxAmmo. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder|Ammo")
	TMap<EAmmoType, int32> MaxAmmoByType;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder|Ammo", meta = (ClampMin = "0"))
	int32 DefaultMaxAmmo = 240;

	/** The shared reserve, per ammo type. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon Holder|Ammo")
	TMap<EAmmoType, int32> ReserveAmmo;

	int32 GetMaxAmmo(EAmmoType Type) const;

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

		
};
