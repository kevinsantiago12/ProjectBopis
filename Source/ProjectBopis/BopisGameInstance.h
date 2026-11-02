#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "BopisGameInstance.generated.h"

/** Graphics defaults: the hardware benchmark's pick on a PC's first run, and on the Steam Deck
    (the performance baseline) High at its native 1280x800, locked to 60, on every run. */
UCLASS()
class PROJECTBOPIS_API UBopisGameInstance : public UGameInstance
{
	GENERATED_BODY()

public:
	virtual void Init() override;

	/** After the engine is initialized: only then does ApplySettings apply quality levels. */
	virtual void OnStart() override;

private:
	/** First run only: once a benchmark has been recorded, the player's own settings stand. */
	void ApplyFirstRunGraphics();

	/** Every run on the Steam Deck: High at DeckResolutionScale, 1280x800 fullscreen at 60, and
	    the settings only the Deck gets, whatever was saved. */
	void ApplyDeckOverrides();

	/** The Deck's render resolution, in percent: native. 71% (the benchmark's pick) saved ≈1.7 ms
	    of GPU but no fps in fights, which are game-thread-bound (Deck trace 21, 2026-11-02). */
	static constexpr float DeckResolutionScale = 100.0f;
};
