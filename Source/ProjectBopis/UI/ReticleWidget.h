// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "Weapons/WeaponBase.h"
#include "ReticleWidget.generated.h"

/**
 * Crosshair. Expands with the equipped weapon's bloom and takes its
 * appearance from that weapon's crosshair settings.
 */
UCLASS()
class PROJECTBOPIS_API UReticleWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "Reticle")
	float GetCurrentBloom() const;

	/** The equipped weapon's reticle settings, or sane defaults when nothing is held. */
	UFUNCTION(BlueprintPure, Category = "Reticle")
	FCrosshairSettings GetCrosshairSettings() const;
};
