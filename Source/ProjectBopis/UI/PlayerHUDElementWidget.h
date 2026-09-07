// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "PlayerHUDElementWidget.generated.h"

class AProjectBopisCharacter;
class AWeaponBase;

/**
 * Base for individual HUD elements — reticle, ammo, health, radar.
 *
 * Each element sources its own state rather than being fed by the HUD
 * container, so adding one to a layout is pure composition: drop it in and it
 * works. The Character → WeaponHolder → Weapon walk every element needs lives
 * here once instead of in each subclass.
 */
UCLASS(Abstract)
class PROJECTBOPIS_API UPlayerHUDElementWidget : public UUserWidget
{
	GENERATED_BODY()

protected:
	/** The owning player's character, or null. */
	AProjectBopisCharacter* GetPlayerCharacter() const;

	/** The owning player's equipped weapon, or null. */
	AWeaponBase* GetEquippedWeapon() const;
};
