#include "UI/MenuWidget.h"
#include "UI/MenuItemWidget.h"
#include "Components/PanelWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/WidgetSwitcher.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Gameplay/LevelTravelSubsystem.h"
#include "Framework/Application/SlateApplication.h"

namespace
{
	/** Visits Widget and everything under it, in order, until Visit returns false (then returns
	    false). Unlike the widget tree's own walk it steps into a page that is a widget of its
	    own (WBP_OptionsPage), but not into a menu item: an item's insides are its own. */
	bool ForEachMenuWidget(UWidget* Widget, TFunctionRef<bool(UWidget*)> Visit)
	{
		if (!Widget)
		{
			return true;
		}
		if (!Visit(Widget))
		{
			return false;
		}

		if (const UUserWidget* Page = Cast<UUserWidget>(Widget))
		{
			if (Widget->IsA<UMenuItemWidget>() || !Page->WidgetTree)
			{
				return true;
			}
			return ForEachMenuWidget(Page->WidgetTree->RootWidget, Visit);
		}
		if (const UPanelWidget* Panel = Cast<UPanelWidget>(Widget))
		{
			for (int32 Index = 0; Index < Panel->GetChildrenCount(); ++Index)
			{
				if (!ForEachMenuWidget(Panel->GetChildAt(Index), Visit))
				{
					return false;
				}
			}
		}
		return true;
	}
}

void UMenuWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// Focus given to the menu (the controller's UI input mode) goes on to a button.
	SetIsFocusable(true);
	if (Pages)
	{
		Pages->SetActiveWidgetIndex(0);
	}
	bControllerMode = FSlateApplication::IsInitialized() && FSlateApplication::Get().IsGamepadAttached();
	FocusFirstItem();
}

void UMenuWidget::ShowPageNamed(FName PageName)
{
	UWidget* Page = WidgetTree ? WidgetTree->FindWidget(PageName) : nullptr;
	if (!Pages || !Page || Page == Pages->GetActiveWidget())
	{
		return;
	}

	PageHistory.Add(Pages->GetActiveWidget());
	Pages->SetActiveWidget(Page);
	FocusFirstItem();
}

bool UMenuWidget::GoBack()
{
	if (Pages && PageHistory.Num() > 0)
	{
		Pages->SetActiveWidget(PageHistory.Pop());
		FocusFirstItem();
		return true;
	}
	return OnBackFromFirstPage();
}

void UMenuWidget::OpenGameLevel(const TSoftObjectPtr<UWorld>& Level)
{
	// The input mode outlives the map (the viewport holds it), and UI-only tells the viewport
	// to ignore game input. Hand it back before leaving: the game's controller doesn't set one.
	if (APlayerController* Player = GetOwningPlayer())
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->bShowMouseCursor = false;
	}

	// A fade to black first; the next level fades itself in.
	if (ULevelTravelSubsystem* Travel = GetGameInstance()->GetSubsystem<ULevelTravelSubsystem>())
	{
		Travel->FadeAndOpenLevel(Level, LevelFadeOutTime);
	}
}

void UMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// Fades in each time it goes on screen (the pause menu, each time it opens).
	FadeInElapsed = 0.0f;
	SetRenderOpacity(FadeInTime > 0.0f ? 0.0f : 1.0f);
}

void UMenuWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (FadeInElapsed < FadeInTime)
	{
		FadeInElapsed += InDeltaTime;
		SetRenderOpacity(FMath::Min(FadeInElapsed / FadeInTime, 1.0f));
	}
}

FReply UMenuWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	// Unhandled when there's nowhere to go back to, so Escape still stops PIE on the first page.
	const FKey Key = InKeyEvent.GetKey();
	if ((Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right) && GoBack())
	{
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UMenuWidget::FocusFirstItem()
{
	UMenuItemWidget* First = nullptr;
	ForEachMenuWidget(Pages ? Pages->GetActiveWidget() : GetRootWidget(), [&First](UWidget* Widget)
	{
		UMenuItemWidget* Item = Cast<UMenuItemWidget>(Widget);
		if (Item && Item->IsSelectable())
		{
			First = Item;
			return false;   // found: stop
		}
		return true;
	});
	if (!First)
	{
		return;
	}

	// Focus given to the menu goes on to the item. An item on a page of its own sits in that
	// page's tree, not the menu's, so the page forwards it the last step.
	UWidget* Next = First;
	for (UUserWidget* Holder = First->GetTypedOuter<UUserWidget>(); Holder; Holder = Holder->GetTypedOuter<UUserWidget>())
	{
		if (Holder != this)
		{
			Holder->SetIsFocusable(true);
		}
		Holder->SetDesiredFocusWidget(Next);
		if (Holder == this)
		{
			break;
		}
		Next = Holder;
	}
	First->SetFocus();   // does nothing until the menu is on screen; the desired focus covers that
}

FReply UMenuWidget::NativeOnPreviewKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	// Any gamepad button: the gamepad is driving again.
	if (InKeyEvent.GetKey().IsGamepadKey())
	{
		SetControllerMode(true);
	}
	return Super::NativeOnPreviewKeyDown(InGeometry, InKeyEvent);
}

FReply UMenuWidget::NativeOnAnalogValueChanged(const FGeometry& InGeometry, const FAnalogInputEvent& InAnalogEvent)
{
	// A stick pushed past half way: the gamepad is driving.
	if (FMath::Abs(InAnalogEvent.GetAnalogValue()) > 0.5f)
	{
		SetControllerMode(true);
	}
	return Super::NativeOnAnalogValueChanged(InGeometry, InAnalogEvent);
}

void UMenuWidget::SetControllerMode(bool bOn)
{
	if (bControllerMode == bOn)
	{
		return;
	}
	bControllerMode = bOn;

	// The selection frame shows only for a controller: every item updates its look.
	ForEachMenuWidget(GetRootWidget(), [](UWidget* Widget)
	{
		if (UMenuItemWidget* Item = Cast<UMenuItemWidget>(Widget))
		{
			Item->RefreshLook();
		}
		return true;
	});
}

FReply UMenuWidget::NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	// A real move (Slate's synthetic ones have no delta) hands the menu to the mouse: the button
	// under the cursor takes the focus, without the ring.
	const FVector2D Delta = InMouseEvent.GetCursorDelta();
	if (bControllerMode && !Delta.IsNearlyZero())
	{
		SetControllerMode(false);
		ForEachMenuWidget(Pages ? Pages->GetActiveWidget() : GetRootWidget(), [](UWidget* Widget)
		{
			UMenuItemWidget* Item = Cast<UMenuItemWidget>(Widget);
			if (Item && Item->IsHovered() && Item->IsSelectable())
			{
				Item->SetFocus();
				return false;
			}
			return true;
		});
	}
	return Super::NativeOnMouseMove(InGeometry, InMouseEvent);
}
