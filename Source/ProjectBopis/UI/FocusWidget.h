// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "FocusWidget.generated.h"

/** Focus meter readout. */
UCLASS()
class PROJECTBOPIS_API UFocusWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	/** Meter fill, 0..1 (0 when there's no character). */
	UFUNCTION(BlueprintPure, Category = "Focus")
	float GetMeterFraction() const;

	UFUNCTION(BlueprintPure, Category = "Focus")
	bool IsFocusActive() const;
};
