// Fill out your copyright notice in the Description page of Project Settings.


#include "UI/ReticleWidget.h"
#include "Weapons/WeaponBase.h"

float UReticleWidget::GetCurrentBloom() const
{
	AWeaponBase* Weapon = GetEquippedWeapon();
	return Weapon ? Weapon->GetCurrentBloom() : 0.0f;
}

FCrosshairSettings UReticleWidget::GetCrosshairSettings() const
{
	// Defaults rather than zeroes, so the reticle stays visible with nothing equipped.
	AWeaponBase* Weapon = GetEquippedWeapon();
	return Weapon ? Weapon->GetCrosshairSettings() : FCrosshairSettings();
}
