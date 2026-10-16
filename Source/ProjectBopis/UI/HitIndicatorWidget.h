// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "HitIndicatorWidget.generated.h"

/**
 * Directional damage markers: arcs on a ring round the screen centre, toward where shots came
 * from — red for hits, grey for near misses — fading out. Drawn in code; place it full-screen.
 */
UCLASS()
class PROJECTBOPIS_API UHitIndicatorWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

protected:
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

	/** Distance from the screen centre to the arcs, in pixels. */
	UPROPERTY(EditAnywhere, Category = "Hit Indicator", meta = (ClampMin = "10.0"))
	float Radius = 160.0f;

	/** Width of each arc, in degrees round the ring. */
	UPROPERTY(EditAnywhere, Category = "Hit Indicator", meta = (ClampMin = "5.0", ClampMax = "120.0"))
	float ArcDegrees = 30.0f;

	UPROPERTY(EditAnywhere, Category = "Hit Indicator", meta = (ClampMin = "1.0"))
	float Thickness = 6.0f;

	UPROPERTY(EditAnywhere, Category = "Hit Indicator")
	FLinearColor HitColor = FLinearColor(0.85f, 0.05f, 0.05f, 0.9f);

	UPROPERTY(EditAnywhere, Category = "Hit Indicator")
	FLinearColor NearMissColor = FLinearColor(0.7f, 0.7f, 0.7f, 0.5f);
};
