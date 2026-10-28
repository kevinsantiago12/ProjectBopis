// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "Containers/Ticker.h"
#include "ProjectBopisPlayerController.generated.h"

class UInputMappingContext;
class UUserWidget;
class SImage;

/**
 *  Simple Player Controller
 *  Manages the input mapping context.
 *  Overrides the Player Camera Manager class.
 */
UCLASS(abstract, config="Game")
class PROJECTBOPIS_API AProjectBopisPlayerController : public APlayerController
{
	GENERATED_BODY()
	
public:

	/** Constructor */
	AProjectBopisPlayerController();

protected:

	/** Input Mapping Contexts */
	UPROPERTY(EditAnywhere, Category="Input|Input Mappings")
	TArray<UInputMappingContext*> DefaultMappingContexts;

	/** Input Mapping Contexts */
	UPROPERTY(EditAnywhere, Category="Input|Input Mappings")
	TArray<UInputMappingContext*> MobileExcludedMappingContexts;

	/** Mobile controls widget to spawn */
	UPROPERTY(EditAnywhere, Category="Input|Touch Controls")
	TSubclassOf<UUserWidget> MobileControlsWidgetClass;

	/** Pointer to the mobile controls widget */
	UPROPERTY()
	TObjectPtr<UUserWidget> MobileControlsWidget;

	/** If true, the player will use UMG touch controls even if not playing on mobile platforms */
	UPROPERTY(EditAnywhere, Config, Category = "Input|Touch Controls")
	bool bForceTouchControls = false;

	/** Level start (restarts too): the screen stays black and the game paused until the frames
	    run steady, the engine's warm-up (shaders, textures) hidden behind it, then fades in. */
	UPROPERTY(EditAnywhere, Category = "Level Start")
	bool bLevelStartCurtain = true;

	/** Frames this quick or quicker (seconds) count as steady: 1/45. */
	UPROPERTY(EditAnywhere, Category = "Level Start", meta = (ClampMin = "0.001"))
	float SteadyFrameTime = 0.022f;

	/** Seconds of steady frames in a row before the fade-in. */
	UPROPERTY(EditAnywhere, Category = "Level Start", meta = (ClampMin = "0.0"))
	float SteadyTime = 0.5f;

	/** Seconds of black at the least and at the most, steady or not. */
	UPROPERTY(EditAnywhere, Category = "Level Start", meta = (ClampMin = "0.0"))
	float MinBlackTime = 0.5f;

	UPROPERTY(EditAnywhere, Category = "Level Start", meta = (ClampMin = "0.0"))
	float MaxBlackTime = 3.0f;

	UPROPERTY(EditAnywhere, Category = "Level Start", meta = (ClampMin = "0.01"))
	float FadeInTime = 0.4f;

	/** Gameplay initialization */
	virtual void BeginPlay() override;

	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** Input mapping context setup */
	virtual void SetupInputComponent() override;

	/** Returns true if the player should use UMG touch controls */
	bool ShouldUseTouchControls() const;

private:
	/** Runs the black every frame, paused or not (real seconds). False once it's gone. */
	bool TickCurtain(float DeltaTime);

	void RemoveCurtain();

	/** The black over the whole screen, HUD included. */
	TSharedPtr<SImage> Curtain;
	FTSTicker::FDelegateHandle CurtainTicker;

	float CurtainTime = 0.0f;
	float SteadyFor = 0.0f;
	bool bCurtainFading = false;
	float FadeTime = 0.0f;
};
