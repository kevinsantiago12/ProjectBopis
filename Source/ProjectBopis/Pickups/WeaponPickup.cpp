// Copyright Epic Games, Inc. All Rights Reserved.

#include "Pickups/WeaponPickup.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponBase.h"
#include "Weapons/WeaponHolderComponent.h"
#include "UI/GameMessageSubsystem.h"
#include "Components/SphereComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Kismet/GameplayStatics.h"

namespace
{
	/** "Picked up 9mm Pistol": the weapon's display name. */
	void ShowWeaponMessage(const UObject* WorldContextObject, TSubclassOf<AWeaponBase> WeaponClass)
	{
		const FText& Name = WeaponClass->GetDefaultObject<AWeaponBase>()->GetDisplayName();
		UGameMessageSubsystem::ShowGameMessage(WorldContextObject, FText::Format(NSLOCTEXT("GameMessages", "Weapon", "Picked up {0}"), Name));
	}
}

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
	// Small and still: the sun's cascade shadow isn't worth it for a pickup.
	MeshComponent->SetCastShadow(false);
}

void AWeaponPickup::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	// Runs in the editor too, so a placed pickup shows its gun as soon as WeaponClass
	// is set. The class default object holds the Blueprint's mesh choice.
	const AWeaponBase* WeaponDefaults = WeaponClass ? WeaponClass->GetDefaultObject<AWeaponBase>() : nullptr;
	const USkeletalMeshComponent* WeaponMesh = WeaponDefaults ? WeaponDefaults->GetWeaponMesh() : nullptr;
	MeshComponent->SetSkeletalMeshAsset(WeaponMesh ? WeaponMesh->GetSkeletalMeshAsset() : nullptr);
	// The same size as in the hand: the weapon Blueprint's mesh scale.
	MeshComponent->SetRelativeScale3D(WeaponMesh ? WeaponMesh->GetRelativeScale3D() : FVector::OneVector);
}

void AWeaponPickup::BeginPlay()
{
	Super::BeginPlay();

	const AWeaponBase* WeaponDefaults = WeaponClass ? WeaponClass->GetDefaultObject<AWeaponBase>() : nullptr;
	const int32 MagazineSize = WeaponDefaults ? WeaponDefaults->GetMagazineSize() : 0;

	const int32 Base = FMath::RoundToInt(MagazineSize * BaseMagazines);
	const int32 Extra = FMath::RoundToInt(MagazineSize * RandomExtraMagazines);
	RoundsRemaining = AmmoMode == EPickupAmmoMode::Random
		? FMath::RandRange(Base, Base + Extra)
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

	// New weapon: it joins the backpack with this pickup's rounds.
	if (!Holder->FindCarriedWeapon(WeaponClass))
	{
		GiveNewWeapon(Holder, WeaponClass);
		return;
	}

	// Second copy of a dual-capable weapon: unlock the dual version, keep the single.
	const TSubclassOf<AWeaponBase> DualClass = WeaponClass->GetDefaultObject<AWeaponBase>()->GetDualWieldClass();
	if (DualClass && !Holder->FindCarriedWeapon(DualClass))
	{
		GiveNewWeapon(Holder, DualClass);
		return;
	}

	// Already have everything this pickup offers: it's an ammo box now. It fills the pool as far
	// as it can and goes; what doesn't fit is lost.
	const EAmmoType AmmoType = WeaponClass->GetDefaultObject<AWeaponBase>()->GetAmmoType();
	const int32 Taken = Holder->AddAmmo(AmmoType, RoundsRemaining);
	if (Taken <= 0)
	{
		return;
	}

	UGameMessageSubsystem::ShowAmmoMessage(this, AmmoType, Taken);
	Consume();
}

void AWeaponPickup::GiveNewWeapon(UWeaponHolderComponent* Holder, TSubclassOf<AWeaponBase> NewClass)
{
	// A magazine can't hold more than its size, so what's over goes to the shared pool.
	const AWeaponBase* Defaults = NewClass->GetDefaultObject<AWeaponBase>();
	const int32 InMagazine = FMath::Min(RoundsRemaining, Defaults->GetMagazineSize());
	Holder->GiveWeapon(NewClass, InMagazine);
	Holder->AddAmmo(Defaults->GetAmmoType(), RoundsRemaining - InMagazine);
	ShowWeaponMessage(this, NewClass);
	Consume();
}

void AWeaponPickup::Consume()
{
	if (PickupSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, PickupSound, GetActorLocation());
	}

	Destroy();
}
