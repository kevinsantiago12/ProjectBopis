// Copyright Epic Games, Inc. All Rights Reserved.

#include "Enemies/BopisAIController.h"
#include "Enemies/EnemyBase.h"
#include "Perception/AIPerceptionComponent.h"
#include "Perception/AISenseConfig_Sight.h"
#include "Perception/AISenseConfig_Hearing.h"
#include "Perception/AISense_Sight.h"
#include "Perception/AISense_Hearing.h"
#include "Kismet/GameplayStatics.h"
#include "Components/StateTreeAIComponent.h"
#include "StateTree.h"

ABopisAIController::ABopisAIController()
{
	Perception = CreateDefaultSubobject<UAIPerceptionComponent>(TEXT("Perception"));
	SetPerceptionComponent(*Perception);

	// Everyone counts: nothing has a team yet, and the player would otherwise be "neutral"
	// and go unseen.
	SightConfig = CreateDefaultSubobject<UAISenseConfig_Sight>(TEXT("Sight"));
	SightConfig->SightRadius = 3000.0f;
	SightConfig->LoseSightRadius = 3500.0f;
	SightConfig->PeripheralVisionAngleDegrees = 70.0f;
	SightConfig->DetectionByAffiliation.bDetectEnemies = true;
	SightConfig->DetectionByAffiliation.bDetectNeutrals = true;
	SightConfig->DetectionByAffiliation.bDetectFriendlies = true;
	Perception->ConfigureSense(*SightConfig);

	// Wide open: how far a shot carries is the weapon's NoiseRange, not the listener's.
	HearingConfig = CreateDefaultSubobject<UAISenseConfig_Hearing>(TEXT("Hearing"));
	HearingConfig->HearingRange = 10000.0f;
	HearingConfig->DetectionByAffiliation.bDetectEnemies = true;
	HearingConfig->DetectionByAffiliation.bDetectNeutrals = true;
	HearingConfig->DetectionByAffiliation.bDetectFriendlies = true;
	Perception->ConfigureSense(*HearingConfig);

	Perception->SetDominantSense(SightConfig->GetSenseImplementation());

	// The tree comes from the pawn (per archetype), so it's started by hand once both are ready.
	StateTree = CreateDefaultSubobject<UStateTreeAIComponent>(TEXT("StateTree"));
	StateTree->SetStartLogicAutomatically(false);
	BrainComponent = StateTree;
}

void ABopisAIController::BeginPlay()
{
	Super::BeginPlay();

	Perception->OnTargetPerceptionUpdated.AddDynamic(this, &ABopisAIController::OnTargetPerceived);

	// Possessed before play began (placed in the level): start now that the components are up.
	if (GetPawn())
	{
		StartBehaviour();
	}
}

void ABopisAIController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	// Spawned mid-game: play has already begun, so start straight away.
	if (HasActorBegunPlay())
	{
		StartBehaviour();
	}
}

void ABopisAIController::StartBehaviour()
{
	const AEnemyBase* Enemy = Cast<AEnemyBase>(GetPawn());
	if (Enemy && Enemy->GetBehaviour() && !StateTree->IsRunning())
	{
		StateTree->SetStateTree(Enemy->GetBehaviour());
		StateTree->StartLogic();
	}
}

void ABopisAIController::OnTargetPerceived(AActor* Actor, FAIStimulus Stimulus)
{
	AEnemyBase* Enemy = Cast<AEnemyBase>(GetPawn());
	APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Enemy || !Player || !Stimulus.WasSuccessfullySensed())
	{
		return;
	}

	// Seeing the player, or hearing any gunfire (the player's, or an ally shooting at them):
	// either way the fight is on, and it's the player it's about.
	const bool bSawPlayer = Actor == Player && Stimulus.Type == UAISense::GetSenseID<UAISense_Sight>();
	const bool bHeardGunfire = Stimulus.Type == UAISense::GetSenseID<UAISense_Hearing>();
	if (bSawPlayer || bHeardGunfire)
	{
		Enemy->Alert(Player);
	}

	// The player's own gunfire: where it came from is where they are, even behind a wall.
	if (bHeardGunfire && Actor == Player)
	{
		Enemy->HearPlayer(Stimulus.StimulusLocation);
	}
}
