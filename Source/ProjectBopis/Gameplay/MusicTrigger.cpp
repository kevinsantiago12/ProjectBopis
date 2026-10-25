// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/MusicTrigger.h"
#include "Gameplay/MusicSubsystem.h"
#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/BillboardComponent.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/GameplayStatics.h"

AMusicTrigger::AMusicTrigger()
{
	PrimaryActorTick.bCanEverTick = false;

	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->InitBoxExtent(FVector(200.0f, 200.0f, 100.0f));
	Volume->SetCollisionProfileName(TEXT("Trigger"));
	Volume->SetGenerateOverlapEvents(true);
	Volume->ShapeColor = FColor(80, 160, 255);
	RootComponent = Volume;

	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(Volume);
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(24.0f);
	Label->SetTextRenderColor(FColor(80, 160, 255));
	Label->SetHiddenInGame(true);
	Label->bIsEditorOnly = true;

#if WITH_EDITORONLY_DATA
	Icon = CreateEditorOnlyDefaultSubobject<UBillboardComponent>(TEXT("Icon"));
	if (Icon)
	{
		static ConstructorHelpers::FObjectFinderOptional<UTexture2D> MusicSprite(TEXT("/Engine/EditorResources/AudioIcons/S_AudioComponent"));
		Icon->Sprite = MusicSprite.Get();
		Icon->SetupAttachment(Volume);
		Icon->SetRelativeScale3D(FVector(2.0f));
	}
#endif
}

void AMusicTrigger::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

#if WITH_EDITOR
	// Above the box, whatever its size: what it changes the music to.
	Label->SetRelativeLocation(FVector(0.0f, 0.0f, Volume->GetUnscaledBoxExtent().Z + 40.0f));
	Label->SetText(FText::FromString(FString::Printf(TEXT("MUSIC%s\n%s"),
		bPlayAtStart ? TEXT(" (at start)") : TEXT(""), Track ? *Track->GetName() : TEXT("fade out"))));
#endif
}

void AMusicTrigger::BeginPlay()
{
	Super::BeginPlay();

	Volume->OnComponentBeginOverlap.AddDynamic(this, &AMusicTrigger::OnVolumeOverlap);
	if (bPlayAtStart)
	{
		Fire();
	}
}

void AMusicTrigger::OnVolumeOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (OtherActor && OtherActor == UGameplayStatics::GetPlayerPawn(this, 0))
	{
		Fire();
	}
}

void AMusicTrigger::Fire()
{
	if (bTriggerOnce && bTriggered)
	{
		return;
	}
	bTriggered = true;

	if (UMusicSubsystem* Music = GetWorld()->GetSubsystem<UMusicSubsystem>())
	{
		Music->PlayMusic(Track, FadeTime, TrackVolume);
	}
}
