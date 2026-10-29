// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "GameMessageWidget.generated.h"

class UTextBlock;

/**
 *  The gameplay message feed (UGameMessageSubsystem). The designer's Text Blocks Message_0 ..
 *  Message_4, top to bottom, are the lines: oldest at the top, newest at the bottom. Unused
 *  lines collapse, so in a Vertical Box anchored at its bottom the feed grows upward.
 */
UCLASS()
class PROJECTBOPIS_API UGameMessageWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** A line fades out over its last this-many seconds. */
	UPROPERTY(EditAnywhere, Category = "Game Messages", meta = (ClampMin = "0.0"))
	float FadeOutTime = 0.5f;

private:
	UPROPERTY(Transient)
	TArray<TObjectPtr<UTextBlock>> Lines;
};
