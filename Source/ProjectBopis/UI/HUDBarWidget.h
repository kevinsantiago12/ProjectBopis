// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "HUDBarWidget.generated.h"

class UImage;
class UMaterialInstanceDynamic;

/**
 * A HUD bar drawn by M_HUDBar on an Image named "Bar". Each tick it pushes the
 * fill and the Image's laid-out size into the material, so the bar can be any
 * length in UMG and its texture tiles instead of stretching.
 */
UCLASS(Abstract)
class PROJECTBOPIS_API UHUDBarWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** How full the bar is, 0..1. */
	virtual float GetBarFill() const { return 0.0f; }

	/** The Image with an M_HUDBar instance as its brush. Optional: without it nothing is driven. */
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UImage> Bar;

private:
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> BarMaterial;
};
