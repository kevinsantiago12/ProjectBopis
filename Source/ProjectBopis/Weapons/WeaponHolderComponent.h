// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
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

	UFUNCTION(BlueprintCallable, Category = "WeaponHolder")
	void FireEquippedWeapon();

	/** Return the currently equipped weapon, if any. */
	AWeaponBase* GetEquippedWeapon() const { return EquippedWeapon;  }

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	int32 MaxCarriedWeapons = 2;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon Holder")
	TArray<TObjectPtr<AWeaponBase>> CarriedWeapons;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon Holder")
	TObjectPtr<AWeaponBase> EquippedWeapon;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Holder")
	FName WeaponAttachSocketName = TEXT("hand_r");

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

		
};
