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
	FString WaveText;
	if (Waves.Num() > 0)
	{
		int32 WaveSpawns = 0;
		for (const FEncounterWave& Wave : Waves)
		{
			WaveSpawns += Wave.Spawns.Num();
		}
		WaveText = FString::Printf(TEXT("\nWaves %d (%d spawns)"), Waves.Num(), WaveSpawns);
	}
	Label->SetRelativeLocation(FVector(0.0f, 0.0f, Volume->GetUnscaledBoxExtent().Z + 40.0f));
	Label->SetText(FText::FromString(FString::Printf(TEXT("TRIGGER\n%s\nEnemies %d  Spawns %d (ahead %d)%s"),
		*GetActorLabel(), Enemies.Num(), Spawns.Num(), SpawnAhead, *WaveText)));
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
	const FColor WaveSpawnColor(255, 120, 170);
	const FColor AmbushColor(255, 190, 0);
	const FColor PatrolColor(40, 220, 80);
	const FColor WaitColor(0, 200, 255);
	const FColor EventColor(220, 80, 255);
	const FColor ClearedColor(255, 255, 255);

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

	// What it sets going once the room's cleared: white arrows.
	for (const AEncounterEvent* Event : EventsOnCleared)
	{
		if (Event)
		{
			DrawDebugDirectionalArrow(World, From, Event->GetActorLocation(), 60.0f, ClearedColor, false, -1.0f, SDPG_World, 2.0f);
		}
	}
	for (const AEncounterTrigger* Trigger : TriggersOnCleared)
	{
		if (Trigger)
		{
			DrawDebugDirectionalArrow(World, From, Trigger->GetActorLocation(), 60.0f, ClearedColor, false, -1.0f, SDPG_World, 2.0f);
		}
	}

	// A spawn entry: a line to where it appears, then its moves from there.
	auto DrawSpawn = [&](const FEncounterSpawn& Spawn, const FColor& Color)
	{
		if (!Spawn.SpawnPoint)
		{
			return;
		}
		const FVector SpawnAt = Spawn.SpawnPoint->GetActorLocation();
		Line(From, SpawnAt, Color);
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
	};

	for (const FEncounterSpawn& Spawn : Spawns)
	{
		DrawSpawn(Spawn, SpawnColor);
	}
	for (const FEncounterWave& Wave : Waves)
	{
		for (const FEncounterSpawn& Spawn : Wave.Spawns)
		{
			DrawSpawn(Spawn, WaveSpawnColor);
		}
		for (const AEncounterEvent* Event : Wave.EventsToStart)
		{
			if (Event)
			{
				DrawDebugDirectionalArrow(World, From, Event->GetActorLocation(), 60.0f, EventColor, false, -1.0f, SDPG_World, 2.0f);
			}
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

	// Everyone it will bring in is built now, behind the level load, and put to sleep where the
	// trigger stands: bringing one in only wakes it, so nothing is built mid-fight.
	BuildReserves(INDEX_NONE, Spawns);
	for (int32 WaveIndex = 0; WaveIndex < Waves.Num(); ++WaveIndex)
	{
		BuildReserves(WaveIndex, Waves[WaveIndex].Spawns);
	}

	// Watches the room from the start, for its waves and for its being cleared: one shot clear
	// from the doorway, before the player walks in, counts too.
	GetWorldTimerManager().SetTimer(RoomTimer, this, &AEncounterTrigger::UpdateRoom, 0.25f, true);
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
		BringIn(INDEX_NONE);
		for (AEncounterEvent* Event : EventsToStart)
		{
			if (Event)
			{
				Event->StartEvent();
			}
		}
	}
}

void AEncounterTrigger::BringIn(int32 WaveIndex)
{
	const TArray<FEncounterSpawn>& List = WaveIndex == INDEX_NONE ? Spawns : Waves[WaveIndex].Spawns;
	PendingSpawns += List.Num();
	for (int32 Index = 0; Index < List.Num(); ++Index)
	{
		if (List[Index].Delay > 0.0f)
		{
			FTimerHandle Timer;
			GetWorldTimerManager().SetTimer(Timer,
				FTimerDelegate::CreateUObject(this, &AEncounterTrigger::SpawnOne, WaveIndex, Index), List[Index].Delay, false);
		}
		else
		{
			SpawnOne(WaveIndex, Index);
		}
	}
}

void AEncounterTrigger::SpawnOne(int32 WaveIndex, int32 Index)
{
	// This one's moment has come, whether or not it makes it in.
	PendingSpawns = FMath::Max(0, PendingSpawns - 1);

	const TArray<FEncounterSpawn>* List = WaveIndex == INDEX_NONE ? &Spawns
		: (Waves.IsValidIndex(WaveIndex) ? &Waves[WaveIndex].Spawns : nullptr);
	if (!List || !List->IsValidIndex(Index))
	{
		return;
	}
	const FEncounterSpawn& Spawn = (*List)[Index];
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

	// Its reserve, built asleep at the start, wakes on the point; without one, it's built now.
	TWeakObjectPtr<AEnemyBase> Reserve;
	Reserves.RemoveAndCopyValue(FIntPoint(WaveIndex, Index), Reserve);
	AEnemyBase* Enemy = Reserve.Get();
	if (Enemy)
	{
		Enemy->Wake(SpawnTransform);
	}
	else
	{
		Enemy = BuildEnemy(Class, Spawn.Weapon, SpawnTransform, false);
		if (!Enemy)
		{
			return;
		}
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

	// Spawned ahead: joins its own trigger (asleep, unless patrolling), and is that room's to
	// clear. Otherwise it's this room's: a patroller just patrols, the rest come in set off.
	if (Spawn.WaitForTrigger)
	{
		Spawn.WaitForTrigger->AddEnemy(Enemy, !bPatroller);
		return;
	}
	Enemies.Add(Enemy);
	if (!bPatroller)
	{
		Enemy->SetWaitingForTrigger(true);
		Enemy->TriggerAmbush(Player);
	}
}

int32 AEncounterTrigger::GetAliveCount() const
{
	int32 Alive = PendingSpawns;
	for (const AEnemyBase* Enemy : Enemies)
	{
		if (IsValid(Enemy) && !Enemy->IsDead())
		{
			++Alive;
		}
	}
	return Alive;
}

bool AEncounterTrigger::IsRoomDone() const
{
	if (bCleared)
	{
		return true;
	}
	// A wave still to come (they come once it's fired).
	if (bTriggered && Waves.IsValidIndex(NextWave))
	{
		return false;
	}
	// Not while it still has spawns or waves to bring in, nor before it's had anyone to clear.
	const bool bAllIn = bTriggered || (Spawns.Num() == 0 && Waves.Num() == 0);
	const bool bHadAnyone = bTriggered || Enemies.Num() > 0;
	return bAllIn && bHadAnyone && GetAliveCount() == 0;
}

void AEncounterTrigger::UpdateRoom()
{
	if (bCleared)
	{
		return;
	}

	// The next wave, once the trigger's fired and the wave before is all in: due when the room's
	// thinned out to its count, and in its Delay later. No clearing while one's still to come.
	if (bTriggered && Waves.IsValidIndex(NextWave))
	{
		const FEncounterWave& Wave = Waves[NextWave];
		const double Now = GetWorld()->GetTimeSeconds();
		if (NextWaveAt < 0.0 && PendingSpawns == 0 && GetAliveCount() <= Wave.StartWhenAliveAtMost)
		{
			NextWaveAt = Now + Wave.Delay;
		}
		if (NextWaveAt >= 0.0 && Now >= NextWaveAt)
		{
			const int32 WaveIndex = NextWave++;
			NextWaveAt = -1.0;
			BringIn(WaveIndex);
			for (AEncounterEvent* Event : Wave.EventsToStart)
			{
				if (Event)
				{
					Event->StartEvent();
				}
			}
			OnWaveStarted.Broadcast(this, WaveIndex);
		}
		return;
	}

	if (!IsRoomDone())
	{
		return;
	}
	bCleared = true;
	GetWorldTimerManager().ClearTimer(RoomTimer);

	for (AEncounterEvent* Event : EventsOnCleared)
	{
		if (Event)
		{
			Event->StartEvent();
		}
	}
	for (AEncounterTrigger* Trigger : TriggersOnCleared)
	{
		if (Trigger)
		{
			Trigger->Fire();
		}
	}
	OnCleared.Broadcast(this);
}

void AEncounterTrigger::BuildReserves(int32 WaveIndex, const TArray<FEncounterSpawn>& List)
{
	const FTransform Hideout(GetActorLocation());
	for (int32 Index = 0; Index < List.Num(); ++Index)
	{
		const FEncounterSpawn& Spawn = List[Index];
		const TSubclassOf<AEnemyBase> Class = Spawn.EnemyClass ? Spawn.EnemyClass : DefaultEnemyClass;
		if (!Class || !Spawn.SpawnPoint)
		{
			continue;
		}
		if (AEnemyBase* Reserve = BuildEnemy(Class, Spawn.Weapon, Hideout, true))
		{
			Reserves.Add(FIntPoint(WaveIndex, Index), Reserve);
		}
	}
}

AEnemyBase* AEncounterTrigger::BuildEnemy(TSubclassOf<AEnemyBase> Class, TSubclassOf<AWeaponBase> Weapon,
	const FTransform& Where, bool bAsleep)
{
	// Deferred, so its gun is chosen before it begins play and equips one. A reserve always
	// spawns (it's hidden), and without a controller, so no AI runs until it wakes.
	AEnemyBase* Enemy = GetWorld()->SpawnActorDeferred<AEnemyBase>(Class, Where, nullptr, nullptr,
		bAsleep ? ESpawnActorCollisionHandlingMethod::AlwaysSpawn
			: ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding);
	if (!Enemy)
	{
		return nullptr;
	}
	if (Weapon)
	{
		if (UWeaponHolderComponent* Holder = Enemy->GetWeaponHolder())
		{
			Holder->SetStartingWeaponClass(Weapon);
		}
	}
	if (bAsleep)
	{
		Enemy->AutoPossessAI = EAutoPossessAI::Disabled;
	}
	Enemy->FinishSpawning(Where);
	if (!IsValid(Enemy))
	{
		return nullptr;
	}
	if (bAsleep)
	{
		Enemy->Sleep();
	}
	return Enemy;
}
