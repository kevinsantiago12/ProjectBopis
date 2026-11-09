#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"
#include "MainMenuPlayerController.generated.h"

class UUserWidget;

/** The main menu's controller: black until the scene's camera is up, then a cut to it and a
    fade-in. Cursor on, UI-only input, and the menu widget on screen. */
UCLASS(abstract)
class PROJECTBOPIS_API AMainMenuPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	/** Cuts to the scene's camera and fades in. Called by the game mode once a scene shows. */
	void ViewSceneCamera(AActor* Camera);

protected:
	/** The menu itself (WBP_MainMenu). Optional for now: none = just the scene. */
	UPROPERTY(EditDefaultsOnly, Category = "Main Menu")
	TSubclassOf<UUserWidget> MenuWidgetClass;

	/** Seconds from black to the scene. */
	UPROPERTY(EditDefaultsOnly, Category = "Main Menu", meta = (ClampMin = "0.0"))
	float FadeInTime = 1.0f;

	virtual void BeginPlay() override;

private:
	UPROPERTY()
	TObjectPtr<UUserWidget> MenuWidget;

	/** Adds the menu, with the cursor and UI input. Once the scene has faded in. */
	void ShowMenu();

	FTimerHandle MenuTimer;
};
