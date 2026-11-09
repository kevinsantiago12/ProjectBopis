#include "UI/MenuItemWidget.h"
#include "UI/MenuWidget.h"
#include "Components/TextBlock.h"

void UMenuItemWidget::NativePreConstruct()
{
	Super::NativePreConstruct();

	// Runs in the designer too, so the label shows while editing.
	if (Label)
	{
		Label->SetText(Text);
	}
	ApplyLook();   // the resting look, in the designer too
}

void UMenuItemWidget::NativeOnAddedToFocusPath(const FFocusEvent& InFocusEvent)
{
	Super::NativeOnAddedToFocusPath(InFocusEvent);
	SetHighlighted(true);
}

void UMenuItemWidget::NativeOnRemovedFromFocusPath(const FFocusEvent& InFocusEvent)
{
	Super::NativeOnRemovedFromFocusPath(InFocusEvent);
	SetHighlighted(false);
}

void UMenuItemWidget::NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	Super::NativeOnMouseEnter(InGeometry, InMouseEvent);

	// The mouse moves the focus only when it's driving: with a gamepad, a parked cursor that an
	// item slides under mustn't steal the selection.
	const UMenuWidget* Menu = GetTypedOuter<UMenuWidget>();
	if (IsSelectable() && !(Menu && Menu->IsControllerMode()))
	{
		SetFocus();
	}
}

void UMenuItemWidget::SetHighlighted(bool bInHighlighted)
{
	if (bHighlighted == bInHighlighted)
	{
		return;
	}
	bHighlighted = bInHighlighted;
	ApplyLook();
	OnHighlightChanged(bHighlighted);
}

void UMenuItemWidget::ApplyLook()
{
	if (Label)
	{
		Label->SetColorAndOpacity(FSlateColor(bHighlighted ? HighlightTextColor : NormalTextColor));
	}

	// At design time it stays as set in the designer, so it can be styled there.
	if (FocusFrame && !IsDesignTime())
	{
		const UMenuWidget* Menu = GetTypedOuter<UMenuWidget>();
		const bool bShowFrame = bHighlighted && Menu && Menu->IsControllerMode();
		FocusFrame->SetVisibility(bShowFrame ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
	}
}
