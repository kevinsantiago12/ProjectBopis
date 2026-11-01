// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/HUDCountWidget.h"
#include "FirstAidWidget.generated.h"

/** First-aid kits carried. The layout lives in a Blueprint child (WBP_FirstAid). */
UCLASS()
class PROJECTBOPIS_API UFirstAidWidget : public UHUDCountWidget
{
	GENERATED_BODY()

public:
	/** Kits carried (the FirstAid pool), or 0 with no character. */
	UFUNCTION(BlueprintPure, Category = "First Aid")
	int32 GetFirstAidCount() const;

protected:
	virtual int32 GetCount() const override { return GetFirstAidCount(); }
};
