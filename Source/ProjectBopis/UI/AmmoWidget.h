// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "AmmoWidget.generated.h"

class UImage;
class UTextBlock;
class UTexture2D;

/**
 * Ammunition readout for the equipped weapon.
 */
UCLASS()
class PROJECTBOPIS_API UAmmoWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	/** Rounds in the equipped weapon's magazine, or 0 when nothing is held. */
	UFUNCTION(BlueprintPure, Category = "Ammo")
	int32 GetAmmoInMagazine() const;

	/** Rounds in the equipped weapon's reserve, or 0 when nothing is held. */
	UFUNCTION(BlueprintPure, Category = "Ammo")
	int32 GetReserveAmmo() const;

	/** Whether the equipped weapon is mid-reload. */
	UFUNCTION(BlueprintPure, Category = "Ammo")
	bool IsReloading() const;

	/** Hand grenades carried (the Grenade ammo pool), or 0 with no holder. */
	UFUNCTION(BlueprintPure, Category = "Ammo")
	int32 GetGrenadeCount() const;

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** The equipped weapon's icon, in its own proportions; hidden with nothing held. With an
	    M_HUDIcon instance as its brush (the stroke) the icon goes into its "Texture" parameter. */
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UImage> WeaponIcon;

	/** A dual-wield weapon's second icon, behind WeaponIcon like a shadow; hidden otherwise.
	    Both sit in an Overlay, and their slot padding spreads the pair (DualIconSpread). */
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UImage> WeaponIconDual;

	/** Rounds in the magazine: "15". */
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> MagazineText;

	/** The reserve: "/ 90". */
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> ReserveText;

	/** Height the icons are laid out at, in Slate units; a Scale Box round them in the
	    Blueprint then fits them to the widget's box. */
	UPROPERTY(EditAnywhere, Category = "Ammo")
	float IconHeight = 62.0f;

	/** How far the dual-wield copy sits from the first icon, as a fraction of the icon's width
	    and height (+X right, +Y down), as on the weapon wheel. */
	UPROPERTY(EditAnywhere, Category = "Ammo")
	FVector2D DualIconSpread = FVector2D(0.5, 0.5);

private:
	/** Puts Icon on WeaponIcon (and on WeaponIconDual when bDual), or hides them for null. */
	void ShowIcons(UTexture2D* Icon, bool bDual);

	/** Sets one Image to Icon at IconHeight with the given Overlay padding; hides it for null. */
	void ShowIcon(UImage* Image, UTexture2D* Icon, const FMargin& SlotPadding) const;

	/** What ShowIcons last showed, so the icons are only touched when that changes. */
	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> ShownIcon;

	bool bShownDual = false;
};
