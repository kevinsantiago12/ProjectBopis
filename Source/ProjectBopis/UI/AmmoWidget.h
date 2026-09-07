// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "AmmoWidget.generated.h"

/**
 * Ammunition readout for the equipped weapon.
 */
UCLASS()
class PROJECTBOPIS_API UAmmoWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	/** Rounds in the equipped weapon's magazine, or 0 when nothing is held. */
	UFUNCTION(BlueprintPure, Category = "Ammo")
	int32 GetAmmoInMagazine() const;

	/** Rounds in the equipped weapon's reserve, or 0 when nothing is held. */
	UFUNCTION(BlueprintPure, Category = "Ammo")
	int32 GetReserveAmmo() const;

	/** Whether the equipped weapon is mid-reload. */
	UFUNCTION(BlueprintPure, Category = "Ammo")
	bool IsReloading() const;
};
