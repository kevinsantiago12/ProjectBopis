// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/KillCamComponent.h"
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

	// The starting weapon first, so it's the one equipped; the rest go into the backpack.
	if (StartingWeaponClass)
	{
		if (AWeaponBase* StartingWeapon = GetWorld()->SpawnActor<AWeaponBase>(StartingWeaponClass))
		{
			AddWeapon(StartingWeapon);
		}
	}

	for (const TSubclassOf<AWeaponBase>& WeaponClass : StartingLoadout)
	{
		if (!WeaponClass || FindCarriedWeapon(WeaponClass))
		{
			continue;
		}

		if (AWeaponBase* Weapon = GetWorld()->SpawnActor<AWeaponBase>(WeaponClass))
		{
			// Hidden until equipped; otherwise it would sit visible wherever it spawned.
			Weapon->SetActorHiddenInGame(true);
			AddWeapon(Weapon);
		}
	}

	if (bStartWithFullAmmo)
	{
		// AddAmmo caps at each type's maximum, so asking for the maximum fills it.
		for (const AWeaponBase* Weapon : CarriedWeapons)
		{
			if (Weapon)
			{
				AddAmmo(Weapon->GetAmmoType(), GetMaxAmmo(Weapon->GetAmmoType()));
			}
		}
	}
}


void UWeaponHolderComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// The weapons are actors of their own; they leave with their owner.
	for (AWeaponBase* Weapon : CarriedWeapons)
	{
		if (Weapon)
		{
			Weapon->Destroy();
		}
	}
	CarriedWeapons.Reset();
	EquippedWeapon = nullptr;

	Super::EndPlay(EndPlayReason);
}

// Called every frame
void UWeaponHolderComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

bool UWeaponHolderComponent::AddWeapon(AWeaponBase* NewWeapon, bool bAddStartingReserve)
{
	if (!NewWeapon || CarriedWeapons.Contains(NewWeapon))
	{
		return false;
	}

	InsertCarried(NewWeapon);

	// The weapon reloads from our pool. A weapon from the start loadout brings its
	// starting reserve; a picked-up one brings only the rounds in its magazine.
	NewWeapon->SetReserveSource(this);
	if (bAddStartingReserve)
	{
		AddAmmo(NewWeapon->GetAmmoType(), NewWeapon->GetStartingReserveAmmo());
	}

	// Duals imply the single (Max Payne style): carrying the pair always includes one.
	// Loaded from the shared pool, so no rounds appear from nowhere.
	const TSubclassOf<AWeaponBase> SingleClass = NewWeapon->GetSingleWieldClass();
	if (SingleClass && !FindCarriedWeapon(SingleClass))
	{
		if (AWeaponBase* Single = GetWorld()->SpawnActor<AWeaponBase>(SingleClass))
		{
			Single->SetActorHiddenInGame(true);
			Single->SetReserveSource(this);
			Single->SetAmmoInMagazine(TakeAmmo(Single->GetAmmoType(), Single->GetMagazineSize()));
			InsertCarried(Single);
		}
	}

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

	// The owner animates the change; the holder only swaps the weapon.
	if (ABopisCharacterBase* OwningCharacter = Cast<ABopisCharacterBase>(GetOwner()))
	{
		OwningCharacter->PlayEquipAnimation(EquippedWeapon);
	}
}

bool UWeaponHolderComponent::SelectSlot(int32 Slot)
{
	TArray<AWeaponBase*> InSlot;
	for (AWeaponBase* Weapon : CarriedWeapons)
	{
		if (Weapon && Weapon->GetWeaponSlot() == Slot)
		{
			InSlot.Add(Weapon);
		}
	}

	if (InSlot.IsEmpty())
	{
		return false;
	}

	// Find returns INDEX_NONE (-1) when the equipped weapon is in another slot, so +1
	// lands on the first weapon of this one; otherwise it steps to the next and wraps.
	const int32 CurrentIndex = InSlot.Find(EquippedWeapon);
	AWeaponBase* Next = InSlot[(CurrentIndex + 1) % InSlot.Num()];

	if (Next != EquippedWeapon)
	{
		EquipWeapon(Next);
	}

	return true;
}

AWeaponBase* UWeaponHolderComponent::FindCarriedWeapon(TSubclassOf<AWeaponBase> WeaponClass) const
{
	for (AWeaponBase* Weapon : CarriedWeapons)
	{
		// Exact class: BP_DualPistols must not count as carrying BP_Pistol, or vice versa.
		if (Weapon && Weapon->GetClass() == WeaponClass)
		{
			return Weapon;
		}
	}

	return nullptr;
}

AWeaponBase* UWeaponHolderComponent::GiveWeapon(TSubclassOf<AWeaponBase> WeaponClass, int32 RoundsInMagazine)
{
	if (!WeaponClass)
	{
		return nullptr;
	}

	AWeaponBase* NewWeapon = GetWorld()->SpawnActor<AWeaponBase>(WeaponClass);
	if (!NewWeapon)
	{
		return nullptr;
	}

	// Spawning runs the weapon's BeginPlay, which fills the magazine — overwrite it after.
	NewWeapon->SetAmmoInMagazine(RoundsInMagazine);

	// Hidden until equipped; otherwise it would sit visible wherever it spawned.
	NewWeapon->SetActorHiddenInGame(true);

	AddWeapon(NewWeapon, false);

	// AddWeapon already equipped it if the hands were empty. Otherwise only an upgrade is
	// switched to: the .45 in hand switches to a 9mm or an Uzi, never the other way round.
	if (bAutoEquipOnPickup && EquippedWeapon && EquippedWeapon != NewWeapon && NewWeapon->RanksAbove(*EquippedWeapon))
	{
		EquipWeapon(NewWeapon);
	}

	return NewWeapon;
}

void UWeaponHolderComponent::InsertCarried(AWeaponBase* Weapon)
{
	const int32 Index = CarriedWeapons.IndexOfByPredicate([Weapon](const TObjectPtr<AWeaponBase>& Carried)
	{
		return Carried && Carried->RanksAbove(*Weapon);
	});
	CarriedWeapons.Insert(Weapon, Index == INDEX_NONE ? CarriedWeapons.Num() : Index);
}

void UWeaponHolderComponent::AttachWeaponToHand()
{
	if (!EquippedWeapon)
	{
		return;
	}

	ACharacter* OwningCharacter = Cast<ACharacter>(GetOwner());
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

bool UWeaponHolderComponent::ReloadEquippedWeapon(float Speed)
{
	return EquippedWeapon ? EquippedWeapon->Reload(Speed) : false;
}

EFireResult UWeaponHolderComponent::FireEquippedWeapon(bool bFreshPull)
{
	if (!EquippedWeapon)
	{
		return EFireResult::NoWeapon;
	}

	// Aims from the player's camera crosshair, so this path is player-only. Enemies
	// will get their own aim source when they start shooting.
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

	// Only what's past the character can be the target. The camera sits behind him and 50-65 cm
	// to the side, and swings past door leaves and jambs, so anything between the two would pull
	// the shot sideways or backwards. The trace starts level with the character, as the pose's does.
	const float CharacterDepth = FMath::Max(
		FVector::DotProduct(OwningCharacter->GetActorLocation() - CameraLocation, CameraDirection), 0.0f);

	FHitResult AimHit;
	const bool bAimHit = GetWorld()->LineTraceSingleByChannel(
		AimHit, CameraLocation + (CameraDirection * CharacterDepth), CameraLocation + (CameraDirection * AimRange),
		ECC_Visibility, QueryParams);

	// Stage 2 — the muzzle decides WHERE the shot comes from.
	const FVector MuzzleLocation = EquippedWeapon->GetMuzzleLocation();

	// Taken along the ray rather than from ImpactPoint, so it can be clamped: never nearer than
	// MinConvergenceDistance past the muzzle, or the shot would leave sideways or backwards.
	const float HitDistance = bAimHit ? CharacterDepth + AimHit.Distance : AimRange;
	const float MuzzleDepth = FVector::DotProduct(MuzzleLocation - CameraLocation, CameraDirection);
	const float ConvergeDistance = FMath::Max(HitDistance, MuzzleDepth + MinConvergenceDistance);
	FVector AimPoint = CameraLocation + (CameraDirection * ConvergeDistance);

	// The kill cam has the view, so the crosshair is looking from somewhere else: the shots go
	// into the body it's showing.
	if (UKillCamComponent* KillCam = OwningCharacter->GetKillCam(); KillCam && KillCam->IsPlaying())
	{
		AimPoint = KillCam->TakeShotPoint();
	}

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

	return EquippedWeapon->Fire(MuzzleLocation, FireDirection, false, bFreshPull);
}

int32 UWeaponHolderComponent::GetReserveAmmo(EAmmoType Type) const
{
	return ReserveAmmo.FindRef(Type);
}

int32 UWeaponHolderComponent::GetMaxAmmo(EAmmoType Type) const
{
	const int32* Max = MaxAmmoByType.Find(Type);
	return Max ? *Max : DefaultMaxAmmo;
}

int32 UWeaponHolderComponent::AddAmmo(EAmmoType Type, int32 Amount)
{
	if (Amount <= 0)
	{
		return 0;
	}

	int32& Current = ReserveAmmo.FindOrAdd(Type);
	const int32 Taken = FMath::Min(Amount, FMath::Max(0, GetMaxAmmo(Type) - Current));
	Current += Taken;
	return Taken;
}

int32 UWeaponHolderComponent::TakeAmmo(EAmmoType Type, int32 Wanted)
{
	int32* Current = ReserveAmmo.Find(Type);
	if (!Current || Wanted <= 0)
	{
		return 0;
	}

	const int32 Taken = FMath::Min(Wanted, *Current);
	*Current -= Taken;
	return Taken;
}



