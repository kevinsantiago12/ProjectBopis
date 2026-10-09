// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "BopisCharacterBase.h"
#include "EnemyBase.generated.h"

/**
 *  An enemy: the shared humanoid (weapon, montages, AnimBP) driven by an AI controller
 *  instead of input. Behaviour, movement and damage get layered on in later steps.
 */
UCLASS(abstract)
class PROJECTBOPIS_API AEnemyBase : public ABopisCharacterBase
{
	GENERATED_BODY()

public:

	AEnemyBase();

	virtual void Tick(float DeltaSeconds) override;

protected:

	virtual void Die(AController* Killer, const FVector& ShotDirection) override;

	/** Starts with the weapon up. For checking the raised pose before any AI drives it. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Debug")
	bool bStartRaised = false;

	/** Walked in order, looping. Any actors will do (Target Points are the usual pick).
	    Empty: stands still. Test behaviour until the StateTree takes over. */
	UPROPERTY(EditInstanceOnly, Category = "Enemy|Test Behaviour")
	TArray<TObjectPtr<AActor>> PatrolPoints;

	/** Seconds to wait at each patrol point before moving on. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Test Behaviour", meta = (ClampMin = "0.0"))
	float PatrolWaitTime = 1.0f;

	/** Keeps the player in its sights: weapon up, facing and aiming at them, strafing
	    while it patrols. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Test Behaviour")
	bool bAimAtPlayer = false;

	/** Max walk speed with the weapon lowered. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Movement", meta = (ClampMin = "0.0"))
	float LoweredSpeed = 300.0f;

	/** Max walk speed with the weapon raised. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Movement", meta = (ClampMin = "0.0"))
	float RaisedSpeed = 250.0f;

	/** How fast the body turns, in degrees per second, toward travel or toward the aim. */
	UPROPERTY(EditAnywhere, Category = "Enemy|Movement", meta = (ClampMin = "0.0"))
	float TurnRate = 360.0f;

private:

	/** Focuses the player and raises the weapon when bAimAtPlayer, otherwise lets go. */
	void UpdateAim();

	/** Raised: turn toward the aim and strafe. Lowered: turn toward travel. */
	void UpdateMovementMode();

	/** Walks the patrol points: waits at each, then moves to the next. */
	void UpdatePatrol(float DeltaSeconds);

	int32 PatrolIndex = 0;
	float PatrolWaitRemaining = 0.0f;
};
