// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Camera/PlayerCameraManager.h"
#include "ProjectBopisCameraManager.generated.h"

/**
 *  Player camera manager.
 *  Limits min/max look pitch, and hands the view to the player's kill cam while it plays.
 */
UCLASS()
class AProjectBopisCameraManager : public APlayerCameraManager
{
	GENERATED_BODY()
	
public:

	/** Constructor */
	AProjectBopisCameraManager();

protected:

	/** The player's camera as usual, with the kill cam's view blended over it by its weight. */
	virtual void UpdateViewTarget(FTViewTarget& OutVT, float DeltaTime) override;
};
