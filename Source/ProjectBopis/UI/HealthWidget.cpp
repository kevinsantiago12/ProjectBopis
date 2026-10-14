// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/HealthWidget.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/HealthComponent.h"

float UHealthWidget::GetHealthFraction() const
{
	const AProjectBopisCharacter* Character = GetPlayerCharacter();
	const UHealthComponent* Health = Character ? Character->GetHealthComponent() : nullptr;
	return (Health && Health->GetMaxHealth() > 0.0f) ? Health->GetHealth() / Health->GetMaxHealth() : 0.0f;
}
