// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "WeaponAnimInstance.generated.h"

/**
 *  Base for a weapon mesh's post-process AnimBP (set on the mesh asset, so it runs on top of
 *  whatever the weapon plays): moves the pump slide back by its weapon's pump amount.
 */
UCLASS()
class PROJECTBOPIS_API UWeaponAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

protected:
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

	/** The slide's offset from rest in its parent bone's space, back along the barrel (-X).
	    The AnimGraph adds it to the slide bone (Transform (Modify) Bone, Parent Bone Space). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "Weapon")
	FVector PumpSlideOffset = FVector::ZeroVector;
};
