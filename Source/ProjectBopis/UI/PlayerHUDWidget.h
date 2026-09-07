// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "PlayerHUDWidget.generated.h"

/**
 * Container for the player's HUD elements. Currently just a type for the
 * character's HUDWidgetClass — the layout lives in WBP_PlayerHUD, and each
 * element sources its own state. HUD-wide behaviour (showing/hiding elements
 * on state changes) would live here when it's needed.
 */
UCLASS()
class PROJECTBOPIS_API UPlayerHUDWidget : public UUserWidget
{
	GENERATED_BODY()
};
