// Fill out your copyright notice in the Description page of Project Settings.


#include "UI/PlayerHUDElementWidget.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"

AProjectBopisCharacter* UPlayerHUDElementWidget::GetPlayerCharacter() const
{
	return Cast<AProjectBopisCharacter>(GetOwningPlayerPawn());
}

AWeaponBase* UPlayerHUDElementWidget::GetEquippedWeapon() const
{
	if (AProjectBopisCharacter* Character = GetPlayerCharacter())
	{
		if (UWeaponHolderComponent* Holder = Character->GetWeaponHolder())
		{
			return Holder->GetEquippedWeapon();
		}
	}

	return nullptr;
}
