// Copyright Epic Games, Inc. All Rights Reserved.

#include "Pickups/AmmoPickup.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"

AAmmoPickup::AAmmoPickup()
{
	PrimaryActorTick.bCanEverTick = false;

	TriggerComponent = CreateDefaultSubobject<USphereComponent>(TEXT("Trigger"));
	TriggerComponent->InitSphereRadius(60.0f);
	TriggerComponent->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	RootComponent = TriggerComponent;

	MeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	MeshComponent->SetupAttachment(TriggerComponent);
	MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AAmmoPickup::BeginPlay()
{
	Super::BeginPlay();

	TriggerComponent->OnComponentBeginOverlap.AddDynamic(this, &AAmmoPickup::OnTriggerOverlap);
}

void AAmmoPickup::OnTriggerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	TryGiveAmmo(OtherActor);
}

void AAmmoPickup::TryGiveAmmo(AActor* Collector)
{
	const AProjectBopisCharacter* Character = Cast<AProjectBopisCharacter>(Collector);
	UWeaponHolderComponent* Holder = Character ? Character->GetWeaponHolder() : nullptr;
	if (!Holder)
	{
		return;
	}

	const int32 Taken = Holder->AddAmmo(AmmoType, Amount);
	if (Taken <= 0)
	{
		// Pool already full for this type — leave the pickup for later.
		return;
	}

	Amount -= Taken;

	if (PickupSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, PickupSound, GetActorLocation());
	}

	if (Amount <= 0)
	{
		Destroy();
	}
}
