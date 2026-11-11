#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MovieSceneObjectBindingID.h"
#include "Gameplay/Interactable.h"
#include "InspectPoint.generated.h"

class USphereComponent;
class UArrowComponent;
class ULevelSequence;
class ULevelSequencePlayer;
class ALevelSequenceActor;

/**
 *  A story beat the player can inspect (lore: Inspects): a mini cutscene. The Cutscene plays its own
 *  double of the player (a BP_Player_Cutscene, its binding tagged PlayerTag) while the real one is
 *  hidden and out of play; Interact skips. After it the player is back where the double finished,
 *  and OnInspected fires.
 */
UCLASS()
class PROJECTBOPIS_API AInspectPoint : public AActor, public IInteractable
{
	GENERATED_BODY()

public:
	AInspectPoint();

	virtual void Tick(float DeltaSeconds) override;

	// IInteractable
	virtual FVector GetInteractLocation() const override { return GetActorLocation(); }
	virtual float GetInteractRange() const override;
	virtual bool CanInteract() const override { return !bDone; }
	virtual FText GetInteractPrompt() const override { return Prompt; }
	virtual void Interact(AProjectBopisCharacter* Player) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** Inspected: the cutscene is over (or skipped) and the player has control again. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Inspect")
	void OnInspected(AProjectBopisCharacter* Player);

	/** Centred on what's looked at; its radius is how near the player has to be. Editor only. */
	UPROPERTY(VisibleAnywhere, Category = "Inspect")
	TObjectPtr<USphereComponent> Area;

	/** Where the double starts, facing the arrow's way, for authoring; and where the player comes
	    back if the cutscene has no double. */
	UPROPERTY(VisibleAnywhere, Category = "Inspect")
	TObjectPtr<UArrowComponent> Mark;

	UPROPERTY(EditAnywhere, Category = "Inspect")
	FText Prompt = NSLOCTEXT("Inspect", "Prompt", "Inspect");

	/** The mini cutscene. None: no cutscene, the press just counts. */
	UPROPERTY(EditAnywhere, Category = "Inspect|Cutscene")
	TObjectPtr<ULevelSequence> Cutscene;

	/** The tag on the cutscene's double of the player. Where it finishes, the player comes back. */
	UPROPERTY(EditAnywhere, Category = "Inspect|Cutscene")
	FName PlayerTag = TEXT("Player");

	/** The player's cutscene double. Built when the level starts and kept hidden, then put in the
	    cutscene in place of its own (the binding tagged PlayerTag), so it's there on the first frame:
	    a double the sequence spawns itself shows up late (building it takes a moment, and a new mesh
	    isn't drawn until its shaders are ready). None: the sequence spawns its own. A soft reference,
	    loaded at BeginPlay: a hard one loads the Character Customizer when the game module starts,
	    before the IK Rig plugin, which breaks its AnimBP and fails the cook. */
	UPROPERTY(EditAnywhere, Category = "Inspect|Cutscene")
	TSoftClassPtr<AActor> DoubleClass;

private:
	/** Takes the player out of play and starts the cutscene. False if there's none to play. */
	bool StartCutscene(AProjectBopisCharacter* Player);

	/** Finished, stopped or skipped: the player back where the double finished, then OnInspected. */
	UFUNCTION()
	void EndCutscene();

	/** Interact during the cutscene. */
	void Skip();

	/** Notes where the double stands now, if the cutscene has one and it's spawned. */
	void RecordDouble();

	/** The player and his gun, hidden or shown. */
	void SetPlayerHidden(AProjectBopisCharacter* Player, bool bHide) const;

	/** Builds the double on the Mark (on the floor under it), hidden and still, for the cutscene. */
	void PrepareDouble();

	/** The double shown and animating, or hidden and still. */
	void SetDoubleActive(bool bActive) const;

	/** The Character Customizer shows its character once its clothes and hair have loaded
	    (UnhideCharacter): while the double waits, that puts it back out of sight. */
	void WatchDouble(float DeltaSeconds);

	UPROPERTY()
	TObjectPtr<AActor> Double;

	/** Seconds spent watching the waiting double; it stops after 30. */
	float DoubleWatchTime = 0.0f;

	TWeakObjectPtr<AProjectBopisCharacter> InspectingPlayer;

	UPROPERTY()
	TObjectPtr<ULevelSequencePlayer> SequencePlayer;

	UPROPERTY()
	TObjectPtr<ALevelSequenceActor> SequenceActor;

	FMovieSceneObjectBindingID DoubleBinding;
	FTransform DoubleEnd;
	bool bHasDouble = false;
	bool bHasDoubleEnd = false;
	bool bDamageableBefore = true;

	/** The player was taken out of play, so the end gives him back. */
	bool bTookPlayer = false;

	bool bDone = false;
	bool bEnded = false;
};
