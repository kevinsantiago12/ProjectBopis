#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "InteractPromptWidget.generated.h"

/** The Interact prompt ("Inspect"). Bind a Text Block to GetPromptText and the prompt's
    Visibility to GetPromptVisibility. */
UCLASS()
class PROJECTBOPIS_API UInteractPromptWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	/** The word for what's in front of the player, or empty. */
	UFUNCTION(BlueprintPure, Category = "Interact")
	FText GetPromptText() const;

	UFUNCTION(BlueprintPure, Category = "Interact")
	bool HasPrompt() const;

	/** For the Visibility binding: shown (and ignored by the mouse) while there's a prompt,
	    collapsed otherwise. */
	UFUNCTION(BlueprintPure, Category = "Interact")
	ESlateVisibility GetPromptVisibility() const;
};
