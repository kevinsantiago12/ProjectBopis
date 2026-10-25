// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/LevelExitTrigger.h"
#include "BopisCharacterBase.h"
#include "Gameplay/FocusComponent.h"
#include "Gameplay/MusicSubsystem.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/BillboardComponent.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "UObject/ConstructorHelpers.h"

ALevelExitTrigger::ALevelExitTrigger()
{
	// Ticks only to count down to the load, once the player's out.
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->InitBoxExtent(FVector(200.0f, 200.0f, 100.0f));
	Volume->SetCollisionProfileName(TEXT("Trigger"));
	Volume->SetGenerateOverlapEvents(true);
	Volume->ShapeColor = FColor(60, 220, 90);
	RootComponent = Volume;

	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(Volume);
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(24.0f);
	Label->SetTextRenderColor(FColor(60, 220, 90));
	Label->SetHiddenInGame(true);
	Label->bIsEditorOnly = true;

#if WITH_EDITORONLY_DATA
	Icon = CreateEditorOnlyDefaultSubobject<UBillboardComponent>(TEXT("Icon"));
	if (Icon)
	{
		static ConstructorHelpers::FObjectFinderOptional<UTexture2D> TriggerSprite(TEXT("/Engine/EditorResources/S_Trigger"));
		Icon->Sprite = TriggerSprite.Get();
		Icon->SetupAttachment(Volume);
		Icon->SetRelativeScale3D(FVector(2.0f));
	}
#endif
}

void ALevelExitTrigger::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

#if WITH_EDITOR
	// Above the box, whatever its size: where it goes.
	Label->SetRelativeLocation(FVector(0.0f, 0.0f, Volume->GetUnscaledBoxExtent().Z + 40.0f));
	const FString Next = NextLevel.IsNull() ? FString(TEXT("restarts this level")) : NextLevel.GetAssetName();
	Label->SetText(FText::FromString(FString::Printf(TEXT("EXIT\n%s"), *Next)));
#endif
}

void ALevelExitTrigger::BeginPlay()
{
	Super::BeginPlay();

	Volume->OnComponentBeginOverlap.AddDynamic(this, &ALevelExitTrigger::OnVolumeOverlap);
}

void ALevelExitTrigger::OnVolumeOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (OtherActor && OtherActor == UGameplayStatics::GetPlayerPawn(this, 0))
	{
		Fire();
	}
}

void ALevelExitTrigger::Fire()
{
	ABopisCharacterBase* Player = Cast<ABopisCharacterBase>(UGameplayStatics::GetPlayerPawn(this, 0));
	APlayerController* Controller = UGameplayStatics::GetPlayerController(this, 0);
	if (bExited || !Player || Player->IsDead() || !Controller)
	{
		return;
	}
	bExited = true;

	// The level's over: no dying in its last seconds, no more input, time back to normal.
	Player->SetCanBeDamaged(false);
	Player->DisableInput(Controller);
	if (UFocusComponent* Focus = Player->FindComponentByClass<UFocusComponent>())
	{
		Focus->StopFocus();
	}

	// The HUD goes (an open weapon wheel with it) and the picture fades to black, held there.
	UWidgetLayoutLibrary::RemoveAllWidgets(this);
	if (Controller->PlayerCameraManager)
	{
		Controller->PlayerCameraManager->StartCameraFade(0.0f, 1.0f, FadeTime, FLinearColor::Black, false, true);
	}
	if (bFadeOutMusic)
	{
		if (UMusicSubsystem* Music = GetWorld()->GetSubsystem<UMusicSubsystem>())
		{
			Music->StopMusic(FadeTime);
		}
	}
	if (CompleteWidgetClass)
	{
		if (UUserWidget* Widget = CreateWidget<UUserWidget>(Controller, CompleteWidgetClass))
		{
			Widget->AddToViewport(100);
		}
	}

	SetActorTickEnabled(true);
}

void ALevelExitTrigger::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Counted in real seconds, as the death's restart is: a kill's slow motion can't stretch it.
	TimeSinceExit += FApp::GetDeltaTime();
	if (TimeSinceExit < FMath::Max(LoadDelay, FadeTime))
	{
		return;
	}
	SetActorTickEnabled(false);
	if (NextLevel.IsNull())
	{
		UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)));
	}
	else
	{
		UGameplayStatics::OpenLevelBySoftObjectPtr(this, NextLevel);
	}
}
