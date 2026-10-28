// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LevelStartSubsystem.generated.h"

/**
 *  Holds the enemies at a level's start while the black screen is up (the player controller's
 *  curtain): no behaviour, no moving or shooting, until it has fully faded in.
 */
UCLASS()
class PROJECTBOPIS_API ULevelStartSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** Enemies wait while this is on. */
	bool IsHolding() const { return bHolding; }

	/** On before anything begins play; off once the fade's done, which sets everyone going. */
	void SetHolding(bool bInHolding);

	/** The hold's lifted: what was waiting on it starts now. */
	FSimpleMulticastDelegate OnReleased;

private:
	bool bHolding = false;
};
