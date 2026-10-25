// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MusicTrigger.generated.h"

class UBoxComponent;
class UTextRenderComponent;
class UBillboardComponent;
class USoundBase;

/**
 *  Changes the background music when the player walks into the box: a crossfade to Track, or
 *  out to silence with none. One at the level start (Play At Start) for its opening music, more
 *  where the mood turns.
 */
UCLASS()
class PROJECTBOPIS_API AMusicTrigger : public AActor
{
	GENERATED_BODY()

public:
	AMusicTrigger();

	virtual void OnConstruction(const FTransform& Transform) override;

	/** Changes the music as if the player had walked in (from a level script, say). */
	UFUNCTION(BlueprintCallable, Category = "Music")
	void Fire();

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnVolumeOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, Category = "Music")
	TObjectPtr<UBoxComponent> Volume;

	/** Editor-only text: the track it changes to. */
	UPROPERTY(VisibleAnywhere, Category = "Music")
	TObjectPtr<UTextRenderComponent> Label;

#if WITH_EDITORONLY_DATA
	/** Editor-only icon at the centre: something to click instead of the box's edges. */
	UPROPERTY()
	TObjectPtr<UBillboardComponent> Icon;
#endif

	/** What plays from here (tick Looping on the wave for music that carries on). None: the
	    music fades out. */
	UPROPERTY(EditAnywhere, Category = "Music")
	TObjectPtr<USoundBase> Track;

	/** The crossfade, in real seconds: slow motion doesn't stretch it. 0: a hard cut. */
	UPROPERTY(EditAnywhere, Category = "Music", meta = (ClampMin = "0.0"))
	float FadeTime = 2.0f;

	/** This track's loudness (all the music's together: the SC_Music sound class). */
	UPROPERTY(EditAnywhere, Category = "Music", meta = (ClampMin = "0.0"))
	float TrackVolume = 1.0f;

	/** Goes off once. Off: every time the player walks in (its track carries on if already playing). */
	UPROPERTY(EditAnywhere, Category = "Music")
	bool bTriggerOnce = true;

	/** Goes off as the level starts instead of when the player walks in: the level's opening music. */
	UPROPERTY(EditAnywhere, Category = "Music")
	bool bPlayAtStart = false;

private:
	bool bTriggered = false;
};
