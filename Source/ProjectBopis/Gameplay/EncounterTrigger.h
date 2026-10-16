// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EncounterTrigger.generated.h"

class UBoxComponent;
class AEnemyBase;

/**
 *  A room's start line: when the player walks into the box, every linked enemy is alerted at
 *  once (each still takes its reaction beat). Place it at the doorway or just inside, then
 *  pick the room's enemies in Enemies.
 */
UCLASS()
class PROJECTBOPIS_API AEncounterTrigger : public AActor
{
	GENERATED_BODY()

public:
	AEncounterTrigger();

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnVolumeOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, Category = "Encounter")
	TObjectPtr<UBoxComponent> Volume;

	/** The enemies this sets off. */
	UPROPERTY(EditInstanceOnly, Category = "Encounter")
	TArray<TObjectPtr<AEnemyBase>> Enemies;

	/** Goes off once. Off: every time the player walks in (already-alerted enemies just stay alerted). */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bTriggerOnce = true;

private:
	bool bTriggered = false;
};
