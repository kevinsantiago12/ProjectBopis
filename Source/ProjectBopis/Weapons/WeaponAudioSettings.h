#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "WeaponAudioSettings.generated.h"

/** Project Settings > Game > Weapon Audio. Gunshot loudness for the player's guns and the
    enemies', on top of each fire sound's own volume. Saved to DefaultGame.ini. */
UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Weapon Audio"))
class PROJECTBOPIS_API UWeaponAudioSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	/** The player's gunshots: 2 = twice the volume (+6 dB), 0.5 = half (-6 dB). */
	UPROPERTY(Config, EditAnywhere, Category = "Gunshots", meta = (ClampMin = "0.0", UIMax = "4.0"))
	float PlayerShotVolume = 1.0f;

	/** Every enemy's gunshots, the same way. */
	UPROPERTY(Config, EditAnywhere, Category = "Gunshots", meta = (ClampMin = "0.0", UIMax = "4.0"))
	float EnemyShotVolume = 1.0f;
};
