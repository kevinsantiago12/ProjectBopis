#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "BarkSet.generated.h"

class USoundBase;

/** The moments an enemy calls out. */
UENUM(BlueprintType)
enum class EBarkType : uint8
{
	/** First sight of the player. */
	Spotted,
	/** Searching, after losing the player. */
	LostSight,
	/** Starting a reload. */
	Reloading,
	/** Hit and still standing. */
	Hurt,
	/** Saw an ally die. */
	AllyDown,
	/** A grenade landed close. */
	Grenade,
	/** Killed. */
	Death
};

/** One type's lines, and how often they come. */
USTRUCT(BlueprintType)
struct FBarkLines
{
	GENERATED_BODY()

	/** Picked at random, never the same one twice running. */
	UPROPERTY(EditAnywhere, Category = "Bark")
	TArray<TObjectPtr<USoundBase>> Sounds;

	/** Chance (0-1) it's said when its moment comes. */
	UPROPERTY(EditAnywhere, Category = "Bark", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Chance = 1.0f;

	/** Seconds before anyone in the level says this type again: one "there he is", not five. */
	UPROPERTY(EditAnywhere, Category = "Bark", meta = (ClampMin = "0.0"))
	float Cooldown = 3.0f;
};

/** One voice's barks in one language. */
UCLASS(BlueprintType)
class PROJECTBOPIS_API UBarkSet : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, Category = "Bark")
	TMap<EBarkType, FBarkLines> Lines;
};

/** One voice (a thug, a boss) in every language it has. An enemy points at this. */
UCLASS(BlueprintType)
class PROJECTBOPIS_API UBarkVoice : public UDataAsset
{
	GENERATED_BODY()

public:
	/** By language code: "en", "tl"... */
	UPROPERTY(EditAnywhere, Category = "Bark")
	TMap<FName, TObjectPtr<UBarkSet>> Languages;

	/** The set in this language, else English, else none. */
	const UBarkSet* GetSet(FName Language) const
	{
		if (const TObjectPtr<UBarkSet>* Found = Languages.Find(Language))
		{
			return *Found;
		}
		const TObjectPtr<UBarkSet>* English = Languages.Find(TEXT("en"));
		return English ? English->Get() : nullptr;
	}
};
