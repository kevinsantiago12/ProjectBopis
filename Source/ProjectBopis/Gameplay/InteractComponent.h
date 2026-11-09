#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "InteractComponent.generated.h"

class IInteractable;
class AProjectBopisCharacter;

/**
 *  The player's Interact button. Ten times a second it picks the registered interactable the
 *  player is near and facing, with nothing in between; the HUD prompt shows it and the button
 *  uses it. Calm moments only: alive, on the ground, no kill cam, out of combat.
 */
UCLASS(ClassGroup = (Gameplay), meta = (BlueprintSpawnableComponent))
class PROJECTBOPIS_API UInteractComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UInteractComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** The button: uses the one in front of the player, if any. */
	void Interact();

	/** The prompt's word for the picked one, or empty when there's none. */
	FText GetPromptText() const;

	/** Where the player's head turns: the nearest usable interactable within LookRange and LookAngle
	    of where he faces, in sight. Wider than the prompt's test, so he notices a thing before he's
	    at it. False if there's none. */
	bool GetLookTarget(FVector& OutLocation) const;

protected:
	/** Facing it: the camera looks within this many degrees of it. */
	UPROPERTY(EditAnywhere, Category = "Interact", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float MaxViewAngle = 35.0f;

	/** The glance: how near (cm) a thing has to be for him to look at it... */
	UPROPERTY(EditAnywhere, Category = "Interact|Look", meta = (ClampMin = "0.0"))
	float LookRange = 400.0f;

	/** ...and within this many degrees of where he faces. */
	UPROPERTY(EditAnywhere, Category = "Interact|Look", meta = (ClampMin = "0.0", ClampMax = "180.0"))
	float LookAngle = 90.0f;

private:
	/** The best one to use now (near, faced, in sight, usable), or null. */
	UObject* PickFocus() const;

	/** The one to glance at now (see GetLookTarget), or null. */
	UObject* PickLookTarget() const;

	/** Calm enough to notice or use anything: alive, on the ground, no kill cam, out of combat. */
	static bool IsCalm(const AProjectBopisCharacter& Player);

	/** Nothing between his eyes and Target. Hitting the thing itself, or right at the spot, counts as seen. */
	bool CanSee(const AProjectBopisCharacter& Player, const FVector& Target, const UObject* Thing) const;

	TWeakObjectPtr<UObject> Focused;
	TWeakObjectPtr<UObject> LookTarget;
};
