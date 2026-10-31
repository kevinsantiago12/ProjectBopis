// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/HUDBarWidget.h"
#include "HealthWidget.generated.h"

/** Health bar: M_HUDBar on the "Bar" Image in WBP_Health. */
UCLASS()
class PROJECTBOPIS_API UHealthWidget : public UHUDBarWidget
{
	GENERATED_BODY()

public:
	/** Health left, 0..1 (0 when there's no character). */
	UFUNCTION(BlueprintPure, Category = "Health")
	float GetHealthFraction() const;

protected:
	virtual float GetBarFill() const override { return GetHealthFraction(); }
};
