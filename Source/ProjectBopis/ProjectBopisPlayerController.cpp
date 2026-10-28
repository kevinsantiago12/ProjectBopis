// Copyright Epic Games, Inc. All Rights Reserved.


#include "ProjectBopisPlayerController.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "InputMappingContext.h"
#include "ProjectBopisCameraManager.h"
#include "Blueprint/UserWidget.h"
#include "ProjectBopis.h"
#include "Widgets/Input/SVirtualJoystick.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Widgets/Images/SImage.h"
#include "Styling/CoreStyle.h"
#include "GameFramework/Character.h"
#include "Components/SkeletalMeshComponent.h"
#include "Enemies/EnemyBase.h"
#include "EngineUtils.h"
#include "Gameplay/LevelStartSubsystem.h"

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

	// Level start: black, the player's input off, until the scene's ready (TickCurtain), then a fade-in.
	if (bLevelStartCurtain && IsLocalPlayerController())
	{
		if (UGameViewportClient* Viewport = GetWorld()->GetGameViewport())
		{
			Curtain = SNew(SImage)
				.Image(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.ColorAndOpacity(FLinearColor::Black);
			Viewport->AddViewportWidgetContent(Curtain.ToSharedRef(), 1000);
			CurtainTicker = FTSTicker::GetCoreTicker().AddTicker(
				FTickerDelegate::CreateUObject(this, &AProjectBopisPlayerController::TickCurtain));
		}
	}

	// No black screen after all (not this player's, or no viewport): nothing to wait for.
	if (!Curtain.IsValid())
	{
		SetEnemiesHeld(false);
	}
}

void AProjectBopisPlayerController::PostInitializeComponents()
{
	Super::PostInitializeComponents();

	// Before the level's actors begin play, so an enemy spawned at the start is held too.
	if (bLevelStartCurtain && GetWorld() && GetWorld()->IsGameWorld())
	{
		SetEnemiesHeld(true);
	}
}

void AProjectBopisPlayerController::SetEnemiesHeld(bool bHeld)
{
	if (ULevelStartSubsystem* LevelStart = GetWorld() ? GetWorld()->GetSubsystem<ULevelStartSubsystem>() : nullptr)
	{
		LevelStart->SetHolding(bHeld);
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

	// Black, the player's input off, until everyone's dressed and the frames have run steady
	// for SteadyTime in a row since; at least MinBlackTime, at most MaxBlackTime. The first
	// frame's time includes the load itself, so a long frame counts for a quarter second at most.
	if (!bCurtainFading)
	{
		APawn* PlayerPawn = GetPawn();
		if (PlayerPawn && PlayerPawn->InputEnabled())
		{
			PlayerPawn->DisableInput(this);
		}

		CurtainTime += FMath::Min(DeltaTime, 0.25f);
		SteadyFor = (DeltaTime <= SteadyFrameTime && IsSceneReady()) ? SteadyFor + DeltaTime : 0.0f;
		if ((CurtainTime >= MinBlackTime && SteadyFor >= SteadyTime) || CurtainTime >= MaxBlackTime)
		{
			if (PlayerPawn)
			{
				PlayerPawn->EnableInput(this);
			}
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
		SetEnemiesHeld(false);
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

bool AProjectBopisPlayerController::IsSceneReady() const
{
	// Shown, with a body: the Character Customizer hides its characters, and fills their
	// meshes, only once their outfits have loaded. Sleepers stay hidden on purpose.
	auto IsDressed = [](const ACharacter* Person)
	{
		return Person && !Person->IsHidden() && Person->GetMesh()
			&& Person->GetMesh()->GetSkeletalMeshAsset();
	};

	if (!IsDressed(Cast<ACharacter>(GetPawn())))
	{
		return false;
	}
	for (TActorIterator<AEnemyBase> It(GetWorld()); It; ++It)
	{
		if (!It->IsAsleep() && !It->IsDead() && !IsDressed(*It))
		{
			return false;
		}
	}
	return true;
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
