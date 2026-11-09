#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "BopisGameUserSettings.generated.h"

/** The player's settings, graphics and the rest, saved per machine in GameUserSettings.ini.
    The engine makes it (GameUserSettingsClassName in DefaultEngine.ini); Get() returns it. */
UCLASS()
class PROJECTBOPIS_API UBopisGameUserSettings : public UGameUserSettings
{
	GENERATED_BODY()

public:
	/** The game's one settings object, or null before the engine has made it. */
	static UBopisGameUserSettings* Get();

	virtual void LoadSettings(bool bForceReload = false) override;

	/** The range both sensitivities are kept in, and the step the menu's sliders move by. */
	static constexpr float MinSensitivity = 0.2f;
	static constexpr float MaxSensitivity = 3.0f;
	static constexpr float SensitivityStep = 0.05f;

	/** Multiplies the mouse's look; 1 is the game's own tuning. */
	float GetMouseSensitivity() const { return MouseSensitivity; }
	void SetMouseSensitivity(float Value);

	/** Multiplies the right stick's turn speeds; 1 is the game's own tuning. */
	float GetControllerSensitivity() const { return ControllerSensitivity; }
	void SetControllerSensitivity(float Value);

private:
	UPROPERTY(Config)
	float MouseSensitivity = 1.0f;

	UPROPERTY(Config)
	float ControllerSensitivity = 1.0f;
};
