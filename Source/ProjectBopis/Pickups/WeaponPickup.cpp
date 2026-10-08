// Copyright Epic Games, Inc. All Rights Reserved.

#include "Pickups/WeaponPickup.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponBase.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Components/SphereComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Kismet/GameplayStatics.h"

AWeaponPickup::AWeaponPickup()
{
	PrimaryActorTick.bCanEverTick = false;

	TriggerComponent = CreateDefaultSubobject<USphereComponent>(TEXT("Trigger"));
	TriggerComponent->InitSphereRadius(60.0f);
	TriggerComponent->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	RootComponent = TriggerComponent;

	MeshComponent = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
	MeshComponent->SetupAttachment(TriggerComponent);
	MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AWeaponPickup::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	// Runs in the editor too, so a placed pickup shows its gun as soon as WeaponClass
	// is set. The class default object holds the Blueprint's mesh choice.
	const AWeaponBase* WeaponDefaults = WeaponClass ? WeaponClass->GetDefaultObject<AWeaponBase>() : nullptr;
	const USkeletalMeshComponent* WeaponMesh = WeaponDefaults ? WeaponDefaults->GetWeaponMesh() : nullptr;
	MeshComponent->SetSkeletalMeshAsset(WeaponMesh ? WeaponMesh->GetSkeletalMeshAsset() : nullptr);
}

void AWeaponPickup::BeginPlay()
{
	Super::BeginPlay();

	const AWeaponBase* WeaponDefaults = WeaponClass ? WeaponClass->GetDefaultObject<AWeaponBase>() : nullptr;
	const int32 MagazineSize = WeaponDefaults ? WeaponDefaults->GetMagazineSize() : 0;

	RoundsRemaining = AmmoMode == EPickupAmmoMode::Random
		? FMath::RandRange(MagazineSize / 2, MagazineSize)
		: FixedRounds;

	TriggerComponent->OnComponentBeginOverlap.AddDynamic(this, &AWeaponPickup::OnTriggerOverlap);
}

void AWeaponPickup::OnTriggerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	TryGive(OtherActor);
}

void AWeaponPickup::TryGive(AActor* Collector)
{
	const AProjectBopisCharacter* Character = Cast<AProjectBopisCharacter>(Collector);
	UWeaponHolderComponent* Holder = Character ? Character->GetWeaponHolder() : nullptr;
	if (!Holder || !WeaponClass)
	{
		return;
	}

	// New weapon: it joins the backpack carrying this pickup's rounds.
	if (!Holder->FindCarriedWeapon(WeaponClass))
	{
		Holder->GiveWeapon(WeaponClass, RoundsRemaining);
		Consume();
		return;
	}

	// Second copy of a dual-capable weapon: unlock the dual version, keep the single.
	const TSubclassOf<AWeaponBase> DualClass = WeaponClass->GetDefaultObject<AWeaponBase>()->GetDualWieldClass();
	if (DualClass && !Holder->FindCarriedWeapon(DualClass))
	{
		Holder->GiveWeapon(DualClass, RoundsRemaining);
		Consume();
		return;
	}

	// Already have everything this pickup offers: it's an ammo box now.
	const EAmmoType AmmoType = WeaponClass->GetDefaultObject<AWeaponBase>()->GetAmmoType();
	const int32 Taken = Holder->AddAmmo(AmmoType, RoundsRemaining);
	if (Taken <= 0)
	{
		return;
	}

	RoundsRemaining -= Taken;
	if (RoundsRemaining <= 0)
	{
		Consume();
	}
	else if (PickupSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, PickupSound, GetActorLocation());
	}
}

void AWeaponPickup::Consume()
{
	if (PickupSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, PickupSound, GetActorLocation());
	}

	Destroy();
}
