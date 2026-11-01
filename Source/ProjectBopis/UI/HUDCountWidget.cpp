// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/HUDCountWidget.h"
#include "Components/TextBlock.h"

void UHUDCountWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (Count)
	{
		Count->SetText(FText::AsNumber(GetCount()));
	}
}
