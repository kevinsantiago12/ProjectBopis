// Copyright Epic Games, Inc. All Rights Reserved.

#include "BopisCharacterBase.h"
#include "ProjectBopisAnimInstance.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "AlphaBlend.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

ABopisCharacterBase::ABopisCharacterBase()
{
	// The lowering timer and the looping reload montage are driven per frame.
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(34.0f, 96.0f);

	WeaponHolder = CreateDefaultSubobject<UWeaponHolderComponent>(TEXT("WeaponHolder"));

	// Crouch does nothing at all without this, and fails silently — CanCrouch()
	// just returns false with no warning. It is false by default.
	GetCharacterMovement()->NavAgentProps.bCanCrouch = true;
}

void ABopisCharacterBase::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	TimeUntilWeaponLowered = FMath::Max(0.0f, TimeUntilWeaponLowered - DeltaSeconds);

	UpdateReloadMontage();
}

void ABopisCharacterBase::PlayFireAnimation(const AWeaponBase* Weapon)
{
	if (!Weapon)
	{
		return;
	}

	// Deliberately not gated on UsesAnimationDrivenFeedback() — that flag says
	// where the *weapon's* sound and muzzle flash come from. The body animation
	// is the character animating itself, and plays either way. Looked up by the
	// weapon's anim type, so each weapon gets its own without owning the asset.
	const EWeaponAnimType AnimType = Weapon->GetAnimType();
	UAnimMontage* FoundMontage = nullptr;

	// Most specific map first; each lookup only runs while nothing usable is found yet.
	auto TryMap = [&FoundMontage, AnimType](const TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>>& Map)
	{
		if (!FoundMontage)
		{
			const TObjectPtr<UAnimMontage>* Entry = Map.Find(AnimType);
			FoundMontage = Entry ? Entry->Get() : nullptr;
		}
	};

	if (Weapon->WasLastShotOffhand())
	{
		if (bIsAiming)
		{
			TryMap(AimOffhandFireMontages);
		}
		TryMap(OffhandFireMontages);
	}

	if (bIsAiming)
	{
		TryMap(AimFireMontages);
	}
	TryMap(FireMontages);

	if (FoundMontage)
	{
		if (UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance())
		{
			AnimInstance->Montage_Play(FoundMontage);
		}
	}

	// Procedural kick on top of the montage. It stacks across rapid shots, where the
	// montage just restarts.
	if (UProjectBopisAnimInstance* BopisAnim = Cast<UProjectBopisAnimInstance>(GetMesh()->GetAnimInstance()))
	{
		BopisAnim->AddRecoil(Weapon->WasLastShotOffhand());
	}
}

void ABopisCharacterBase::PlayReloadAnimation(const AWeaponBase* Weapon)
{
	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (!Weapon || !AnimInstance)
	{
		return;
	}

	const EWeaponAnimType AnimType = Weapon->GetAnimType();

	if (TObjectPtr<UAnimMontage>* FoundMontage = ReloadMontages.Find(AnimType); FoundMontage && *FoundMontage)
	{
		AnimInstance->Montage_Play(*FoundMontage);
		ActiveReloadMontage = *FoundMontage;
	}

	// Dual wield reloads both guns in one beat: the off hand plays its own montage in its
	// own slot group, mirrored onto the left arm by the AnimBP.
	if (Weapon->IsDualWield())
	{
		if (TObjectPtr<UAnimMontage>* FoundOffhand = OffhandReloadMontages.Find(AnimType); FoundOffhand && *FoundOffhand)
		{
			AnimInstance->Montage_Play(*FoundOffhand);
		}
	}
}

void ABopisCharacterBase::PlayEquipAnimation(const AWeaponBase* Weapon)
{
	ActiveEquipMontage = nullptr;

	UAnimInstance* AnimInstance = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	if (!Weapon || !AnimInstance)
	{
		return;
	}

	const EWeaponAnimType AnimType = Weapon->GetAnimType();

	if (const TObjectPtr<UAnimMontage>* Found = EquipMontages.Find(AnimType); Found && *Found)
	{
		// Same slot group as fire/reload, so this also cuts off whatever the previous
		// weapon was still playing.
		ActiveEquipMontage = *Found;
		AnimInstance->Montage_Play(ActiveEquipMontage);
	}

	if (Weapon->IsDualWield())
	{
		if (const TObjectPtr<UAnimMontage>* FoundOffhand = OffhandEquipMontages.Find(AnimType); FoundOffhand && *FoundOffhand)
		{
			AnimInstance->Montage_Play(*FoundOffhand);
		}
	}
}

bool ABopisCharacterBase::IsEquipAnimating() const
{
	const UAnimInstance* AnimInstance = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
	return ActiveEquipMontage && AnimInstance && AnimInstance->Montage_IsPlaying(ActiveEquipMontage);
}

void ABopisCharacterBase::UpdateReloadMontage()
{
	if (!ActiveReloadMontage)
	{
		return;
	}

	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (!AnimInstance || !AnimInstance->Montage_IsPlaying(ActiveReloadMontage))
	{
		// Finished, or cut off — firing plays a montage in the same slot group.
		ActiveReloadMontage = nullptr;
		return;
	}

	static const FName LoopSection(TEXT("Loop"));
	static const FName EndSection(TEXT("End"));

	if (AnimInstance->Montage_GetCurrentSection(ActiveReloadMontage) != LoopSection)
	{
		return; // Start, End, or a magazine-style reload with no Loop at all.
	}

	// Loading stops when the magazine fills, the reserve runs dry, or the weapon is
	// swapped: let the current insert finish, then play End (the rack).
	const AWeaponBase* EquippedWeapon = WeaponHolder ? WeaponHolder->GetEquippedWeapon() : nullptr;
	if (!EquippedWeapon || !EquippedWeapon->IsReloading())
	{
		AnimInstance->Montage_SetNextSection(LoopSection, EndSection, ActiveReloadMontage);
		return;
	}

	// Section jumps inside a montage don't blend, and Loop's first and last poses don't
	// match, so letting it wrap snaps. Instead, a blend-time before Loop ends, start a
	// fresh copy at Loop's start: it crossfades in while the old one fades out.
	float LoopStart = 0.0f;
	float LoopEnd = 0.0f;
	ActiveReloadMontage->GetSectionStartAndEndTime(
		ActiveReloadMontage->GetSectionIndex(LoopSection), LoopStart, LoopEnd);

	if (AnimInstance->Montage_GetPosition(ActiveReloadMontage) >= LoopEnd - ReloadLoopBlendTime)
	{
		// bStopAllMontages = true stops the montages already in this slot group — here,
		// the copy we're replacing — blending it out over the new copy's blend-in. That
		// is the crossfade. (False would leave the old copy looping underneath.)
		AnimInstance->Montage_PlayWithBlendIn(ActiveReloadMontage, FAlphaBlendArgs(ReloadLoopBlendTime),
			1.0f, EMontagePlayReturnType::MontageLength, LoopStart, true);
	}
}
