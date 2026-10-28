// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "Perception/AIPerceptionTypes.h"
#include "BopisAIController.generated.h"

class UAIPerceptionComponent;
class UAISenseConfig_Sight;
class UAISenseConfig_Hearing;
class UStateTreeAIComponent;

/**
 *  The enemies' controller: sees and hears for the pawn, and alerts it when the player
 *  shows up or a gun goes off nearby. Behaviour (the StateTree) comes later.
 */
UCLASS()
class PROJECTBOPIS_API ABopisAIController : public AAIController
{
	GENERATED_BODY()

public:

	ABopisAIController();

protected:

	virtual void BeginPlay() override;

	virtual void OnPossess(APawn* InPawn) override;

	/** Runs the pawn's Behaviour (AEnemyBase::Behaviour) — a StateTree per archetype. */
	UPROPERTY(VisibleAnywhere, Category = "AI")
	TObjectPtr<UStateTreeAIComponent> StateTree;

	UPROPERTY(VisibleAnywhere, Category = "AI")
	TObjectPtr<UAIPerceptionComponent> Perception;

	/** Defaults set in the constructor; a Blueprint subclass can tune them per archetype. */
	UPROPERTY(VisibleAnywhere, Category = "AI")
	TObjectPtr<UAISenseConfig_Sight> SightConfig;

	UPROPERTY(VisibleAnywhere, Category = "AI")
	TObjectPtr<UAISenseConfig_Hearing> HearingConfig;

private:

	UFUNCTION()
	void OnTargetPerceived(AActor* Actor, FAIStimulus Stimulus);

	/** Hands the pawn's StateTree to the component and starts it. */
	void StartBehaviour();

	/** StartBehaviour is queued on the level start's hold (see ULevelStartSubsystem). */
	bool bWaitingForLevelStart = false;
};
