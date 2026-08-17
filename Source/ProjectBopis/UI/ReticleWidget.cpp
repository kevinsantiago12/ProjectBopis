// Fill out your copyright notice in the Description page of Project Settings.


#include "UI/ReticleWidget.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"

float UReticleWidget::GetCurrentBloom() const
{
	if (AProjectBopisCharacter* Character = Cast<AProjectBopisCharacter>(GetOwningPlayerPawn()))
	{
		if (UWeaponHolderComponent* Holder = Character->GetWeaponHolder())
		{
			if (AWeaponBase* Weapon = Holder->GetEquippedWeapon())
			{
				return Weapon->GetCurrentBloom();
			}
		}
	}

	return 0.0f;
}


