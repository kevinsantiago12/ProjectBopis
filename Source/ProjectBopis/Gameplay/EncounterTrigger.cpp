// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/EncounterTrigger.h"
#include "Enemies/EnemyBase.h"
#include "Components/BoxComponent.h"
#include "Kismet/GameplayStatics.h"

AEncounterTrigger::AEncounterTrigger()
{
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->InitBoxExtent(FVector(200.0f, 200.0f, 100.0f));
	Volume->SetCollisionProfileName(TEXT("Trigger"));
	Volume->SetGenerateOverlapEvents(true);
	Volume->ShapeColor = FColor::Orange;
	RootComponent = Volume;
}

void AEncounterTrigger::BeginPlay()
{
	Super::BeginPlay();

	Volume->OnComponentBeginOverlap.AddDynamic(this, &AEncounterTrigger::OnVolumeOverlap);
}

void AEncounterTrigger::OnVolumeOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Player || OtherActor != Player || (bTriggerOnce && bTriggered))
	{
		return;
	}
	bTriggered = true;

	// The whole room at once: the sequence starts now.
	for (AEnemyBase* Enemy : Enemies)
	{
		if (Enemy && !Enemy->IsDead())
		{
			Enemy->Alert(Player);
		}
	}
}
