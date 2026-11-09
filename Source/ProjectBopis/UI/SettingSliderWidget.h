#pragma once

#include "CoreMinimal.h"
#include "UI/MenuItemWidget.h"
#include "SettingSliderWidget.generated.h"

class USlider;
class UBorder;
class UTextBlock;

/** Which of the player's settings a slider changes. */
UENUM(BlueprintType)
enum class EPlayerSetting : uint8
{
	MouseSensitivity,
	ControllerSensitivity
};

/** A player setting on a slider, for the Options page. The Blueprint child (WBP_SettingSlider)
    holds the look: a Slider named "Slider", and optionally Text Blocks "Label" and "ValueText"
    and a Border "Background". Each copy sets its Text and Setting in the designer. A change
    takes effect and shows at once, and is saved when it's done. With a pad or the arrow keys,
    left and right change it and up and down move on. */
UCLASS(Abstract)
class PROJECTBOPIS_API USettingSliderWidget : public UMenuItemWidget
{
	GENERATED_BODY()

protected:
	virtual void NativePreConstruct() override;
	virtual void NativeOnInitialized() override;
	virtual void ApplyLook() override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Menu")
	EPlayerSetting Setting = EPlayerSetting::MouseSensitivity;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USlider> Slider;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> ValueText;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UBorder> Background;

private:
	UFUNCTION()
	void HandleValueChanged(float Value);

	UFUNCTION()
	void HandleDragStarted();

	UFUNCTION()
	void HandleDragEnded();

	/** The setting as it is now (1 without a settings object). */
	float ReadSetting() const;

	/** Stores a new value; the settings clamp it to their range. */
	void WriteSetting(float Value);

	/** Writes the player's settings to disk. */
	void SaveChange();

	/** The number beside the slider. */
	void ShowValue(float Value);

	/** A mouse drag is under way: its changes take effect at once, and save once, at the end. */
	bool bDragging = false;
};
