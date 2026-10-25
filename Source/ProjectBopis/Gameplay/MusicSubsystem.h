// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MusicSubsystem.generated.h"

class UAudioComponent;
class USoundBase;

/**
 *  The background music: one track at a time, changed with a crossfade. Slow motion leaves it
 *  alone: fades run in real seconds and the music is out of the Focus's pitch drop. One per
 *  level, made by the engine.
 */
UCLASS()
class PROJECTBOPIS_API UMusicSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** Crossfades to Track over FadeTime seconds (0: a hard cut). Already playing it: carries on.
	    None: fades the music out. */
	UFUNCTION(BlueprintCallable, Category = "Music")
	void PlayMusic(USoundBase* Track, float FadeTime = 2.0f, float Volume = 1.0f);

	/** Fades the music out over FadeTime seconds. */
	UFUNCTION(BlueprintCallable, Category = "Music")
	void StopMusic(float FadeTime = 2.0f) { PlayMusic(nullptr, FadeTime); }

	/** What's playing now (None in silence). */
	UFUNCTION(BlueprintPure, Category = "Music")
	USoundBase* GetCurrentTrack() const;

private:
	/** The track playing now. */
	UPROPERTY()
	TObjectPtr<UAudioComponent> Current;

	/** Old tracks still fading out; each destroys itself once silent. */
	UPROPERTY()
	TArray<TObjectPtr<UAudioComponent>> FadingOut;
};
