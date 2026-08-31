// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "ProjectBopisCharacter.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"

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

	if (StartingWeaponClass)
	{
		if (AWeaponBase* StartingWeapon = GetWorld()->SpawnActor<AWeaponBase>(StartingWeaponClass))
		{
			AddWeapon(StartingWeapon);
		}
	}

	// TEMP DEBUG: re-snap after 5s to test whether the initial attach is mistimed.
	GetWorld()->GetTimerManager().SetTimer(DebugResnapTimerHandle, this,
		&UWeaponHolderComponent::AttachWeaponToHand, 5.0f, false);

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

	AttachWeaponToHand();

	EquippedWeapon->SetActorHiddenInGame(false);
}

void UWeaponHolderComponent::AttachWeaponToHand()
{
	if (!EquippedWeapon)
	{
		return;
	}

	AProjectBopisCharacter* OwningCharacter = Cast<AProjectBopisCharacter>(GetOwner());
	if (!OwningCharacter)
	{
		return;
	}

	USkeletalMeshComponent* ArmsMesh = OwningCharacter->GetFirstPersonMesh();
	if (!ArmsMesh)
	{
		return;
	}

	EquippedWeapon->AttachToComponent(ArmsMesh,
		FAttachmentTransformRules::SnapToTargetNotIncludingScale, WeaponAttachSocketName);

	EquippedWeapon->SetActorRelativeLocation(EquippedWeapon->GetGripLocationOffset());
	EquippedWeapon->SetActorRelativeRotation(EquippedWeapon->GetGripRotationOffset());

	EquippedWeapon->SetInstigator(OwningCharacter);
	EquippedWeapon->SetOwner(OwningCharacter);

	if (USkeletalMeshComponent* MeshComp = EquippedWeapon->GetWeaponMesh())
	{
		MeshComp->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::FirstPerson);
	}
}

EFireResult UWeaponHolderComponent::FireEquippedWeapon()
{
	if (!EquippedWeapon)
	{
		return EFireResult::NoWeapon;
	}

	AProjectBopisCharacter* OwningCharacter = Cast<AProjectBopisCharacter>(GetOwner());
	if (!OwningCharacter)
	{
		return EFireResult::NoWeapon;
	}

	APlayerController* PlayerController = Cast<APlayerController>(OwningCharacter->GetController());
	if (!PlayerController)
	{
		return EFireResult::NoWeapon;
	}

	int32 ViewportSizeX = 0;
	int32 ViewportSizeY = 0;
	PlayerController->GetViewportSize(ViewportSizeX, ViewportSizeY);

	const FVector2D CrosshairScreenPosition(ViewportSizeX * 0.5f, ViewportSizeY * CrosshairViewportPositionY);

	FVector TraceStart;
	FVector TraceDirection;
	if (PlayerController->DeprojectScreenPositionToWorld(CrosshairScreenPosition.X, CrosshairScreenPosition.Y, TraceStart, TraceDirection))
	{
		return EquippedWeapon->Fire(TraceStart, TraceDirection);
	}

	return EFireResult::NoWeapon;
}



