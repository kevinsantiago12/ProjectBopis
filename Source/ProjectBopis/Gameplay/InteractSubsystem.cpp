#include "Gameplay/InteractSubsystem.h"

void UInteractSubsystem::Register(UObject* Interactable)
{
	if (Interactable)
	{
		Interactables.AddUnique(Interactable);
	}
}

void UInteractSubsystem::Unregister(UObject* Interactable)
{
	Interactables.Remove(Interactable);
}
