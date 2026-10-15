// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "Weapons/WeaponBase.h"
#include "ReticleWidget.generated.h"

/**
 * Crosshair. Takes its appearance from the equipped weapon's crosshair settings.
 */
UCLASS()
class PROJECTBOPIS_API UReticleWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	/** The equipped weapon's reticle settings, or sane defaults when nothing is held. */
	UFUNCTION(BlueprintPure, Category = "Reticle")
	FCrosshairSettings GetCrosshairSettings() const;
};
