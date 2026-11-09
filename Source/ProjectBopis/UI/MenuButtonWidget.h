#pragma once

#include "CoreMinimal.h"
#include "UI/MenuItemWidget.h"
#include "MenuButtonWidget.generated.h"

class UButton;

/** What a menu button does when pressed. */
UENUM(BlueprintType)
enum class EMenuButtonAction : uint8
{
	/** Nothing behind it yet: greyed out. */
	None,
	/** Shows the page named in Page. */
	OpenPage,
	/** Back to the menu's previous page. */
	Back,
	/** Opens Level (greyed out while none is set). */
	OpenLevel,
	/** Reloads the level being played (the pause menu's Restart). */
	RestartLevel,
	/** Quits the game. */
	QuitGame,
	/** Only fires OnClicked, for the menu's own code (a pause menu's Restart, say). */
	Custom
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FMenuButtonClicked);

/** One menu button, shared by every menu (main menu, pause menu). The Blueprint child
    (WBP_MenuButton) holds the look: a Button named "Button" and an optional Text Block named
    "Label". Each copy placed in a menu sets its Text and Action in the designer. Focus given to
    it goes on to its Button, so gamepad navigation lands on buttons. The label, highlight and
    frame come from UMenuItemWidget. */
UCLASS(Abstract)
class PROJECTBOPIS_API UMenuButtonWidget : public UMenuItemWidget
{
	GENERATED_BODY()

public:
	/** Fires on every press (mouse, Enter, gamepad A), after the Action. */
	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FMenuButtonClicked OnClicked;

	/** False for None, and for OpenLevel with no level: such a button is greyed out. */
	UFUNCTION(BlueprintPure, Category = "Menu")
	bool IsUsable() const;

	virtual bool IsSelectable() const override { return IsUsable() && GetIsEnabled(); }

protected:
	virtual void NativePreConstruct() override;
	virtual void NativeOnInitialized() override;
	virtual void ApplyLook() override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu")
	EMenuButtonAction Action = EMenuButtonAction::None;

	/** OpenPage: the name of the page (a child of the menu's Pages switcher). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu",
		meta = (EditCondition = "Action == EMenuButtonAction::OpenPage", EditConditionHides))
	FName Page;

	/** OpenLevel: the level it opens. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu",
		meta = (EditCondition = "Action == EMenuButtonAction::OpenLevel", EditConditionHides))
	TSoftObjectPtr<UWorld> Level;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UButton> Button;

private:
	UFUNCTION()
	void HandleClicked();
};
