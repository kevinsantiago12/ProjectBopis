// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Weapons/WeaponBase.h"
#include "ReticleWidget.generated.h"

/**
 * 
 */
UCLASS()
class PROJECTBOPIS_API UReticleWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "Reticle")
	float GetCurrentBloom() const;

	/** The equipped weapon's reticle settings, or sane defaults when nothing is held. */
	UFUNCTION(BlueprintPure, Category = "Reticle")
	FCrosshairSettings GetCrosshairSettings() const;
	
};
