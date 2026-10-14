// Copyright Epic Games, Inc. All Rights Reserved.

#include "Enemies/GunmanStateTreeNodes.h"
#include "Enemies/EnemyBase.h"
#include "AIController.h"
#include "Navigation/PathFollowingComponent.h"
#include "StateTreeExecutionContext.h"

EStateTreeRunStatus FGunmanMoveTask::EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	AAIController* AI = Data.AIController;
	AEnemyBase* Enemy = AI ? Cast<AEnemyBase>(AI->GetPawn()) : nullptr;
	if (!Enemy)
	{
		return EStateTreeRunStatus::Failed;
	}
	Enemy->ClearLineOfFireBlocked();

	FVector Destination;
	if (Data.Goal == EGunmanMoveGoal::EngageSpot)
	{
		if (!Enemy->ChooseNextSpot(Destination))
		{
			return EStateTreeRunStatus::Failed;
		}
	}
	else if (Data.Goal == EGunmanMoveGoal::Roam)
	{
		if (!Enemy->ChooseRoamSpot(Destination))
		{
			return EStateTreeRunStatus::Failed;
		}
	}
	else
	{
		Destination = Enemy->GetLastKnownPlayerLocation();
	}

	// Strafing keeps the focus on the player: it faces (and fires at) them on the way.
	// The last known position can be off the navmesh (mid-dive), so it's projected onto it.
	Data.Destination = Destination;
	const EPathFollowingRequestResult::Type Result = AI->MoveToLocation(Destination, Data.AcceptanceRadius, true, true, true, true);
	if (Result == EPathFollowingRequestResult::Failed)
	{
		return EStateTreeRunStatus::Failed;
	}

	// Searching keeps going on the spot (see Tick); anything else is done once there.
	const bool bKeepsSearching = Data.Goal == EGunmanMoveGoal::LastKnownPosition && Data.bFollowNewInfo;
	return (Result == EPathFollowingRequestResult::AlreadyAtGoal && !bKeepsSearching)
		? EStateTreeRunStatus::Succeeded
		: EStateTreeRunStatus::Running;
}

EStateTreeRunStatus FGunmanMoveTask::Tick(FStateTreeExecutionContext& Context, const float DeltaTime) const
{
	FInstanceDataType& Data = Context.GetInstanceData(*this);
	AAIController* AI = Data.AIController;
	if (!AI)
	{
		return EStateTreeRunStatus::Failed;
	}

	// Searching: a newer sighting or sound moves the goal — head there instead. It never
	// finishes; finding the player again is what ends a search (the tree's transition).
	if (Data.Goal == EGunmanMoveGoal::LastKnownPosition && Data.bFollowNewInfo)
	{
		const AEnemyBase* Enemy = Cast<AEnemyBase>(AI->GetPawn());
		if (Enemy && FVector::Dist2D(Enemy->GetLastKnownPlayerLocation(), Data.Destination) > 200.0f)
		{
			Data.Destination = Enemy->GetLastKnownPlayerLocation();
			AI->MoveToLocation(Data.Destination, Data.AcceptanceRadius, true, true, true, true);
		}
		return EStateTreeRunStatus::Running;
	}

	return AI->GetMoveStatus() == EPathFollowingStatus::Idle
		? EStateTreeRunStatus::Succeeded
		: EStateTreeRunStatus::Running;
}

void FGunmanMoveTask::ExitState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const
{
	// Left early (lost the player, say): don't keep walking to the old goal.
	const FInstanceDataType& Data = Context.GetInstanceData(*this);
	if (!Data.AIController)
	{
		return;
	}
	if (Data.AIController->GetMoveStatus() != EPathFollowingStatus::Idle)
	{
		Data.AIController->StopMovement();
	}
	if (AEnemyBase* Enemy = Cast<AEnemyBase>(Data.AIController->GetPawn()))
	{
		Enemy->EndPush();
	}
}

bool FGunmanCondition::TestCondition(FStateTreeExecutionContext& Context) const
{
	const FInstanceDataType& Data = Context.GetInstanceData(*this);
	const AEnemyBase* Enemy = Data.AIController ? Cast<AEnemyBase>(Data.AIController->GetPawn()) : nullptr;

	bool bResult = false;
	if (Enemy)
	{
		switch (Data.Check)
		{
		case EGunmanCheck::IsAlerted:
			bResult = Enemy->IsAlerted();
			break;
		case EGunmanCheck::HasLostPlayer:
			bResult = Enemy->IsAlerted() && Enemy->GetTimeSinceSeenPlayer() >= Data.LostForSeconds;
			break;
		case EGunmanCheck::LineOfFireBlocked:
			bResult = Enemy->IsLineOfFireBlocked();
			break;
		case EGunmanCheck::LeadGone:
			bResult = Enemy->IsLeadGone();
			break;
		}
	}
	return bResult != Data.bInvert;
}
