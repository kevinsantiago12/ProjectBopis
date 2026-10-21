// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/EncounterTrigger.h"
#include "Enemies/EnemyBase.h"
#include "Gameplay/EncounterEvent.h"
#include "Weapons/WeaponBase.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/BillboardComponent.h"
#include "Engine/Texture2D.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "DrawDebugHelpers.h"

AEncounterTrigger::AEncounterTrigger()
{
	// Ticks only for the editor's link lines; play turns it off in BeginPlay.
	PrimaryActorTick.bCanEverTick = true;

	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->InitBoxExtent(FVector(200.0f, 200.0f, 100.0f));
	Volume->SetCollisionProfileName(TEXT("Trigger"));
	Volume->SetGenerateOverlapEvents(true);
	Volume->ShapeColor = FColor::Orange;
	RootComponent = Volume;

	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(Volume);
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(24.0f);
	Label->SetTextRenderColor(FColor(255, 140, 0));
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

void AEncounterTrigger::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

#if WITH_EDITOR
	// Above the box, whatever its size: name, then what it sets off.
	int32 SpawnAhead = 0;
	for (const FEncounterSpawn& Spawn : Spawns)
	{
		SpawnAhead += Spawn.WaitForTrigger ? 1 : 0;
	}
	Label->SetRelativeLocation(FVector(0.0f, 0.0f, Volume->GetUnscaledBoxExtent().Z + 40.0f));
	Label->SetText(FText::FromString(FString::Printf(TEXT("TRIGGER\n%s\nEnemies %d  Spawns %d (ahead %d)"),
		*GetActorLabel(), Enemies.Num(), Spawns.Num(), SpawnAhead)));
#endif
}

void AEncounterTrigger::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

#if WITH_EDITOR
	const UWorld* World = GetWorld();
	if (bDrawLinks && World && World->WorldType == EWorldType::Editor)
	{
		DrawLinks();
	}
#endif
}

void AEncounterTrigger::DrawLinks() const
{
	const UWorld* World = GetWorld();
	const FVector From = GetActorLocation();
	const FColor EnemyColor(255, 140, 0);
	const FColor SpawnColor(255, 40, 40);
	const FColor AmbushColor(255, 190, 0);
	const FColor PatrolColor(40, 220, 80);
	const FColor WaitColor(0, 200, 255);
	const FColor EventColor(220, 80, 255);

	// One frame's worth: redrawn every editor tick, so moving anything updates the lines.
	auto Line = [World](const FVector& A, const FVector& B, const FColor& Color)
	{
		DrawDebugLine(World, A, B, Color, false, -1.0f, SDPG_World, 2.0f);
	};
	auto Route = [&Line, &PatrolColor](FVector Start, const TArray<TObjectPtr<AActor>>& Points)
	{
		for (const AActor* Point : Points)
		{
			if (Point)
			{
				Line(Start, Point->GetActorLocation(), PatrolColor);
				Start = Point->GetActorLocation();
			}
		}
	};

	for (const AEnemyBase* Enemy : Enemies)
	{
		if (!Enemy)
		{
			continue;
		}
		Line(From, Enemy->GetActorLocation(), EnemyColor);
		if (const AActor* Point = Enemy->GetAmbushPoint())
		{
			Line(Enemy->GetActorLocation(), Point->GetActorLocation(), AmbushColor);
		}
		Route(Enemy->GetActorLocation(), Enemy->GetPatrolPoints());
	}

	for (const AEncounterEvent* Event : EventsToStart)
	{
		if (Event)
		{
			DrawDebugDirectionalArrow(World, From, Event->GetActorLocation(), 60.0f, EventColor, false, -1.0f, SDPG_World, 2.0f);
		}
	}

	for (const FEncounterSpawn& Spawn : Spawns)
	{
		if (!Spawn.SpawnPoint)
		{
			continue;
		}
		const FVector SpawnAt = Spawn.SpawnPoint->GetActorLocation();
		Line(From, SpawnAt, SpawnColor);
		if (Spawn.AmbushPoint)
		{
			Line(SpawnAt, Spawn.AmbushPoint->GetActorLocation(), AmbushColor);
		}
		Route(SpawnAt, Spawn.PatrolPoints);
		if (Spawn.WaitForTrigger)
		{
			// Which trigger wakes it: an arrow from where it appears to that trigger.
			DrawDebugDirectionalArrow(World, SpawnAt, Spawn.WaitForTrigger->GetActorLocation(), 60.0f,
				WaitColor, false, -1.0f, SDPG_World, 2.0f);
		}
	}
}

void AEncounterTrigger::BeginPlay()
{
	Super::BeginPlay();

	// The link lines are editor-only; nothing to tick in play.
	SetActorTickEnabled(false);

	Volume->OnComponentBeginOverlap.AddDynamic(this, &AEncounterTrigger::OnVolumeOverlap);

	for (AEnemyBase* Enemy : Enemies)
	{
		if (Enemy)
		{
			Enemy->SetWaitingForTrigger(bEnemiesWaitForTrigger);
		}
	}
}

void AEncounterTrigger::AddEnemy(AEnemyBase* Enemy, bool bWait)
{
	if (!Enemy)
	{
		return;
	}
	Enemies.Add(Enemy);
	Enemy->SetWaitingForTrigger(bWait && bEnemiesWaitForTrigger);
	if (bTriggered)
	{
		if (APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0))
		{
			Enemy->TriggerAmbush(Player);
		}
	}
}

void AEncounterTrigger::OnVolumeOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (OtherActor && OtherActor == UGameplayStatics::GetPlayerPawn(this, 0))
	{
		Fire();
	}
}

void AEncounterTrigger::Fire()
{
	APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Player || (bTriggerOnce && bTriggered))
	{
		return;
	}
	const bool bFirstTime = !bTriggered;
	bTriggered = true;

	// The whole room at once: the sequence starts now.
	for (AEnemyBase* Enemy : Enemies)
	{
		if (Enemy && !Enemy->IsDead())
		{
			Enemy->TriggerAmbush(Player);
		}
	}

	// And whoever comes in, and whatever it sets going: once, each spawn on its own delay. The
	// spawns first, so an event's speakers are already there when it starts.
	if (bFirstTime)
	{
		for (int32 Index = 0; Index < Spawns.Num(); ++Index)
		{
			if (Spawns[Index].Delay > 0.0f)
			{
				FTimerHandle Timer;
				GetWorldTimerManager().SetTimer(Timer,
					FTimerDelegate::CreateUObject(this, &AEncounterTrigger::SpawnOne, Index), Spawns[Index].Delay, false);
			}
			else
			{
				SpawnOne(Index);
			}
		}
		for (AEncounterEvent* Event : EventsToStart)
		{
			if (Event)
			{
				Event->StartEvent();
			}
		}
	}
}

void AEncounterTrigger::SpawnOne(int32 Index)
{
	if (!Spawns.IsValidIndex(Index))
	{
		return;
	}
	const FEncounterSpawn& Spawn = Spawns[Index];
	const TSubclassOf<AEnemyBase> Class = Spawn.EnemyClass ? Spawn.EnemyClass : DefaultEnemyClass;
	APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Class || !Spawn.SpawnPoint || !Player)
	{
		return;
	}

	// Stood on the point, not sunk into the floor (as the director does).
	const float HalfHeight = Class->GetDefaultObject<AEnemyBase>()->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FTransform SpawnTransform(FRotator(0.0f, Spawn.SpawnPoint->GetActorRotation().Yaw, 0.0f),
		Spawn.SpawnPoint->GetActorLocation() + FVector(0.0f, 0.0f, HalfHeight));

	// Deferred, so its gun is chosen before it begins play and equips one.
	AEnemyBase* Enemy = GetWorld()->SpawnActorDeferred<AEnemyBase>(Class, SpawnTransform, nullptr, nullptr,
		ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding);
	if (!Enemy)
	{
		return;
	}
	if (Spawn.Weapon)
	{
		if (UWeaponHolderComponent* Holder = Enemy->GetWeaponHolder())
		{
			Holder->SetStartingWeaponClass(Spawn.Weapon);
		}
	}
	Enemy->FinishSpawning(SpawnTransform);
	if (!IsValid(Enemy))
	{
		return;
	}

	if (!Spawn.Tag.IsNone())
	{
		Enemy->Tags.AddUnique(Spawn.Tag);
	}
	if (Spawn.Voice)
	{
		Enemy->SetBarkVoice(Spawn.Voice);
	}
	Enemy->SetAmbush(Spawn.AmbushPoint, Spawn.bRushOnTrigger, Spawn.AmbushAcceptanceRadius);
	Enemy->SetHold(Spawn.bHoldsPosition, Spawn.HoldRadius, Spawn.bCrouchWhileHolding);

	// No ambush move and no post to hold: a patroller, walking its route with its senses on.
	const bool bPatroller = !Spawn.AmbushPoint && !Spawn.bRushOnTrigger && !Spawn.bHoldsPosition;
	if (bPatroller)
	{
		Enemy->SetPatrolPoints(Spawn.PatrolPoints);
	}

	// Spawned ahead: joins its own trigger (asleep, unless patrolling). Otherwise a patroller just
	// patrols, and the rest come in already set off.
	if (Spawn.WaitForTrigger)
	{
		Spawn.WaitForTrigger->AddEnemy(Enemy, !bPatroller);
	}
	else if (!bPatroller)
	{
		Enemy->SetWaitingForTrigger(true);
		Enemy->TriggerAmbush(Player);
	}
}
