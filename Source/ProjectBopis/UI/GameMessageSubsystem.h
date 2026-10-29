// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/LocalPlayerSubsystem.h"
#include "GameMessageSubsystem.generated.h"

enum class EAmmoType : uint8;

/** One line in the message feed. EndTime is FPlatformTime::Seconds(): real time, so slow motion
    doesn't stretch a message and a level load doesn't cut it short. */
struct FGameMessage
{
	/** The line's wording before any count is filled in. A new line with the same key replaces
	    this one instead of stacking. */
	FString Key;
	FText Text;
	/** Running total of a counted line; 0 for plain text. */
	int32 Amount = 0;
	double EndTime = 0.0;
};

/**
 *  The player's gameplay message feed ("Picked up 24 rounds", "Quick saved"): the newest few
 *  lines, each up for a few seconds. Lives on the local player, so it outlasts a level load.
 *  UGameMessageWidget shows it.
 */
UCLASS()
class PROJECTBOPIS_API UGameMessageSubsystem : public ULocalPlayerSubsystem
{
	GENERATED_BODY()

public:
	/** Most lines held at once; a new one pushes the oldest out. */
	static constexpr int32 MaxMessages = 5;

	/** Adds a line to the first local player's feed for this many seconds. Empty: nothing. The
	    same text while it's still up isn't stacked: that line moves to the newest place, its time
	    started over. */
	UFUNCTION(BlueprintCallable, Category = "Game Messages", meta = (WorldContext = "WorldContextObject"))
	static void ShowGameMessage(const UObject* WorldContextObject, const FText& Message, float Seconds = 3.0f);

	/** A line that counts: Pattern with its {Amount} filled in. While a line from the same Pattern
	    is up, Amount adds to its total instead ("Picked up 24 .45 rounds", then "Picked up 48 …"),
	    and the line moves to the newest place, its time started over. */
	UFUNCTION(BlueprintCallable, Category = "Game Messages", meta = (WorldContext = "WorldContextObject"))
	static void ShowCountedGameMessage(const UObject* WorldContextObject, const FText& Pattern, int32 Amount, float Seconds = 3.0f);

	/** "Picked up 24 .45 rounds": Type's wording, counted (see ShowCountedGameMessage). Ammo boxes
	    and guns taken for their rounds both use it, so they share a line. */
	static void ShowAmmoMessage(const UObject* WorldContextObject, EAmmoType Type, int32 Amount);

	void AddMessage(const FText& Message, float Seconds);
	void AddCountedMessage(const FText& Pattern, int32 Amount, float Seconds);

	/** Oldest first. Can still hold lines past their EndTime, until the next one comes in. */
	const TArray<FGameMessage>& GetMessages() const { return Messages; }

private:
	/** The first local player's feed, or null. */
	static UGameMessageSubsystem* GetFeed(const UObject* WorldContextObject);

	/** Puts a line in the newest place, replacing any line with the same key. */
	void AddLine(const FString& Key, const FText& Text, int32 Amount, float Seconds);

	TArray<FGameMessage> Messages;
};
