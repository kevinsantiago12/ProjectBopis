// Fill out your copyright notice in the Description page of Project Settings.


#include "UI/AmmoWidget.h"
#include "Weapons/WeaponBase.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Components/Image.h"
#include "Components/OverlaySlot.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
	/** Width over height. */
	float IconAspect(const UTexture2D* Icon)
	{
		return FMath::Max(1, Icon->GetSizeX()) / static_cast<float>(FMath::Max(1, Icon->GetSizeY()));
	}
}

int32 UAmmoWidget::GetAmmoInMagazine() const
{
	AWeaponBase* Weapon = GetEquippedWeapon();
	return Weapon ? Weapon->GetAmmoInMagazine() : 0;
}

int32 UAmmoWidget::GetReserveAmmo() const
{
	AWeaponBase* Weapon = GetEquippedWeapon();
	return Weapon ? Weapon->GetReserveAmmo() : 0;
}

bool UAmmoWidget::IsReloading() const
{
	AWeaponBase* Weapon = GetEquippedWeapon();
	return Weapon ? Weapon->IsReloading() : false;
}

int32 UAmmoWidget::GetGrenadeCount() const
{
	const AProjectBopisCharacter* Player = GetPlayerCharacter();
	const UWeaponHolderComponent* Holder = Player ? Player->GetWeaponHolder() : nullptr;
	return Holder ? Holder->GetReserveAmmo(EAmmoType::Grenade) : 0;
}

void UAmmoWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// Hidden until a tick finds a weapon (left alone in the designer, for the preview icon).
	if (!IsDesignTime())
	{
		ShowIcons(nullptr, false);
	}
}

void UAmmoWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	const AWeaponBase* Weapon = GetEquippedWeapon();
	UTexture2D* Icon = Weapon ? Weapon->GetIcon() : nullptr;
	const bool bDual = Icon && Weapon->IsDualWield();
	if (Icon != ShownIcon || bDual != bShownDual)
	{
		ShowIcons(Icon, bDual);
	}

	// Nothing held: blank rather than "0 / 0". Set only on a change: a new FText every frame
	// makes Slate lay the text out again every frame.
	const int32 Magazine = Weapon ? Weapon->GetAmmoInMagazine() : -1;
	if (MagazineText && Magazine != ShownMagazine)
	{
		MagazineText->SetText(Weapon ? FText::AsNumber(Magazine) : FText::GetEmpty());
		ShownMagazine = Magazine;
	}
	const int32 Reserve = Weapon ? Weapon->GetReserveAmmo() : -1;
	if (ReserveText && Reserve != ShownReserve)
	{
		ReserveText->SetText(Weapon
			? FText::Format(NSLOCTEXT("AmmoWidget", "Reserve", "/ {0}"), Reserve)
			: FText::GetEmpty());
		ShownReserve = Reserve;
	}
}

void UAmmoWidget::ShowIcons(UTexture2D* Icon, bool bDual)
{
	ShownIcon = Icon;
	bShownDual = bDual;

	// A dual pair: the first icon top-left, the copy DualIconSpread of an icon down and right,
	// so the Overlay (and the Scale Box fitting it) gets the pair's whole size.
	const FVector2D Offset = bDual
		? DualIconSpread * FVector2D(IconHeight * IconAspect(Icon), IconHeight)
		: FVector2D::ZeroVector;
	if (WeaponIcon)
	{
		ShowIcon(WeaponIcon, Icon, FMargin(0.0f, 0.0f, Offset.X, Offset.Y));
	}
	if (WeaponIconDual)
	{
		ShowIcon(WeaponIconDual, bDual ? Icon : nullptr, FMargin(Offset.X, Offset.Y, 0.0f, 0.0f));
	}
}

void UAmmoWidget::ShowIcon(UImage* Image, UTexture2D* Icon, const FMargin& SlotPadding) const
{
	if (Icon)
	{
		// An M_HUDIcon brush takes the icon as its "Texture" parameter; a plain brush takes it directly.
		UMaterialInstanceDynamic* Material = Image->GetDynamicMaterial();
		if (Material)
		{
			Material->SetTextureParameterValue(TEXT("Texture"), Icon);
		}
		FSlateBrush Brush = Image->GetBrush();
		if (!Material)
		{
			Brush.SetResourceObject(Icon);
		}
		Brush.ImageSize = FVector2D(IconHeight * IconAspect(Icon), IconHeight);
		Image->SetBrush(Brush);
	}
	if (UOverlaySlot* OverlaySlot = Cast<UOverlaySlot>(Image->Slot))
	{
		OverlaySlot->SetPadding(SlotPadding);
	}
	Image->SetVisibility(Icon ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
}
