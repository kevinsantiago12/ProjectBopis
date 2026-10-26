// Copyright Epic Games, Inc. All Rights Reserved.

#include "Weapons/WeaponAnimInstance.h"
#include "Weapons/WeaponBase.h"

void UWeaponAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);

	const AWeaponBase* Weapon = Cast<AWeaponBase>(GetOwningActor());
	PumpSlideOffset = Weapon ? Weapon->GetPumpOffset() : FVector::ZeroVector;
}
