// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/DamageType.h"
#include "MeleeDamageType.generated.h"

/** A blow from a melee strike. Characters take it at face value wherever it lands (no bone
    multipliers), and it always staggers them. */
UCLASS()
class PROJECTBOPIS_API UMeleeDamageType : public UDamageType
{
	GENERATED_BODY()
};
