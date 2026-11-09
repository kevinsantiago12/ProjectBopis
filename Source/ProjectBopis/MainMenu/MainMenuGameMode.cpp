#include "MainMenu/MainMenuGameMode.h"
#include "MainMenu/MainMenuPlayerController.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "Camera/CameraActor.h"
#include "EngineUtils.h"

AMainMenuGameMode::AMainMenuGameMode()
{
	DefaultPawnClass = nullptr;
}

void AMainMenuGameMode::BeginPlay()
{
	Super::BeginPlay();

	if (Scenes.Num() > 0)
	{
		ShowScene(bRandomScene ? FMath::RandRange(0, Scenes.Num() - 1) : 0);
	}
}

bool AMainMenuGameMode::PlayerCanRestart_Implementation(APlayerController* Player)
{
	return false;
}

void AMainMenuGameMode::ShowScene(int32 Index)
{
	if (!Scenes.IsValidIndex(Index))
	{
		return;
	}

	if (CurrentScene)
	{
		CurrentScene->OnLevelShown.RemoveDynamic(this, &AMainMenuGameMode::OnSceneShown);
		CurrentScene->SetIsRequestingUnloadAndRemoval(true);
		CurrentScene = nullptr;
	}

	// Loads in the background; OnLevelShown fires once it's in and visible.
	bool bLoaded = false;
	CurrentScene = ULevelStreamingDynamic::LoadLevelInstanceBySoftObjectPtr(
		this, Scenes[Index], FVector::ZeroVector, FRotator::ZeroRotator, bLoaded);

	if (bLoaded && CurrentScene)
	{
		CurrentScene->OnLevelShown.AddDynamic(this, &AMainMenuGameMode::OnSceneShown);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Main menu: couldn't load scene %d (%s)"),
			Index, *Scenes[Index].ToString());
	}
}

void AMainMenuGameMode::OnSceneShown()
{
	CameraSearchTimeLeft = CameraSearchTimeout;
	FindSceneCamera();
}

void AMainMenuGameMode::FindSceneCamera()
{
	UWorld* World = GetWorld();
	for (TActorIterator<ACameraActor> It(World); It; ++It)
	{
		ACameraActor* Camera = *It;
		if (Camera->GetLevel() == World->PersistentLevel || Camera == SceneCamera.Get())
		{
			continue;   // the hub's own, or the scene we just left
		}

		SceneCamera = Camera;
		if (AMainMenuPlayerController* Controller =
			Cast<AMainMenuPlayerController>(World->GetFirstPlayerController()))
		{
			Controller->ViewSceneCamera(Camera);
		}
		return;
	}

	// Not in yet: World Partition loads the scene's actors just after the scene shows.
	constexpr float RetryInterval = 0.1f;
	CameraSearchTimeLeft -= RetryInterval;
	if (CameraSearchTimeLeft > 0.0f)
	{
		GetWorldTimerManager().SetTimer(CameraSearchTimer, this,
			&AMainMenuGameMode::FindSceneCamera, RetryInterval, false);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Main menu: scene %s has no camera"),
			CurrentScene ? *CurrentScene->GetWorldAssetPackageName() : TEXT("(none)"));
	}
}
