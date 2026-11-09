#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "InteractSubsystem.generated.h"

/** The level's interactables, so the player picks from a short list instead of searching the world. */
UCLASS()
class PROJECTBOPIS_API UInteractSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	void Register(UObject* Interactable);
	void Unregister(UObject* Interactable);

	const TArray<TWeakObjectPtr<UObject>>& GetInteractables() const { return Interactables; }

private:
	TArray<TWeakObjectPtr<UObject>> Interactables;
};
