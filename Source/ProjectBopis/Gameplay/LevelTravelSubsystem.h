#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Containers/Ticker.h"
#include "LevelTravelSubsystem.generated.h"

class SImage;

/** Every level change goes through here: the screen fades to black (over the HUD and menus too)
    with the sound, then the level opens. The black stays up until the next level is loaded,
    where its own black start takes over (the level-start curtain, or the main menu's camera
    fade). Real seconds on the core ticker, so a paused game or slow motion can't stall it. */
UCLASS()
class PROJECTBOPIS_API ULevelTravelSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Fades to black over FadeTime, then opens Level; none reloads the current level.
	    Ignored while already on the way out. */
	UFUNCTION(BlueprintCallable, Category = "Level Travel")
	void FadeAndOpenLevel(const TSoftObjectPtr<UWorld>& Level, float FadeTime = 0.6f);

	UFUNCTION(BlueprintPure, Category = "Level Travel")
	bool IsTravelling() const { return TickerHandle.IsValid(); }

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	bool TickFade(float DeltaTime);

	/** The next level is in: its own black has taken over, so the cover goes. */
	void OnPostLoadMap(UWorld* LoadedWorld);

	void RemoveCover();

	/** Black over everything (Z-order 1000, as the level-start curtain): the HUD and menus are
	    widgets, which the camera's own fade doesn't cover. */
	TSharedPtr<SImage> Cover;

	FTSTicker::FDelegateHandle TickerHandle;
	FDelegateHandle PostLoadMapHandle;
	FName PendingLevel;
	float FadeDuration = 0.0f;
	float FadeElapsed = 0.0f;
};
