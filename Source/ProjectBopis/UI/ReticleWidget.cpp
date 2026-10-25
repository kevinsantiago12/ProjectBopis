// Fill out your copyright notice in the Description page of Project Settings.


#include "UI/ReticleWidget.h"
#include "ProjectBopisCharacter.h"

void UReticleWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// No crosshair while the weapon wheel is up: its slow motion isn't for lining up shots.
	const AProjectBopisCharacter* Player = GetPlayerCharacter();
	const float Opacity = Player && Player->IsWeaponWheelOpen() ? 0.0f : 1.0f;
	if (GetRenderOpacity() != Opacity)
	{
		SetRenderOpacity(Opacity);
	}
}
