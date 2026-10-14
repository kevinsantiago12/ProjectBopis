// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "HealthWidget.generated.h"

/** Health readout. Placeholder look — the layout lives in WBP_Health. */
UCLASS()
class PROJECTBOPIS_API UHealthWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	/** Health left, 0..1 (0 when there's no character). */
	UFUNCTION(BlueprintPure, Category = "Health")
	float GetHealthFraction() const;
};
