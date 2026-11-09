#include "Gameplay/LevelTravelSubsystem.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UObjectGlobals.h"
#include "Widgets/Images/SImage.h"

void ULevelTravelSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	PostLoadMapHandle = FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(
		this, &ULevelTravelSubsystem::OnPostLoadMap);
}

void ULevelTravelSubsystem::Deinitialize()
{
	FCoreUObjectDelegates::PostLoadMapWithWorld.Remove(PostLoadMapHandle);
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}
	RemoveCover();
	Super::Deinitialize();
}

void ULevelTravelSubsystem::FadeAndOpenLevel(const TSoftObjectPtr<UWorld>& Level, float FadeTime)
{
	UWorld* World = GetGameInstance()->GetWorld();
	if (IsTravelling() || !World)
	{
		return;
	}

	PendingLevel = Level.IsNull()
		? FName(*UGameplayStatics::GetCurrentLevelName(World))
		: FName(*Level.GetLongPackageName());
	FadeDuration = FMath::Max(FadeTime, 0.0f);
	FadeElapsed = 0.0f;

	if (UGameViewportClient* Viewport = GetGameInstance()->GetGameViewportClient())
	{
		RemoveCover();
		Cover = SNew(SImage).ColorAndOpacity(FLinearColor::Transparent);
		Viewport->AddViewportWidgetContent(Cover.ToSharedRef(), 1000);
	}
	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &ULevelTravelSubsystem::TickFade));
}

bool ULevelTravelSubsystem::TickFade(float DeltaTime)
{
	UWorld* World = GetGameInstance()->GetWorld();
	if (!World)
	{
		TickerHandle.Reset();
		RemoveCover();
		return false;
	}

	FadeElapsed += DeltaTime;
	const float Alpha = FadeDuration > 0.0f ? FMath::Min(FadeElapsed / FadeDuration, 1.0f) : 1.0f;
	if (Cover.IsValid())
	{
		Cover->SetColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, Alpha));
	}

	// The sound fades with the picture: the camera's fade does that (the engine puts the
	// volume back when the next level loads).
	APlayerController* Player = World->GetFirstPlayerController();
	if (Player && Player->PlayerCameraManager)
	{
		Player->PlayerCameraManager->SetManualCameraFade(Alpha, FLinearColor::Black, true);
	}

	if (Alpha < 1.0f)
	{
		return true;   // keep ticking
	}

	// Black: open the level. The cover stays up through the load (OnPostLoadMap takes it down).
	TickerHandle.Reset();
	UGameplayStatics::OpenLevel(World, PendingLevel);
	return false;      // done: the ticker drops this
}

void ULevelTravelSubsystem::OnPostLoadMap(UWorld* LoadedWorld)
{
	RemoveCover();
}

void ULevelTravelSubsystem::RemoveCover()
{
	if (Cover.IsValid())
	{
		if (UGameViewportClient* Viewport = GetGameInstance()->GetGameViewportClient())
		{
			Viewport->RemoveViewportWidgetContent(Cover.ToSharedRef());
		}
		Cover.Reset();
	}
}
