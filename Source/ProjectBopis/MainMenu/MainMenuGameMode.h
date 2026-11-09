#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "TimerManager.h"
#include "MainMenuGameMode.generated.h"

class ULevelStreamingDynamic;
class ACameraActor;

/** The main menu's game mode, on the hub (Lvl_MainMenu). No pawn: it loads one of the menu's
    scenes as a level instance, then has the menu controller look through that scene's camera. */
UCLASS(abstract)
class PROJECTBOPIS_API AMainMenuGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AMainMenuGameMode();

	/** Unloads the scene on show, if any, and loads Scenes[Index]. */
	UFUNCTION(BlueprintCallable, Category = "Main Menu")
	void ShowScene(int32 Index);

protected:
	/** The menu's scenes (Lvl_MenuScene_*), each with its own menu camera placed in it. */
	UPROPERTY(EditDefaultsOnly, Category = "Main Menu")
	TArray<TSoftObjectPtr<UWorld>> Scenes;

	/** True: a random scene each time the menu opens. False: always the first. */
	UPROPERTY(EditDefaultsOnly, Category = "Main Menu")
	bool bRandomScene = true;

	/** How long (seconds) to keep looking for the scene's camera once it shows. World Partition
	    scenes bring their actors in a moment after the scene itself. */
	UPROPERTY(EditDefaultsOnly, Category = "Main Menu", meta = (ClampMin = "0.1"))
	float CameraSearchTimeout = 5.0f;

	virtual void BeginPlay() override;

	/** The menu has no pawn: never spawn one. */
	virtual bool PlayerCanRestart_Implementation(APlayerController* Player) override;

private:
	/** Bound to the scene's OnLevelShown: finds its camera and hands it to the controller. */
	UFUNCTION()
	void OnSceneShown();

	UPROPERTY()
	TObjectPtr<ULevelStreamingDynamic> CurrentScene;

	/** Looks for a camera in a loaded scene (not the hub, not the last scene's) and hands it to the
	    controller; if there's none yet, tries again shortly, until CameraSearchTimeout runs out. */
	void FindSceneCamera();

	TWeakObjectPtr<ACameraActor> SceneCamera;
	FTimerHandle CameraSearchTimer;
	float CameraSearchTimeLeft = 0.0f;
};
