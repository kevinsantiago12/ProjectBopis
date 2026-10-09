// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

/** Main log category used across the project */
DECLARE_LOG_CATEGORY_EXTERN(LogProjectBopis, Log, All);

/** The "Projectile" object channel from DefaultEngine.ini — bullets in flight. */
#define ECC_Projectile ECC_GameTraceChannel1
