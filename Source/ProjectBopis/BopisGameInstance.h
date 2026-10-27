#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "BopisGameInstance.generated.h"

/** Applies first-run graphics defaults: the hardware benchmark's pick on PCs, and on the
    Steam Deck (the performance baseline) High at its native 1280x800, locked to 60. */
UCLASS()
class PROJECTBOPIS_API UBopisGameInstance : public UGameInstance
{
	GENERATED_BODY()

public:
	virtual void Init() override;

private:
	/** First run only: once a benchmark has been recorded, the player's own settings stand. */
	void ApplyFirstRunGraphics();
};
