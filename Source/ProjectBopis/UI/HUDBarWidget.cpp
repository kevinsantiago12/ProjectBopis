// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/HUDBarWidget.h"
#include "Components/Image.h"
#include "Materials/MaterialInstanceDynamic.h"

void UHUDBarWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// The brush's material becomes this widget's own copy, so Fill can change every frame.
	if (Bar)
	{
		BarMaterial = Bar->GetDynamicMaterial();
	}
}

void UHUDBarWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (!BarMaterial)
	{
		return;
	}

	BarMaterial->SetScalarParameterValue(TEXT("Fill"), FMath::Clamp(GetBarFill(), 0.0f, 1.0f));

	// The shape and tiling are worked out in Slate units, so feed the Image's laid-out size.
	const FVector2f Size = Bar->GetCachedGeometry().GetLocalSize();
	if (Size.X > 0.0f && Size.Y > 0.0f)
	{
		BarMaterial->SetScalarParameterValue(TEXT("Length"), Size.X);
		BarMaterial->SetScalarParameterValue(TEXT("Height"), Size.Y);
	}
}
