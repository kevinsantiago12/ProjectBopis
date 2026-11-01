// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/GrenadeWidget.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"

int32 UGrenadeWidget::GetGrenadeCount() const
{
	const AProjectBopisCharacter* Character = GetPlayerCharacter();
	const UWeaponHolderComponent* Holder = Character ? Character->GetWeaponHolder() : nullptr;
	return Holder ? Holder->GetReserveAmmo(EAmmoType::Grenade) : 0;
}

void UGrenadeWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	const AProjectBopisCharacter* Character = GetPlayerCharacter();
	const bool bMelee = Character && Character->GetQuickAction() == EQuickAction::Melee;

	// Melee has nothing to count.
	if (Count)
	{
		Count->SetVisibility(bMelee ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}

	UTexture2D* Texture = bMelee ? MeleeIcon : GrenadeIcon;
	if (Icon && Texture && Icon->GetBrush().GetResourceObject() != Texture)
	{
		// Keep the Image's designed height; the width follows the new icon's proportions.
		FSlateBrush Brush = Icon->GetBrush();
		Brush.SetResourceObject(Texture);
		Brush.ImageSize.X = Brush.ImageSize.Y * Texture->GetSizeX() / FMath::Max(1, Texture->GetSizeY());
		Icon->SetBrush(Brush);
	}
}
