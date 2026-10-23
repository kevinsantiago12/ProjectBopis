// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Gameplay/ShootdodgeComponent.h"
#include "RollComponent.generated.h"

class AProjectBopisCharacter;
class UAnimSequenceBase;
class UAnimMontage;

/** One roll direction's clips; one is picked at random (forward over either shoulder, say). */
USTRUCT(BlueprintType)
struct FRollAnims
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Roll")
	TArray<TObjectPtr<UAnimSequenceBase>> Clips;
};

/**
 *  The dodge roll: a quick ground roll in one of eight directions relative to the camera,
 *  carried by the clip's root motion. Evasive (enemies rarely hit mid-roll), free, and
 *  committed — no firing or reloading until it's done.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class PROJECTBOPIS_API URollComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	URollComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Rolls the way the movement input points, if allowed: on the ground, not mid-dive,
	    off cooldown, with a clip for that direction. */
	bool TryRoll();

	/** Drops a roll on the spot (death): no blend, rotation handed back. */
	void Cancel();

	UFUNCTION(BlueprintPure, Category = "Roll")
	bool IsRolling() const { return RollMontage != nullptr; }

protected:

	virtual void BeginPlay() override;

	/** Clips by direction, relative to the body (which faces the aim). Their root motion
	    carries the roll, so it covers the distance the animation does. */
	UPROPERTY(EditAnywhere, Category = "Roll")
	TMap<EShootdodgeDirection, FRollAnims> Animations;

	/** Full-body slot the roll plays in. */
	UPROPERTY(EditAnywhere, Category = "Roll")
	FName SlotName = TEXT("DeathSlot");

	UPROPERTY(EditAnywhere, Category = "Roll", meta = (ClampMin = "0.1"))
	float PlayRate = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Roll", meta = (ClampMin = "0.0"))
	float BlendInTime = 0.1f;

	UPROPERTY(EditAnywhere, Category = "Roll", meta = (ClampMin = "0.0"))
	float BlendOutTime = 0.2f;

	/** Seconds after a roll before the next can start. */
	UPROPERTY(EditAnywhere, Category = "Roll", meta = (ClampMin = "0.0"))
	float Cooldown = 0.25f;

	/** How far through the roll (0..1) movement input may cut it short and take over —
	    the rest is mostly getting back up. 1: always plays out. */
	UPROPERTY(EditAnywhere, Category = "Roll", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MoveOutAfter = 0.6f;

	/** Blend out when moving out early, in seconds. */
	UPROPERTY(EditAnywhere, Category = "Roll", meta = (ClampMin = "0.0"))
	float MoveOutBlendTime = 0.15f;

	/** Moving out early comes out at full run speed the way the input points, rather than
	    from a standstill. */
	UPROPERTY(EditAnywhere, Category = "Roll")
	bool bCarryMomentum = true;

	/** Holding the roll button: this far through the roll (0..1) it cuts into a kneel (the
	    character's post-roll crouch) instead of playing out. */
	UPROPERTY(EditAnywhere, Category = "Roll|Kneel", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float CrouchOutAfter = 0.5f;

	/** Blend out when cutting into the kneel, in seconds. */
	UPROPERTY(EditAnywhere, Category = "Roll|Kneel", meta = (ClampMin = "0.0"))
	float CrouchOutBlendTime = 0.15f;

	/** Partway into the roll, slow motion (a free Focus) for RollFocusDuration: no shooting
	    yet, but time to line up the shots for coming out of it. */
	UPROPERTY(EditAnywhere, Category = "Roll|Focus")
	bool bRollFocus = true;

	/** How far through the roll (0..1) the body hits the ground — the thud. */
	UPROPERTY(EditAnywhere, Category = "Roll", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float RollThudAt = 0.2f;

	/** How far through the roll (0..1) the slow motion starts. */
	UPROPERTY(EditAnywhere, Category = "Roll|Focus", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float RollFocusStartAt = 0.3f;

	/** Real seconds of slow motion. It runs its course even past the end of the roll. */
	UPROPERTY(EditAnywhere, Category = "Roll|Focus", meta = (ClampMin = "0.0"))
	float RollFocusDuration = 1.0f;

private:

	/** The eight-way direction the movement input points, relative to the camera. */
	EShootdodgeDirection PickDirection() const;

	/** The roll is over: rotation back to the movement stances, cooldown starts. */
	void EndRoll();

	UPROPERTY(Transient)
	TObjectPtr<AProjectBopisCharacter> Character;

	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> RollMontage;

	float CooldownLeft = 0.0f;

	/** This roll's slow motion has been tried (once per roll). */
	bool bRollFocusDone = false;

	/** This roll's thud has played. */
	bool bRollThudDone = false;

	/** The slow motion running is this roll's (a free Focus), with this much real time left. */
	bool bOwnsFocus = false;
	float RollFocusLeft = 0.0f;
};
