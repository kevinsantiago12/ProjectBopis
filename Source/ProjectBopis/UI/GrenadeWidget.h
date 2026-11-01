// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/HUDCountWidget.h"
#include "GrenadeWidget.generated.h"

class UImage;
class UTexture2D;

/**
 * The G key's quick action, picked in the weapon wheel's quick-action segment: grenades (icon
 * and how many are carried) or melee (icon only). The layout lives in a Blueprint child
 * (WBP_Grenades): an Image "Icon" beside the "Count" Text Block.
 */
UCLASS()
class PROJECTBOPIS_API UGrenadeWidget : public UHUDCountWidget
{
	GENERATED_BODY()

public:
	/** Grenades carried (the Grenade pool), or 0 with no character. */
	UFUNCTION(BlueprintPure, Category = "Grenades")
	int32 GetGrenadeCount() const;

protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual int32 GetCount() const override { return GetGrenadeCount(); }

	/** Shows GrenadeIcon or MeleeIcon at its designed height. Optional: without it only the count changes. */
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UImage> Icon;

	UPROPERTY(EditAnywhere, Category = "Quick Action")
	TObjectPtr<UTexture2D> GrenadeIcon;

	UPROPERTY(EditAnywhere, Category = "Quick Action")
	TObjectPtr<UTexture2D> MeleeIcon;
};
