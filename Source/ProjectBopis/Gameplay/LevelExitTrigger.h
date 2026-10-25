// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LevelExitTrigger.generated.h"

class UBoxComponent;
class UTextRenderComponent;
class UBillboardComponent;
class UUserWidget;
class UWorld;

/**
 *  The end of a level: when the player walks into the box, the level's over. They can't be hurt
 *  or act any more, slow motion ends, the HUD goes and the picture fades to black (the music
 *  with it), then NextLevel loads, or this one again. All in real seconds.
 */
UCLASS()
class PROJECTBOPIS_API ALevelExitTrigger : public AActor
{
	GENERATED_BODY()

public:
	ALevelExitTrigger();

	virtual void OnConstruction(const FTransform& Transform) override;

	/** Counts down to the load once the player's out. */
	virtual void Tick(float DeltaSeconds) override;

	/** Ends the level as if the player had walked in (from a level script, say). */
	UFUNCTION(BlueprintCallable, Category = "Exit")
	void Fire();

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnVolumeOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, Category = "Exit")
	TObjectPtr<UBoxComponent> Volume;

	/** Editor-only text: where it goes. */
	UPROPERTY(VisibleAnywhere, Category = "Exit")
	TObjectPtr<UTextRenderComponent> Label;

#if WITH_EDITORONLY_DATA
	/** Editor-only icon at the centre: something to click instead of the box's edges. */
	UPROPERTY()
	TObjectPtr<UBillboardComponent> Icon;
#endif

	/** The level it loads. None: this one again, from the top. */
	UPROPERTY(EditAnywhere, Category = "Exit")
	TSoftObjectPtr<UWorld> NextLevel;

	/** The fade to black, in real seconds. */
	UPROPERTY(EditAnywhere, Category = "Exit", meta = (ClampMin = "0.0"))
	float FadeTime = 1.5f;

	/** Real seconds from walking in to the load (never before the fade's done). */
	UPROPERTY(EditAnywhere, Category = "Exit", meta = (ClampMin = "0.0"))
	float LoadDelay = 3.0f;

	/** Shown over the black: a "level complete" card, designed in UMG. None: just the fade. */
	UPROPERTY(EditAnywhere, Category = "Exit")
	TSubclassOf<UUserWidget> CompleteWidgetClass;

	/** The music fades out with the picture. Off: it plays on until the load. */
	UPROPERTY(EditAnywhere, Category = "Exit")
	bool bFadeOutMusic = true;

private:
	bool bExited = false;

	/** Real seconds since the player walked in. */
	float TimeSinceExit = 0.0f;
};
