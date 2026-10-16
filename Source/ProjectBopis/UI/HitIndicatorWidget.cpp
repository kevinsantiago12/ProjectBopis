// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/HitIndicatorWidget.h"
#include "ProjectBopisCharacter.h"
#include "Rendering/DrawElements.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"

int32 UHitIndicatorWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);

	const AProjectBopisCharacter* Character = GetPlayerCharacter();
	const APlayerController* PlayerController = GetOwningPlayer();
	if (!Character || !PlayerController || !PlayerController->PlayerCameraManager)
	{
		return LayerId;
	}

	const FVector2D Centre = AllottedGeometry.GetLocalSize() * 0.5;
	const float ViewYaw = PlayerController->PlayerCameraManager->GetCameraRotation().Yaw;
	const float Now = Character->GetWorld()->GetRealTimeSeconds();
	const float HalfArc = FMath::DegreesToRadians(ArcDegrees * 0.5f);
	constexpr int32 Steps = 8;

	for (const FHitIndicator& Marker : Character->GetHitIndicators())
	{
		// Up the screen is the way the camera looks; clockwise is to its right. Measured each
		// frame, so a marker swings round as the player turns.
		const FVector ToSource = Marker.Source - Character->GetActorLocation();
		const float Angle = FMath::DegreesToRadians(FRotator::NormalizeAxis(ToSource.Rotation().Yaw - ViewYaw));
		const float Fade = 1.0f - FMath::Clamp((Now - Marker.StartTime) / Marker.Duration, 0.0f, 1.0f);
		FLinearColor Colour = Marker.bHit ? HitColor : NearMissColor;
		Colour.A *= Fade;

		TArray<FVector2D> Points;
		for (int32 Step = 0; Step <= Steps; ++Step)
		{
			const float A = Angle - HalfArc + 2.0f * HalfArc * Step / Steps;
			Points.Add(Centre + FVector2D(FMath::Sin(A), -FMath::Cos(A)) * Radius);
		}
		FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 1, AllottedGeometry.ToPaintGeometry(), Points,
			ESlateDrawEffect::None, Colour, true, Thickness);
	}
	return LayerId + 1;
}
