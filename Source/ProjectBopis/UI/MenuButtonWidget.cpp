#include "UI/MenuButtonWidget.h"
#include "UI/MenuWidget.h"
#include "Components/Button.h"
#include "Kismet/KismetSystemLibrary.h"

bool UMenuButtonWidget::IsUsable() const
{
	switch (Action)
	{
	case EMenuButtonAction::None:
		return false;
	case EMenuButtonAction::OpenLevel:
		return !Level.IsNull();
	default:
		return true;
	}
}

void UMenuButtonWidget::NativePreConstruct()
{
	Super::NativePreConstruct();   // the label and the resting look

	// Runs in the designer too, so the greyed-out state shows while editing.
	SetIsEnabled(IsUsable());
}

void UMenuButtonWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	if (Button)
	{
		Button->OnClicked.AddDynamic(this, &UMenuButtonWidget::HandleClicked);

		// Focus given to this widget goes on to its Button.
		SetIsFocusable(true);
		SetDesiredFocusWidget(Button);
	}
}

void UMenuButtonWidget::HandleClicked()
{
	UMenuWidget* Menu = GetTypedOuter<UMenuWidget>();

	switch (Action)
	{
	case EMenuButtonAction::OpenPage:
		if (Menu)
		{
			Menu->ShowPageNamed(Page);
		}
		break;
	case EMenuButtonAction::Back:
		if (Menu)
		{
			Menu->GoBack();
		}
		break;
	case EMenuButtonAction::OpenLevel:
		if (Menu)
		{
			Menu->OpenGameLevel(Level);
		}
		break;
	case EMenuButtonAction::RestartLevel:
		if (Menu)
		{
			Menu->OpenGameLevel(TSoftObjectPtr<UWorld>());
		}
		break;
	case EMenuButtonAction::QuitGame:
		UKismetSystemLibrary::QuitGame(this, GetOwningPlayer(), EQuitPreference::Quit, false);
		break;
	default:
		break;
	}

	OnClicked.Broadcast();
}

void UMenuButtonWidget::ApplyLook()
{
	Super::ApplyLook();   // the label and the frame

	if (Button)
	{
		Button->SetBackgroundColor(IsHighlighted() ? HighlightColor : NormalColor);
	}
}
