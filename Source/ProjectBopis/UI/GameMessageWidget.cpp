// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/GameMessageWidget.h"
#include "UI/GameMessageSubsystem.h"
#include "Components/TextBlock.h"
#include "Engine/LocalPlayer.h"
#include "HAL/PlatformTime.h"

void UGameMessageWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// The designer's lines, by name; a missing one just isn't used.
	for (int32 Index = 0; Index < UGameMessageSubsystem::MaxMessages; ++Index)
	{
		if (UTextBlock* Line = Cast<UTextBlock>(GetWidgetFromName(*FString::Printf(TEXT("Message_%d"), Index))))
		{
			Lines.Add(Line);
		}
	}
}

void UGameMessageWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	const ULocalPlayer* Player = GetOwningLocalPlayer();
	const UGameMessageSubsystem* Feed = Player ? Player->GetSubsystem<UGameMessageSubsystem>() : nullptr;
	const double Now = FPlatformTime::Seconds();

	// The lines still up, oldest first. More of them than designer lines: the newest win.
	TArray<const FGameMessage*, TInlineAllocator<UGameMessageSubsystem::MaxMessages>> Live;
	if (Feed)
	{
		for (const FGameMessage& Message : Feed->GetMessages())
		{
			if (Message.EndTime > Now)
			{
				Live.Add(&Message);
			}
		}
	}
	const int32 First = FMath::Max(0, Live.Num() - Lines.Num());

	for (int32 Index = 0; Index < Lines.Num(); ++Index)
	{
		UTextBlock* Line = Lines[Index];
		const int32 MessageIndex = First + Index;
		if (!Live.IsValidIndex(MessageIndex))
		{
			Line->SetVisibility(ESlateVisibility::Collapsed);
			continue;
		}

		const float TimeLeft = static_cast<float>(Live[MessageIndex]->EndTime - Now);
		Line->SetText(Live[MessageIndex]->Text);
		Line->SetRenderOpacity(FadeOutTime > 0.0f ? FMath::Clamp(TimeLeft / FadeOutTime, 0.0f, 1.0f) : 1.0f);
		Line->SetVisibility(ESlateVisibility::HitTestInvisible);
	}
}
