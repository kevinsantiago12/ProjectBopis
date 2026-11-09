#include "BopisGameUserSettings.h"
#include "Engine/Engine.h"

UBopisGameUserSettings* UBopisGameUserSettings::Get()
{
	return GEngine ? Cast<UBopisGameUserSettings>(GEngine->GetGameUserSettings()) : nullptr;
}

void UBopisGameUserSettings::LoadSettings(bool bForceReload)
{
	Super::LoadSettings(bForceReload);

	// A hand-edited file can't leave the view frozen or spinning.
	SetMouseSensitivity(MouseSensitivity);
	SetControllerSensitivity(ControllerSensitivity);
}

void UBopisGameUserSettings::SetMouseSensitivity(float Value)
{
	MouseSensitivity = FMath::Clamp(Value, MinSensitivity, MaxSensitivity);
}

void UBopisGameUserSettings::SetControllerSensitivity(float Value)
{
	ControllerSensitivity = FMath::Clamp(Value, MinSensitivity, MaxSensitivity);
}
