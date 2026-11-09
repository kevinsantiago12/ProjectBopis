#include "UI/PauseMenuWidget.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "InputAction.h"

void UPauseMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// On screen: the game stops, and the menu takes the cursor and the input.
	UGameplayStatics::SetGamePaused(this, true);
	if (APlayerController* Player = GetOwningPlayer())
	{
		Player->bShowMouseCursor = true;
		FInputModeUIOnly Mode;
		Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		Mode.SetWidgetToFocus(GetCachedWidget());
		Player->SetInputMode(Mode);
	}
}

void UPauseMenuWidget::Resume()
{
	RemoveFromParent();
	UGameplayStatics::SetGamePaused(this, false);
	if (APlayerController* Player = GetOwningPlayer())
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->bShowMouseCursor = false;
	}
}

bool UPauseMenuWidget::OnBackFromFirstPage()
{
	Resume();
	return true;
}

FReply UPauseMenuWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	// The pause key closes it from any page, as it opened it (not on a held key's repeats).
	if (!InKeyEvent.IsRepeat() && IsToggleKey(InKeyEvent.GetKey()))
	{
		Resume();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

bool UPauseMenuWidget::IsToggleKey(const FKey& Key) const
{
	if (!ToggleAction)
	{
		return Key == EKeys::Gamepad_Special_Right;
	}

	const ULocalPlayer* LocalPlayer = GetOwningLocalPlayer();
	const UEnhancedInputLocalPlayerSubsystem* Input =
		LocalPlayer ? LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr;
	return Input && Input->QueryKeysMappedToAction(ToggleAction).Contains(Key);
}
