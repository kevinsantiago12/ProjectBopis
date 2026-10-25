// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "Weapons/WeaponBase.h"
#include "ReticleWidget.generated.h"

/**
 * Crosshair: a static dot, drawn entirely by WBP_Reticle. The code only hides it while the
 * weapon wheel is up.
 */
UCLASS()
class PROJECTBOPIS_API UReticleWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
};
