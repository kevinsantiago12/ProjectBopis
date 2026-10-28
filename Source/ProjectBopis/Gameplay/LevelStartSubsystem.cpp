// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/LevelStartSubsystem.h"

void ULevelStartSubsystem::SetHolding(bool bInHolding)
{
	const bool bReleasing = bHolding && !bInHolding;
	bHolding = bInHolding;
	if (bReleasing)
	{
		OnReleased.Broadcast();
		OnReleased.Clear();
	}
}
