// Copyright Epic Games, Inc. All Rights Reserved.


#include "ProjectBopisPlayerController.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "InputMappingContext.h"
#include "ProjectBopisCameraManager.h"
#include "Blueprint/UserWidget.h"
#include "ProjectBopis.h"
#include "Widgets/Input/SVirtualJoystick.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Widgets/Images/SImage.h"
#include "Styling/CoreStyle.h"

AProjectBopisPlayerController::AProjectBopisPlayerController()
{
	// set the player camera manager class
	PlayerCameraManagerClass = AProjectBopisCameraManager::StaticClass();
}

void AProjectBopisPlayerController::BeginPlay()
{
	Super::BeginPlay();

	
	// only spawn touch controls on local player controllers
	if (IsLocalPlayerController() && ShouldUseTouchControls())
	{
		// spawn the mobile controls widget
		MobileControlsWidget = CreateWidget<UUserWidget>(this, MobileControlsWidgetClass);

		if (MobileControlsWidget)
		{
			// add the controls to the player screen
			MobileControlsWidget->AddToPlayerScreen(0);

		} else {

			UE_LOG(LogProjectBopis, Error, TEXT("Could not spawn mobile controls widget."));

		}

	}

	// Level start: black and paused until the frames settle (TickCurtain), then a fade-in.
	if (bLevelStartCurtain && IsLocalPlayerController())
	{
		if (UGameViewportClient* Viewport = GetWorld()->GetGameViewport())
		{
			Curtain = SNew(SImage)
				.Image(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.ColorAndOpacity(FLinearColor::Black);
			Viewport->AddViewportWidgetContent(Curtain.ToSharedRef(), 1000);
			UGameplayStatics::SetGamePaused(this, true);
			CurtainTicker = FTSTicker::GetCoreTicker().AddTicker(
				FTickerDelegate::CreateUObject(this, &AProjectBopisPlayerController::TickCurtain));
		}
	}
}

void AProjectBopisPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	FTSTicker::GetCoreTicker().RemoveTicker(CurtainTicker);
	RemoveCurtain();
	Super::EndPlay(EndPlayReason);
}

bool AProjectBopisPlayerController::TickCurtain(float DeltaTime)
{
	if (!Curtain.IsValid())
	{
		return false;
	}

	// Black and paused until the frames have run steady for SteadyTime in a row, within
	// MinBlackTime and MaxBlackTime. The first frame's time includes the load itself, so a
	// long frame counts for a quarter second at most.
	if (!bCurtainFading)
	{
		CurtainTime += FMath::Min(DeltaTime, 0.25f);
		SteadyFor = DeltaTime <= SteadyFrameTime ? SteadyFor + DeltaTime : 0.0f;
		if ((CurtainTime >= MinBlackTime && SteadyFor >= SteadyTime) || CurtainTime >= MaxBlackTime)
		{
			UGameplayStatics::SetGamePaused(this, false);
			bCurtainFading = true;
		}
		return true;
	}

	// Then the game runs and the black fades out.
	FadeTime += DeltaTime;
	const float Opacity = 1.0f - FMath::Clamp(FadeTime / FadeInTime, 0.0f, 1.0f);
	Curtain->SetColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, Opacity));
	if (Opacity <= 0.0f)
	{
		RemoveCurtain();
		return false;
	}
	return true;
}

void AProjectBopisPlayerController::RemoveCurtain()
{
	if (Curtain.IsValid())
	{
		if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
		{
			Viewport->RemoveViewportWidgetContent(Curtain.ToSharedRef());
		}
		Curtain.Reset();
	}
}

void AProjectBopisPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	// only add IMCs for local player controllers
	if (IsLocalPlayerController())
	{
		// Add Input Mapping Context
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
		{
			for (UInputMappingContext* CurrentContext : DefaultMappingContexts)
			{
				Subsystem->AddMappingContext(CurrentContext, 0);
			}

			// only add these IMCs if we're not using mobile touch input
			if (!ShouldUseTouchControls())
			{
				for (UInputMappingContext* CurrentContext : MobileExcludedMappingContexts)
				{
					Subsystem->AddMappingContext(CurrentContext, 0);
				}
			}
		}
	}
	
}

bool AProjectBopisPlayerController::ShouldUseTouchControls() const
{
	// are we on a mobile platform? Should we force touch?
	return SVirtualJoystick::ShouldDisplayTouchInterface() || bForceTouchControls;
}
