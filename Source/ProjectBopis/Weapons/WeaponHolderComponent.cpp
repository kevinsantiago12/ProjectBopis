// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "ProjectBopisCharacter.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Camera/CameraComponent.h"

// Sets default values for this component's properties
UWeaponHolderComponent::UWeaponHolderComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;

	// ...
}


// Called when the game starts
void UWeaponHolderComponent::BeginPlay()
{
	Super::BeginPlay();

	// ...
	
}


// Called every frame
void UWeaponHolderComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

bool UWeaponHolderComponent::AddWeapon(AWeaponBase* NewWeapon)
{
	if (!NewWeapon || CarriedWeapons.Num() >= MaxCarriedWeapons)
	{
		return false;
	}

	CarriedWeapons.Add(NewWeapon);

	if (!EquippedWeapon)
	{
		EquipWeapon(NewWeapon);
	}

	return true;
}

void UWeaponHolderComponent::EquipWeapon(AWeaponBase* WeaponToEquip)
{
	if (!WeaponToEquip || !CarriedWeapons.Contains(WeaponToEquip))
	{
		return;
	}

	if (EquippedWeapon)
	{
		EquippedWeapon->SetActorHiddenInGame(true);
		EquippedWeapon->DetachFromActor(FDetachmentTransformRules::KeepRelativeTransform);
	}

	EquippedWeapon = WeaponToEquip;

	if (AProjectBopisCharacter* OwningCharacter = Cast<AProjectBopisCharacter>(GetOwner()))
	{
		if (USkeletalMeshComponent* ArmsMesh = OwningCharacter->GetFirstPersonMesh())
		{
			EquippedWeapon->AttachToComponent(ArmsMesh,
				FAttachmentTransformRules::SnapToTargetNotIncludingScale, WeaponAttachSocketName);

			if (UStaticMeshComponent* MeshComp = EquippedWeapon->GetWeaponMesh())
			{
				MeshComp->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;
			}
		}
	}

	EquippedWeapon->SetActorHiddenInGame(false);
}

void UWeaponHolderComponent::FireEquippedWeapon()
{
	if (!EquippedWeapon)
	{
		return;
	}

	if (AProjectBopisCharacter* OwningCharacter = Cast<AProjectBopisCharacter>(GetOwner()))
	{
		if (UCameraComponent* Camera = OwningCharacter->GetFirstPersonCameraComponent())
		{
			EquippedWeapon->Fire(Camera->GetComponentLocation(), Camera->GetForwardVector());
		}
	}
}



