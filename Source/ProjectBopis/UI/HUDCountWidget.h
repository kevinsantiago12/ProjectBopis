// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "HUDCountWidget.generated.h"

class UTextBlock;

/**
 * A HUD count (first-aid kits, grenades): each tick it writes GetCount() into an
 * optional Text Block named "Count". The icon beside it is a plain Image in the
 * Blueprint child.
 */
UCLASS(Abstract)
class PROJECTBOPIS_API UHUDCountWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** The number shown. */
	virtual int32 GetCount() const { return 0; }

	/** The number's Text Block. Optional: without it nothing is driven. */
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> Count;

private:
	/** The number on screen, so the text is only re-laid-out when it changes. */
	int32 ShownCount = -1;
};
