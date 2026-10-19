// Fill out your copyright notice in the Description page of Project Settings.


#include "UI/AmmoWidget.h"
#include "Weapons/WeaponBase.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"

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
