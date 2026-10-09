// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/FocusWidget.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/FocusComponent.h"

float UFocusWidget::GetMeterFraction() const
{
	const AProjectBopisCharacter* Character = GetPlayerCharacter();
	const UFocusComponent* Focus = Character ? Character->GetFocus() : nullptr;
	return Focus ? Focus->GetMeterFraction() : 0.0f;
}

bool UFocusWidget::IsFocusActive() const
{
	const AProjectBopisCharacter* Character = GetPlayerCharacter();
	const UFocusComponent* Focus = Character ? Character->GetFocus() : nullptr;
	return Focus && Focus->IsFocusActive();
}
