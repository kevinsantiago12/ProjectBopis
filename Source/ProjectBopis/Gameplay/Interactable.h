#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "Interactable.generated.h"

class AProjectBopisCharacter;

UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class UInteractable : public UInterface
{
	GENERATED_BODY()
};

/**
 *  Something the player can press Interact at: an inspect now, a civilian later. It registers
 *  itself with UInteractSubsystem; the player's UInteractComponent picks the one in front of
 *  them and the HUD shows its prompt.
 */
class PROJECTBOPIS_API IInteractable
{
	GENERATED_BODY()

public:
	/** The point the player has to be near and facing, and that the line-of-sight test aims at. */
	virtual FVector GetInteractLocation() const = 0;

	/** How near (cm) the player has to be to GetInteractLocation. */
	virtual float GetInteractRange() const = 0;

	/** Usable now: not done already. (The player's side, such as being out of combat, is the
	    component's.) */
	virtual bool CanInteract() const = 0;

	/** The prompt's word: "Inspect", later "Talk". */
	virtual FText GetInteractPrompt() const = 0;

	/** The button was pressed with this one picked. */
	virtual void Interact(AProjectBopisCharacter* Player) = 0;
};
