#include "UI/SettingSliderWidget.h"
#include "BopisGameUserSettings.h"
#include "Components/Slider.h"
#include "Components/Border.h"
#include "Components/TextBlock.h"

void USettingSliderWidget::NativePreConstruct()
{
	Super::NativePreConstruct();

	// Both sensitivities share one range and step. In the designer too, so it looks right there.
	const float Current = ReadSetting();
	if (Slider)
	{
		Slider->SetMinValue(UBopisGameUserSettings::MinSensitivity);
		Slider->SetMaxValue(UBopisGameUserSettings::MaxSensitivity);
		Slider->SetStepSize(UBopisGameUserSettings::SensitivityStep);
		Slider->SetValue(Current);
	}
	ShowValue(Current);
}

void USettingSliderWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	if (Slider)
	{
		// Left and right change it at once, with no press to grab it first, so up and down
		// still move on through the page. A drag snaps to the same steps.
		Slider->RequiresControllerLock = false;
		Slider->MouseUsesStep = true;

		Slider->OnValueChanged.AddDynamic(this, &USettingSliderWidget::HandleValueChanged);
		Slider->OnMouseCaptureBegin.AddDynamic(this, &USettingSliderWidget::HandleDragStarted);
		Slider->OnMouseCaptureEnd.AddDynamic(this, &USettingSliderWidget::HandleDragEnded);

		// Focus given to this widget goes on to its Slider.
		SetIsFocusable(true);
		SetDesiredFocusWidget(Slider);
	}
}

void USettingSliderWidget::HandleValueChanged(float Value)
{
	// On the slider's steps, so the number stays a round one.
	const float Stepped = FMath::GridSnap(Value, UBopisGameUserSettings::SensitivityStep);
	ShowValue(Stepped);

	// No change: the menu putting the stored value on the slider, or a step against an end.
	if (FMath::IsNearlyEqual(Stepped, ReadSetting()))
	{
		return;
	}
	WriteSetting(Stepped);

	// A key or pad step is a whole change; a drag saves once, when it ends.
	if (!bDragging)
	{
		SaveChange();
	}
}

void USettingSliderWidget::HandleDragStarted()
{
	bDragging = true;
}

void USettingSliderWidget::HandleDragEnded()
{
	bDragging = false;
	SaveChange();
}

float USettingSliderWidget::ReadSetting() const
{
	const UBopisGameUserSettings* Settings = UBopisGameUserSettings::Get();
	if (!Settings)
	{
		return 1.0f;
	}
	switch (Setting)
	{
	case EPlayerSetting::ControllerSensitivity:
		return Settings->GetControllerSensitivity();
	case EPlayerSetting::MouseSensitivity:
	default:
		return Settings->GetMouseSensitivity();
	}
}

void USettingSliderWidget::WriteSetting(float Value)
{
	UBopisGameUserSettings* Settings = UBopisGameUserSettings::Get();
	if (!Settings)
	{
		return;
	}
	switch (Setting)
	{
	case EPlayerSetting::MouseSensitivity:
		Settings->SetMouseSensitivity(Value);
		break;
	case EPlayerSetting::ControllerSensitivity:
		Settings->SetControllerSensitivity(Value);
		break;
	}
}

void USettingSliderWidget::SaveChange()
{
	if (UBopisGameUserSettings* Settings = UBopisGameUserSettings::Get())
	{
		Settings->SaveSettings();
	}
}

void USettingSliderWidget::ShowValue(float Value)
{
	if (ValueText)
	{
		FNumberFormattingOptions TwoPlaces;
		TwoPlaces.MinimumFractionalDigits = 2;
		TwoPlaces.MaximumFractionalDigits = 2;
		ValueText->SetText(FText::AsNumber(Value, &TwoPlaces));
	}
}

void USettingSliderWidget::ApplyLook()
{
	Super::ApplyLook();   // the label and the frame

	if (Background)
	{
		Background->SetBrushColor(IsHighlighted() ? HighlightColor : NormalColor);
	}
}
