// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Tasks/StateTreeAITask.h"
#include "Conditions/StateTreeAIConditionBase.h"
#include "GunmanStateTreeNodes.generated.h"

class AAIController;

UENUM()
enum class EGunmanMoveGoal : uint8
{
	/** Where to fight from next, picked by the enemy (AEnemyBase::ChooseNextSpot) — sometimes a push. */
	EngageSpot,
	/** Where the player was last seen (or heard). */
	LastKnownPosition,
	/** Nothing to go on: somewhere to roam to (AEnemyBase::ChooseRoamSpot). */
	Roam
};

USTRUCT()
struct FGunmanMoveTaskInstanceData
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = Context)
	TObjectPtr<AAIController> AIController = nullptr;

	UPROPERTY(EditAnywhere, Category = Parameter)
	EGunmanMoveGoal Goal = EGunmanMoveGoal::EngageSpot;

	/** How close counts as arrived (cm). */
	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = "0.0"))
	float AcceptanceRadius = 50.0f;

	/** Last Known Position only: keep heading for the newest sighting or sound, and stay on
	    the spot listening rather than finishing on arrival. */
	UPROPERTY(EditAnywhere, Category = Parameter)
	bool bFollowNewInfo = true;

	/** Where the move is headed now. */
	UPROPERTY()
	FVector Destination = FVector::ZeroVector;
};

/** Walks the gunman to its goal, gun up and facing the player all the way — shooting is the
    enemy's own business. Succeeds on arrival; fails if there's nowhere to go. */
USTRUCT(meta = (DisplayName = "Gunman Move", Category = "AI|Gunman"))
struct FGunmanMoveTask : public FStateTreeAIActionTaskBase
{
	GENERATED_BODY()

	using FInstanceDataType = FGunmanMoveTaskInstanceData;
	virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }

	virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;
	virtual EStateTreeRunStatus Tick(FStateTreeExecutionContext& Context, const float DeltaTime) const override;
	virtual void ExitState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override;
};

UENUM()
enum class EGunmanCheck : uint8
{
	IsAlerted,
	/** Alerted, but the player has been out of sight for LostForSeconds. */
	HasLostPlayer,
	/** Its shots have been held for an ally in the way for the enemy's
	    RepositionWhenBlockedAfter — time to find a new spot. */
	LineOfFireBlocked,
	/** Alerted, the player lost, and the last known spot searched out — roam. */
	LeadGone
};

USTRUCT()
struct FGunmanConditionInstanceData
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = Context)
	TObjectPtr<AAIController> AIController = nullptr;

	UPROPERTY(EditAnywhere, Category = Parameter)
	EGunmanCheck Check = EGunmanCheck::IsAlerted;

	UPROPERTY(EditAnywhere, Category = Parameter, meta = (ClampMin = "0.0"))
	float LostForSeconds = 3.0f;

	UPROPERTY(EditAnywhere, Category = Parameter)
	bool bInvert = false;
};

/** What the gunman knows: alerted, or has lost the player. */
USTRUCT(meta = (DisplayName = "Gunman Check", Category = "AI|Gunman"))
struct FGunmanCondition : public FStateTreeAIConditionBase
{
	GENERATED_BODY()

	using FInstanceDataType = FGunmanConditionInstanceData;
	virtual const UStruct* GetInstanceDataType() const override { return FInstanceDataType::StaticStruct(); }

	virtual bool TestCondition(FStateTreeExecutionContext& Context) const override;
};
