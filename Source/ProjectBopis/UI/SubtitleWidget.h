#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "SubtitleWidget.generated.h"

/**
 * The subtitle line (scripted events' dialogue). Bind a Text Block to GetSubtitleText and its
 * visibility to HasSubtitle.
 */
UCLASS()
class PROJECTBOPIS_API USubtitleWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	/** The line being shown, or empty. */
	UFUNCTION(BlueprintPure, Category = "Subtitle")
	FText GetSubtitleText() const;

	/** A line is up. */
	UFUNCTION(BlueprintPure, Category = "Subtitle")
	bool HasSubtitle() const;
};
