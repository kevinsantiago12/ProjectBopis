#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MenuItemWidget.generated.h"

class UTextBlock;

/** One thing on a menu page the player can select: a button (UMenuButtonWidget) or a setting
    (USettingSliderWidget). It holds what they share: the label, the highlight while focused,
    the controller's selection frame, and the mouse taking the focus. UMenuWidget finds the
    items on a page by this class. */
UCLASS(Abstract)
class PROJECTBOPIS_API UMenuItemWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Can take the focus. A child can narrow it: a button with nothing behind it can't. */
	virtual bool IsSelectable() const { return GetIsEnabled(); }

	/** Focused (gamepad, keyboard, or the mouse over it, which moves the focus here). */
	UFUNCTION(BlueprintPure, Category = "Menu")
	bool IsHighlighted() const { return bHighlighted; }

	/** Re-applies the look (colours, selection frame), e.g. when the menu switches between
	    controller and mouse. */
	void RefreshLook() { ApplyLook(); }

protected:
	virtual void NativePreConstruct() override;
	virtual void NativeOnAddedToFocusPath(const FFocusEvent& InFocusEvent) override;
	virtual void NativeOnRemovedFromFocusPath(const FFocusEvent& InFocusEvent) override;
	virtual void NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	/** Puts the look for the current state on the item: the Label's colour and the frame here,
	    the background in each child (a Button's, a Border's). */
	virtual void ApplyLook();

	/** For more than the colours (a slide, a sound): the highlight came or went. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Menu")
	void OnHighlightChanged(bool bIsHighlighted);

	/** What the item says. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu")
	FText Text;

	/** The look at rest and highlighted: the background and the Label's colour. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu|Look")
	FLinearColor NormalColor = FLinearColor(0.02f, 0.02f, 0.02f, 0.65f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu|Look")
	FLinearColor HighlightColor = FLinearColor(0.85f, 0.82f, 0.74f, 0.95f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu|Look")
	FLinearColor NormalTextColor = FLinearColor::White;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu|Look")
	FLinearColor HighlightTextColor = FLinearColor(0.02f, 0.02f, 0.02f, 1.0f);

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> Label;

	/** The selection frame (an outline Image over the item, say): shown while this item is
	    selected and a controller drives the menu. Optional; designed in the item's WBP. */
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UWidget> FocusFrame;

private:
	void SetHighlighted(bool bInHighlighted);

	bool bHighlighted = false;
};
