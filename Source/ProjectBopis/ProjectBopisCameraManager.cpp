// Copyright Epic Games, Inc. All Rights Reserved.


#include "ProjectBopisCameraManager.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/KillCamComponent.h"

AProjectBopisCameraManager::AProjectBopisCameraManager()
{
	// set the min/max pitch
	ViewPitchMin = -70.0f;
	ViewPitchMax = 80.0f;
}

void AProjectBopisCameraManager::UpdateViewTarget(FTViewTarget& OutVT, float DeltaTime)
{
	Super::UpdateViewTarget(OutVT, DeltaTime);

	const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(OutVT.Target);
	if (const UKillCamComponent* KillCam = Player ? Player->GetKillCam() : nullptr)
	{
		KillCam->BlendView(OutVT.POV);
	}
}
