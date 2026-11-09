#include "MainMenu/MainMenuPlayerController.h"
#include "Blueprint/UserWidget.h"
#include "Camera/PlayerCameraManager.h"

void AMainMenuPlayerController::BeginPlay()
{
	Super::BeginPlay();

	// Black until the scene's camera is up: the hub has nothing to look at. The menu comes
	// once the scene has faded in (ShowMenu).
	if (IsLocalPlayerController() && PlayerCameraManager)
	{
		PlayerCameraManager->SetManualCameraFade(1.0f, FLinearColor::Black, false);
	}
}

void AMainMenuPlayerController::ViewSceneCamera(AActor* Camera)
{
	// A cut, not a blend: there's nothing behind the black to blend from.
	SetViewTarget(Camera);

	if (PlayerCameraManager)
	{
		PlayerCameraManager->StartCameraFade(1.0f, 0.0f, FadeInTime, FLinearColor::Black);
	}

	// The menu once the scene is in view; it fades itself in.
	if (FadeInTime > 0.0f)
	{
		GetWorldTimerManager().SetTimer(MenuTimer, this, &AMainMenuPlayerController::ShowMenu, FadeInTime, false);
	}
	else
	{
		ShowMenu();
	}
}

void AMainMenuPlayerController::ShowMenu()
{
	if (MenuWidget || !MenuWidgetClass || !IsLocalPlayerController())
	{
		return;
	}

	MenuWidget = CreateWidget<UUserWidget>(this, MenuWidgetClass);
	MenuWidget->AddToViewport();

	bShowMouseCursor = true;
	FInputModeUIOnly Mode;
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	Mode.SetWidgetToFocus(MenuWidget->TakeWidget());
	SetInputMode(Mode);
}
