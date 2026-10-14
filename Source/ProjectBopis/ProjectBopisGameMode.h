// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "ProjectBopisGameMode.generated.h"

/**
 *  Simple GameMode for the game
 */
UCLASS(abstract)
class AProjectBopisGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AProjectBopisGameMode();

	/** Records a fresh corpse; past MaxCorpses, the oldest is removed. */
	void RegisterCorpse(AActor* Corpse);

	/** Asks to be one of the few enemies allowed to really try to hit the player. True if
	    the requester holds a token (already, or granted now). Nearer enemies take
	    precedence: with every token held, one clearly nearer than the farthest holder
	    takes that holder's token. Distance: requester to the player, in cm. */
	bool RequestAttackToken(AActor* Requester, float Distance);

	/** Hands a token back early (lost sight, died). bCooldown: wait AttackTokenCooldown
	    before taking another, as when a hold runs out. */
	void ReleaseAttackToken(AActor* Holder, bool bCooldown = false);

protected:
	/** How many enemies at once may try to hit the player; the rest only fire near misses. */
	UPROPERTY(EditAnywhere, Category = "Combat|Attack Tokens", meta = (ClampMin = "0"))
	int32 MaxAttackTokens = 2;

	/** Seconds an enemy keeps its token before handing it on. */
	UPROPERTY(EditAnywhere, Category = "Combat|Attack Tokens", meta = (ClampMin = "0.1"))
	float AttackTokenHoldTime = 3.0f;

	/** Seconds after a token runs out before the same enemy can take another. */
	UPROPERTY(EditAnywhere, Category = "Combat|Attack Tokens", meta = (ClampMin = "0.0"))
	float AttackTokenCooldown = 1.5f;

	/** How much nearer (cm) than the farthest holder an enemy must be to take its token —
	    so two at much the same distance don't trade it back and forth every frame. */
	UPROPERTY(EditAnywhere, Category = "Combat|Attack Tokens", meta = (ClampMin = "0.0"))
	float AttackTokenStealMargin = 300.0f;

	/** Most bodies left lying around at once. Older ones are removed as new ones fall. */
	UPROPERTY(EditAnywhere, Category = "Corpses", meta = (ClampMin = "0"))
	int32 MaxCorpses = 5;

	/** While over MaxCorpses, how often (seconds) to look for an off-camera body to remove. */
	UPROPERTY(EditAnywhere, Category = "Corpses", meta = (ClampMin = "0.05"))
	float CorpseCheckInterval = 0.5f;

	/** Removes the oldest off-camera corpses until back within MaxCorpses. Bodies on screen
	    are never removed; if they're all in view, it tries again every CorpseCheckInterval. */
	void TrimCorpses();

private:
	/** Oldest first. Weak, so a corpse destroyed some other way simply drops out. */
	TArray<TWeakObjectPtr<AActor>> Corpses;

	FTimerHandle CorpseCheckTimer;

	/** Who holds a token, since when (world seconds), and how far from the player they
	    were when they last asked. */
	struct FAttackToken
	{
		TWeakObjectPtr<AActor> Holder;
		float GrantedAt = 0.0f;
		float Distance = 0.0f;
	};
	TArray<FAttackToken> AttackTokens;

	/** World time before which each enemy can't take a token again. */
	TMap<TWeakObjectPtr<AActor>, float> AttackTokenCooldowns;
};



