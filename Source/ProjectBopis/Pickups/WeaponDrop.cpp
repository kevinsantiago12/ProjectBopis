// Copyright Epic Games, Inc. All Rights Reserved.

#include "Pickups/WeaponDrop.h"
#include "Pickups/WeaponPickup.h"
#include "Weapons/WeaponBase.h"
#include "Components/BoxComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ProjectBopis.h"

AWeaponDrop::AWeaponDrop()
{
	PrimaryActorTick.bCanEverTick = true;

	Body = CreateDefaultSubobject<UBoxComponent>(TEXT("Body"));
	Body->InitBoxExtent(FVector(20.0f, 5.0f, 10.0f));

	// Solid against the world, but no obstacle to people, cameras or bullets.
	Body->SetCollisionProfileName(TEXT("PhysicsActor"));
	Body->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	Body->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	Body->SetCollisionResponseToChannel(ECC_Projectile, ECR_Ignore);
	Body->SetSimulatePhysics(true);
	RootComponent = Body;

	MeshComponent = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
	MeshComponent->SetupAttachment(Body);
	MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AWeaponDrop::Launch(TSubclassOf<AWeaponBase> InWeaponClass, TSubclassOf<AWeaponPickup> InPickupClass,
	const FVector& Velocity, const FVector& AngularVelocityDegrees)
{
	WeaponClass = InWeaponClass;
	PickupClass = InPickupClass;

	// The weapon's own mesh, from its class defaults — same trick as AWeaponPickup.
	const AWeaponBase* WeaponDefaults = WeaponClass ? WeaponClass->GetDefaultObject<AWeaponBase>() : nullptr;
	const USkeletalMeshComponent* WeaponMesh = WeaponDefaults ? WeaponDefaults->GetWeaponMesh() : nullptr;
	MeshComponent->SetSkeletalMeshAsset(WeaponMesh ? WeaponMesh->GetSkeletalMeshAsset() : nullptr);

	// Fit the box to the gun and centre it, then shift the actor by the same amount so the
	// gun stays exactly where the hand held it.
	const FBox LocalBox = MeshComponent->CalcBounds(FTransform::Identity).GetBox();
	if (LocalBox.IsValid)
	{
		Body->SetBoxExtent(LocalBox.GetExtent());
		MeshComponent->SetRelativeLocation(-LocalBox.GetCenter());
		SetActorLocation(GetActorLocation() + GetActorQuat().RotateVector(LocalBox.GetCenter()),
			false, nullptr, ETeleportType::TeleportPhysics);
	}

	Body->SetPhysicsLinearVelocity(Velocity);
	Body->SetPhysicsAngularVelocityInDegrees(AngularVelocityDegrees);
}

void AWeaponDrop::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	FlightTime += DeltaSeconds;
	const bool bSettled = FlightTime >= MinFlightTime && Body->GetPhysicsLinearVelocity().Size() < SettleSpeed;
	if (bSettled || FlightTime >= MaxFlightTime)
	{
		BecomePickup();
	}
}

void AWeaponDrop::BecomePickup()
{
	if (PickupClass && WeaponClass)
	{
		// Exactly where the gun lies, so the swap can't be seen. Deferred, so the pickup
		// knows its weapon before its construction script picks the mesh.
		const FTransform Where = MeshComponent->GetComponentTransform();
		if (AWeaponPickup* Pickup = GetWorld()->SpawnActorDeferred<AWeaponPickup>(PickupClass, Where,
			nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn))
		{
			Pickup->SetWeaponClass(WeaponClass);
			Pickup->FinishSpawning(Where);
		}
	}

	Destroy();
}
