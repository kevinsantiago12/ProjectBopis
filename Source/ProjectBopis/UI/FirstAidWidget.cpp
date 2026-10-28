// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/FirstAidWidget.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"

int32 UFirstAidWidget::GetFirstAidCount() const
{
	const AProjectBopisCharacter* Character = GetPlayerCharacter();
	const UWeaponHolderComponent* Holder = Character ? Character->GetWeaponHolder() : nullptr;
	return Holder ? Holder->GetReserveAmmo(EAmmoType::FirstAid) : 0;
}
