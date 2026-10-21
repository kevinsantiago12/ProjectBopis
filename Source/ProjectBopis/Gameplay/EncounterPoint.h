#pragma once

#include "CoreMinimal.h"
#include "Engine/TargetPoint.h"
#include "EncounterPoint.generated.h"

class UTextRenderComponent;

UENUM(BlueprintType)
enum class EEncounterPointRole : uint8
{
	/** Where a trigger's spawned enemy appears. */
	Spawn,
	/** Where an enemy runs to when its trigger fires. */
	Ambush,
	/** A stop on a patroller's route. */
	Patrol
};

/** A marker for encounter triggers: a spawn, ambush or patrol point, labelled in the editor
    (role and name) so it's easy to find. The label never shows in game. */
UCLASS()
class PROJECTBOPIS_API AEncounterPoint : public ATargetPoint
{
	GENERATED_BODY()

public:
	AEncounterPoint();

	virtual void OnConstruction(const FTransform& Transform) override;

protected:
	UPROPERTY(EditAnywhere, Category = "Encounter")
	EEncounterPointRole PointRole = EEncounterPointRole::Spawn;

	/** Editor-only text: role and name. */
	UPROPERTY(VisibleAnywhere, Category = "Encounter")
	TObjectPtr<UTextRenderComponent> Label;
};
