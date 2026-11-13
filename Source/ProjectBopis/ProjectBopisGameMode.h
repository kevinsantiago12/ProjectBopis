// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "ProjectBopisGameMode.generated.h"

/**
 *  Simple GameMode for the game
 */
UCLASS(abstract)
class AProjectBopisGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AProjectBopisGameMode();

	/** Records a fresh corpse; past MaxCorpses, the oldest is removed. */
	void RegisterCorpse(AActor* Corpse);

	/** Console, while playing: "StartAt S3" reloads the level at the PlayerStart whose Player Start Tag is S3,
	    and keeps spawning there (later Plays too, until the editor closes). "StartAt off" goes back to the
	    level's own start. The same choice is the console variable Bopis.StartAt. */
	UFUNCTION(Exec)
	void StartAt(const FString& Tag);

protected:
	/** The level's own start (its untagged PlayerStart), or the test start Bopis.StartAt names. The
	    editor's "Play From Here" still comes first. */
	virtual AActor* ChoosePlayerStart_Implementation(AController* Player) override;

	/** Most bodies left lying around at once. Older ones are removed as new ones fall. */
	UPROPERTY(EditAnywhere, Category = "Corpses", meta = (ClampMin = "0"))
	int32 MaxCorpses = 5;

	/** While over MaxCorpses, how often (seconds) to look for an off-camera body to remove. */
	UPROPERTY(EditAnywhere, Category = "Corpses", meta = (ClampMin = "0.05"))
	float CorpseCheckInterval = 0.5f;

	/** Removes the oldest off-camera corpses until back within MaxCorpses. Bodies on screen
	    are never removed; if they're all in view, it tries again every CorpseCheckInterval. */
	void TrimCorpses();

private:
	/** Oldest first. Weak, so a corpse destroyed some other way simply drops out. */
	TArray<TWeakObjectPtr<AActor>> Corpses;

	FTimerHandle CorpseCheckTimer;
};



