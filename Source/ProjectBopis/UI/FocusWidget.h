// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/HUDBarWidget.h"
#include "FocusWidget.generated.h"

/** Focus meter: M_HUDBar on the "Bar" Image in WBP_Focus. */
UCLASS()
class PROJECTBOPIS_API UFocusWidget : public UHUDBarWidget
{
	GENERATED_BODY()

public:
	/** Meter fill, 0..1 (0 when there's no character). */
	UFUNCTION(BlueprintPure, Category = "Focus")
	float GetMeterFraction() const;

	UFUNCTION(BlueprintPure, Category = "Focus")
	bool IsFocusActive() const;

protected:
	virtual float GetBarFill() const override { return GetMeterFraction(); }
};
