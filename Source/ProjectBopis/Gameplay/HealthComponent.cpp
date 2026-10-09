// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/HealthComponent.h"

UHealthComponent::UHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UHealthComponent::BeginPlay()
{
	Super::BeginPlay();

	// Here, not the constructor — MaxHealth is a per-Blueprint default.
	Health = MaxHealth;
}

bool UHealthComponent::ApplyDamage(float Amount)
{
	if (Amount <= 0.0f || IsDepleted())
	{
		return false;
	}

	Health = FMath::Max(0.0f, Health - Amount);
	return IsDepleted();
}
