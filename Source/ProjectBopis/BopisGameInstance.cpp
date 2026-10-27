#include "BopisGameInstance.h"
#include "GameFramework/GameUserSettings.h"
#include "Engine/Engine.h"

void UBopisGameInstance::Init()
{
	Super::Init();
	ApplyFirstRunGraphics();
}

void UBopisGameInstance::ApplyFirstRunGraphics()
{
	// Never in the editor: play-in-editor shares the editor's own quality settings.
	UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	if (GIsEditor || !Settings || Settings->GetLastCPUBenchmarkResult() >= 0.0f)
	{
		return;
	}

	Settings->RunHardwareBenchmark();
	Settings->ApplyHardwareBenchmarkResults();

	// Steam sets SteamDeck=1 on the Deck, and Proton passes it through to the game.
	if (FPlatformMisc::GetEnvironmentVariable(TEXT("SteamDeck")) == TEXT("1"))
	{
		Settings->SetOverallScalabilityLevel(2);
		Settings->SetScreenResolution(FIntPoint(1280, 800));
		Settings->SetFullscreenMode(EWindowMode::Fullscreen);
		Settings->SetFrameRateLimit(60.0f);
		Settings->SetVSyncEnabled(true);
	}

	Settings->ApplySettings(false);
	Settings->SaveSettings();
}
