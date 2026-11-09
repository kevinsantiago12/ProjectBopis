// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SwingDoor.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class USoundBase;

/**
 *  A door that swings both ways, as in Max Payne: whoever walks into it (the player, an enemy,
 *  anyone with a pawn) pushes it open away from them, harder the faster they come, and a spring
 *  swings it back through shut once they're gone. The leaf never blocks a pawn or the camera and
 *  doesn't cut the navmesh; it does stop shots.
 *  Origin: the doorway's centre on the floor, local X along the wall (the generator's doors.json).
 */
UCLASS()
class PROJECTBOPIS_API ASwingDoor : public AActor
{
	GENERATED_BODY()

public:
	ASwingDoor();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnPushZoneEnter(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	/** Blueprint: it was pushed open toward its +Y (Direction 1) or -Y (-1). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Door")
	void OnPushedOpen(float Direction, AActor* Pusher);

	UPROPERTY(VisibleAnywhere, Category = "Door")
	TObjectPtr<USceneComponent> Root;

	/** Turns about Z at one side of the doorway; the leaf hangs off it. */
	UPROPERTY(VisibleAnywhere, Category = "Door")
	TObjectPtr<USceneComponent> Hinge;

	/** The door itself (its mesh is set in the Blueprint: Favela's SM_Door_01). */
	UPROPERTY(VisibleAnywhere, Category = "Door")
	TObjectPtr<UStaticMeshComponent> Leaf;

	/** Pawns in here push the door: the doorway, PushDepth to either side. */
	UPROPERTY(VisibleAnywhere, Category = "Door")
	TObjectPtr<UBoxComponent> PushZone;

	/** The leaf's size (cm); its mesh is scaled to it. The width is the jamb's clear opening. */
	UPROPERTY(EditAnywhere, Category = "Door", meta = (ClampMin = "40.0"))
	float LeafWidth = 94.0f;

	UPROPERTY(EditAnywhere, Category = "Door", meta = (ClampMin = "100.0"))
	float LeafHeight = 210.0f;

	/** Gap (cm) under the leaf, so it swings clear of the floor. */
	UPROPERTY(EditAnywhere, Category = "Door", meta = (ClampMin = "0.0"))
	float FloorGap = 1.0f;

	/** Hinged on the doorway's +X side instead of its -X side. */
	UPROPERTY(EditAnywhere, Category = "Door")
	bool bHingeOnRight = false;

	/** Quarter turns (0-3) of the leaf's mesh about Z before it's fitted: 2 puts a handle modelled on
	    the mesh's -X edge on the free edge; 1 or 3 for a mesh modelled along its Y. */
	UPROPERTY(EditAnywhere, Category = "Door", meta = (ClampMin = "0", ClampMax = "3"))
	int32 LeafQuarterTurns = 0;

	/** How far (cm) to each side of the doorway a pawn starts pushing. */
	UPROPERTY(EditAnywhere, Category = "Door", meta = (ClampMin = "20.0"))
	float PushDepth = 90.0f;

	/** How far it swings open (degrees); a stop 5 degrees past it. */
	UPROPERTY(EditAnywhere, Category = "Door|Swing", meta = (ClampMin = "10.0", ClampMax = "170.0"))
	float OpenAngle = 95.0f;

	/** The spring: how hard it pulls toward open or shut, and how fast the swing dies down. Under
	    2 x sqrt(Stiffness) it swings past shut and back, as a two-way door does. */
	UPROPERTY(EditAnywhere, Category = "Door|Swing", meta = (ClampMin = "1.0"))
	float Stiffness = 60.0f;

	UPROPERTY(EditAnywhere, Category = "Door|Swing", meta = (ClampMin = "0.0"))
	float Damping = 6.0f;

	/** A push's kick: degrees per second of swing for each cm per second the pawn moves at the door. */
	UPROPERTY(EditAnywhere, Category = "Door|Swing", meta = (ClampMin = "0.0"))
	float PushKick = 0.4f;

	/** Seconds after the last pawn leaves before it swings shut. */
	UPROPERTY(EditAnywhere, Category = "Door|Swing", meta = (ClampMin = "0.0"))
	float CloseDelay = 0.5f;

	UPROPERTY(EditAnywhere, Category = "Door|Sound")
	TObjectPtr<USoundBase> OpenSound;

	/** Plays as it swings back through shut. */
	UPROPERTY(EditAnywhere, Category = "Door|Sound")
	TObjectPtr<USoundBase> CloseSound;

private:
	void ApplySwing();

	float Swing = 0.0f;          // degrees; + is the leaf toward the door's +Y
	float SwingSpeed = 0.0f;     // degrees per second
	float Target = 0.0f;
	float OpenDir = 0.0f;        // +1 or -1 while open, 0 while shut
	float EmptyTime = 0.0f;
	bool bCloseSoundDue = false;
};
