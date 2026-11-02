// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/HUDCountWidget.h"
#include "Components/TextBlock.h"

void UHUDCountWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// Only on a change: a new FText every frame makes Slate lay the text out again every frame.
	const int32 Value = GetCount();
	if (Count && Value != ShownCount)
	{
		Count->SetText(FText::AsNumber(Value));
		ShownCount = Value;
	}
}
