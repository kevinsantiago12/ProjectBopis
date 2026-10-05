// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Camera/PlayerCameraManager.h"
#include "ProjectBopisCameraManager.generated.h"

/**
 *  Player camera manager.
 *  Limits min/max look pitch.
 */
UCLASS()
class AProjectBopisCameraManager : public APlayerCameraManager
{
	GENERATED_BODY()
	
public:

	/** Constructor */
	AProjectBopisCameraManager();
};
