#include "BopisGameInstance.h"
#include "GameFramework/GameUserSettings.h"
#include "Engine/Engine.h"
#include "HAL/IConsoleManager.h"

void UBopisGameInstance::Init()
{
	Super::Init();
	ApplyFirstRunGraphics();
}

void UBopisGameInstance::OnStart()
{
	Super::OnStart();
	// Not from Init: there the engine isn't initialized yet, and ApplySettings silently skips
	// the quality levels (UGameUserSettings::ApplyNonResolutionSettings).
	ApplyDeckOverrides();
}

void UBopisGameInstance::ApplyFirstRunGraphics()
{
	// Never in the editor: play-in-editor shares the editor's own quality settings.
	UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	if (GIsEditor || !Settings || Settings->GetLastCPUBenchmarkResult() >= 0.0f)
	{
		return;
	}

	// The Deck's settings come from ApplyDeckOverrides on every start instead.
	Settings->RunHardwareBenchmark();
	Settings->ApplyHardwareBenchmarkResults();
	Settings->ApplySettings(false);
	Settings->SaveSettings();
}

void UBopisGameInstance::ApplyDeckOverrides()
{
	// Steam sets SteamDeck=1 on the Deck; -Deck on the command line forces it for testing.
	const bool bDeck = FPlatformMisc::GetEnvironmentVariable(TEXT("SteamDeck")) == TEXT("1")
		|| FParse::Param(FCommandLine::Get(), TEXT("Deck"));
	UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	if (GIsEditor || !bDeck || !Settings)
	{
		return;
	}

	// Every start, not just the first, so neither saved settings nor how the game was launched
	// can leave the Deck on another level: High, at DeckResolutionScale (a single overall level
	// would otherwise set High's own 87%), native 1280x800, fullscreen, locked to 60.
	Settings->SetOverallScalabilityLevel(2);
	Settings->SetResolutionScaleValueEx(DeckResolutionScale);
	Settings->SetScreenResolution(FIntPoint(1280, 800));
	Settings->SetFullscreenMode(EWindowMode::Fullscreen);
	Settings->SetFrameRateLimit(60.0f);
	Settings->SetVSyncEnabled(true);
	Settings->ApplySettings(false);
	Settings->SaveSettings();

	// Particles and other after-DOF translucency at half resolution (Deck trace 9: 1.75 -> 0.91 ms
	// in fights). Set by code, so it outranks the scalability tiers and survives a change of
	// quality level. 50 is the one value the default nearest-depth upsample supports.
	if (IConsoleVariable* HalfRes = IConsoleManager::Get().FindConsoleVariable(TEXT("r.SeparateTranslucencyScreenPercentage")))
	{
		HalfRes->Set(50.0f, ECVF_SetByCode);
	}

	// Enemies' animation at a lower rate when far or off screen: the Deck's fights are
	// game-thread-bound (trace 21). PCs keep full-rate animation.
	if (IConsoleVariable* AnimRate = IConsoleManager::Get().FindConsoleVariable(TEXT("bopis.EnemyAnimRateOptimization")))
	{
		AnimRate->Set(true, ECVF_SetByCode);
	}

#if !UE_BUILD_SHIPPING
	// Proof on the Deck that this ran, and what actually took: the values read back, not the ones asked for.
	IConsoleManager& Console = IConsoleManager::Get();
	const IConsoleVariable* Effects = Console.FindConsoleVariable(TEXT("sg.EffectsQuality"));
	const IConsoleVariable* Screen = Console.FindConsoleVariable(TEXT("r.ScreenPercentage"));
	const FString Applied = FString::Printf(TEXT("Deck settings applied: effects quality %d, screen %.0f%%"),
		Effects ? Effects->GetInt() : -1, Screen ? Screen->GetFloat() : -1.0f);
	UE_LOG(LogTemp, Display, TEXT("%s"), *Applied);
	GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Green, Applied);
#endif
}
