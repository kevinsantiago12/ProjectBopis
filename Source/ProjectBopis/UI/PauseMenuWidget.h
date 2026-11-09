#pragma once

#include "CoreMinimal.h"
#include "UI/MenuWidget.h"
#include "PauseMenuWidget.generated.h"

class UInputAction;

/** The pause menu (WBP_PauseMenu): a menu that pauses the game while it's up. Going on screen
    pauses and takes the cursor and UI input; Back from its first page (Escape, B), or Start
    from any page, resumes. Its buttons are WBP_MenuButton copies like the main menu's: Resume
    is a Back button, Restart a RestartLevel one, Main Menu an OpenLevel one. */
UCLASS(Abstract)
class PROJECTBOPIS_API UPauseMenuWidget : public UMenuWidget
{
	GENERATED_BODY()

public:
	/** Closes the menu and unpauses, handing input back to the game. */
	UFUNCTION(BlueprintCallable, Category = "Menu")
	void Resume();

protected:
	virtual void NativeConstruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual bool OnBackFromFirstPage() override;

	/** The pause action (IA_Pause): every key mapped to it also closes the menu, so the key that
	    opens it closes it too. Without one, only gamepad Start does. */
	UPROPERTY(EditDefaultsOnly, Category = "Menu")
	TObjectPtr<UInputAction> ToggleAction;

private:
	/** True if Key is mapped to ToggleAction in the player's current input mappings. */
	bool IsToggleKey(const FKey& Key) const;
};
