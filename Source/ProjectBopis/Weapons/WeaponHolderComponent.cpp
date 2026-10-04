// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "ProjectBopisCharacter.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"

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
		// Or the timer fires on a weapon we're no longer holding.
		EquippedWeapon->CancelReload();

		// The off-hand mesh is attached to our skeleton, not the weapon — bring it home
		// first, or it stays in the left hand after the weapon is put away.
		if (USkeletalMeshComponent* Offhand = EquippedWeapon->GetOffhandMesh())
		{
			Offhand->AttachToComponent(EquippedWeapon->GetWeaponMesh(),
				FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		}

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

	USkeletalMeshComponent* CharacterMesh = OwningCharacter->GetMesh();
	if (!CharacterMesh)
	{
		return;
	}

	EquippedWeapon->AttachToComponent(CharacterMesh,
		FAttachmentTransformRules::SnapToTargetNotIncludingScale, WeaponAttachSocketName);

	EquippedWeapon->SetActorRelativeLocation(EquippedWeapon->GetGripLocationOffset());
	EquippedWeapon->SetActorRelativeRotation(EquippedWeapon->GetGripRotationOffset());

	if (EquippedWeapon->IsDualWield())
	{
		if (USkeletalMeshComponent* Offhand = EquippedWeapon->GetOffhandMesh())
		{
			Offhand->AttachToComponent(CharacterMesh,
				FAttachmentTransformRules::SnapToTargetNotIncludingScale, OffhandAttachSocketName);
			Offhand->SetRelativeLocation(EquippedWeapon->GetOffhandGripLocationOffset());
			Offhand->SetRelativeRotation(EquippedWeapon->GetOffhandGripRotationOffset());
		}
	}

	EquippedWeapon->SetInstigator(OwningCharacter);
	EquippedWeapon->SetOwner(OwningCharacter);
}

bool UWeaponHolderComponent::ReloadEquippedWeapon()
{
	return EquippedWeapon ? EquippedWeapon->Reload() : false;
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

	FVector CameraLocation;
	FVector CameraDirection;
	if (!PlayerController->DeprojectScreenPositionToWorld(
		CrosshairScreenPosition.X, CrosshairScreenPosition.Y, CameraLocation, CameraDirection))
	{
		return EFireResult::NoWeapon;
	}

	// Stage 1 — the camera decides WHAT you hit. Trace from the crosshair to find
	// the point the player is actually looking at. In third person the camera sits
	// behind and beside the character, so firing along this ray directly would send
	// shots through cover the character is standing behind.
	const float AimRange = EquippedWeapon->GetMaxRange();

	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(OwningCharacter);
	QueryParams.AddIgnoredActor(EquippedWeapon);

	FHitResult AimHit;
	const bool bAimHit = GetWorld()->LineTraceSingleByChannel(
		AimHit, CameraLocation, CameraLocation + (CameraDirection * AimRange),
		ECC_Visibility, QueryParams);

	// Taken along the ray rather than from ImpactPoint, so it can be clamped.
	const float HitDistance = bAimHit ? AimHit.Distance : AimRange;
	const float ConvergeDistance = FMath::Max(HitDistance, MinConvergenceDistance);
	const FVector AimPoint = CameraLocation + (CameraDirection * ConvergeDistance);

	// Stage 2 — the muzzle decides WHERE the shot comes from.
	const FVector MuzzleLocation = EquippedWeapon->GetMuzzleLocation();

	// The muzzle can poke through a wall the character is pressed against, which would
	// let the shot originate on the far side. Trace from the character's centre out to
	// the muzzle; if that short path is blocked, the barrel isn't really where it looks.
	// Traced from the actor rather than the camera, which sits behind the character and
	// would cross its own body and any cover, giving constant false positives.
	if (bBlockShotWhenMuzzleObstructed)
	{
		FHitResult MuzzleBlockHit;
		const bool bMuzzleBlocked = GetWorld()->LineTraceSingleByChannel(
			MuzzleBlockHit, OwningCharacter->GetActorLocation(), MuzzleLocation,
			ECC_Visibility, QueryParams);

		if (bMuzzleBlocked)
		{
			return EFireResult::Blocked;
		}
	}

	FVector FireDirection = (AimPoint - MuzzleLocation).GetSafeNormal();
	if (FireDirection.IsNearlyZero())
	{
		FireDirection = CameraDirection;
	}

	return EquippedWeapon->Fire(MuzzleLocation, FireDirection);
}



