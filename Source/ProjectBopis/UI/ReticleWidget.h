// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "Weapons/WeaponBase.h"
#include "ReticleWidget.generated.h"

/**
 * Crosshair: a static dot, drawn entirely by WBP_Reticle. Kept as the widget's parent
 * class so reticle behaviour has a home if it ever needs code again.
 */
UCLASS()
class PROJECTBOPIS_API UReticleWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()
};
