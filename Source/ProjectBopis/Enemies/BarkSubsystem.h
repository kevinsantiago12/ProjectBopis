#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Enemies/BarkSet.h"
#include "BarkSubsystem.generated.h"

class UAudioComponent;
class USoundBase;

/**
 *  Every enemy's barks go through here, so a room full of them doesn't talk over itself: only the
 *  player's earshot, a level-wide cooldown per type, one line per speaker, a cap on how many at
 *  once, and never the same line twice running. One per level, made by the engine.
 */
UCLASS()
class PROJECTBOPIS_API UBarkSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** Says Type's line in Voice from Speaker's head, if it gets through. Returns whether it played. */
	bool TryBark(AActor* Speaker, const UBarkVoice* Voice, EBarkType Type);

	/** Plays a voice from Speaker's head (its root without one) in 3D: full within FullRange,
	    gone Falloff further out. */
	static UAudioComponent* PlayVoice(AActor* Speaker, USoundBase* Sound, float FullRange, float Falloff);

	/** The language barks are picked in ("en", "tl"...). A voice without it falls back to English. */
	UFUNCTION(BlueprintCallable, Category = "Bark")
	void SetLanguage(FName InLanguage) { Language = InLanguage; }

	UFUNCTION(BlueprintPure, Category = "Bark")
	FName GetLanguage() const { return Language; }

	/** At most this many barks at once (death grunts always get through). */
	int32 MaxConcurrent = 2;

	/** Barks further than this from the player (cm) aren't said at all. */
	float HearingRange = 3000.0f;

	/** Full volume within this (cm), fading out over VoiceFalloff further. */
	float VoiceFullRange = 400.0f;
	float VoiceFalloff = 2500.0f;

private:
	FName Language = TEXT("en");

	/** World time each type may next be said. */
	TMap<EBarkType, double> NextAllowed;

	/** Each type's last line, so it isn't said twice running. */
	TMap<EBarkType, TWeakObjectPtr<USoundBase>> LastPlayed;

	/** What's being said now. */
	UPROPERTY()
	TArray<TObjectPtr<UAudioComponent>> Playing;
};
