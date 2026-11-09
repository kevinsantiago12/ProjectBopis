#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MenuWidget.generated.h"

class UWidgetSwitcher;

/** Base for every menu: the main menu (WBP_MainMenu) and, later, the pause menu. The Blueprint
    child holds the look and the buttons (WBP_MenuButton, each with its own Action); this holds
    the paging, focus and going back. An optional Widget Switcher named "Pages" holds the pages,
    its first child being the first page. Escape or gamepad B goes back a page. Focus goes to
    the first selectable item (UMenuItemWidget: a button or a setting) on the page showing, so
    a gamepad always has one. A page can be a widget of its own (WBP_OptionsPage, in both
    menus); its items count too. */
UCLASS(Abstract)
class PROJECTBOPIS_API UMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Shows the page of that name (a child of Pages), remembering the one it came from. */
	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowPageNamed(FName PageName);

	/** Back to the page before; from the first page, OnBackFromFirstPage. Returns whether it
	    did anything. */
	UFUNCTION(BlueprintCallable, Category = "Menu")
	bool GoBack();

	/** Hands input back to the game and opens Level, after a fade to black. No level reloads
	    the current one. */
	virtual void OpenGameLevel(const TSoftObjectPtr<UWorld>& Level);

	/** A gamepad is driving the menu: the selected button shows its selection frame. */
	bool IsControllerMode() const { return bControllerMode; }

protected:
	virtual void NativeOnInitialized() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnPreviewKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnAnalogValueChanged(const FGeometry& InGeometry, const FAnalogInputEvent& InAnalogEvent) override;
	virtual FReply NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	/** Seconds to fade in, each time the menu goes on screen. */
	UPROPERTY(EditAnywhere, Category = "Menu", meta = (ClampMin = "0.0"))
	float FadeInTime = 0.4f;

	/** Seconds of fade to black before an OpenLevel button's level loads. */
	UPROPERTY(EditAnywhere, Category = "Menu", meta = (ClampMin = "0.0"))
	float LevelFadeOutTime = 0.6f;

	/** Back from the first page. The main menu does nothing (false); the pause menu will
	    resume. */
	virtual bool OnBackFromFirstPage() { return false; }

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UWidgetSwitcher> Pages;

private:
	/** Focus goes to the first selectable item on the page showing (or anywhere, without
	    Pages): now, and whenever the menu gets focus back. */
	void FocusFirstItem();

	/** Pages left for another, oldest first, for GoBack. */
	UPROPERTY()
	TArray<TObjectPtr<UWidget>> PageHistory;

	float FadeInElapsed = 0.0f;

	/** Switches between controller and mouse; the buttons update their selection frame. */
	void SetControllerMode(bool bOn);

	/** A gamepad drives the menu (on at start with one attached; off on a real mouse move). */
	bool bControllerMode = false;
};
