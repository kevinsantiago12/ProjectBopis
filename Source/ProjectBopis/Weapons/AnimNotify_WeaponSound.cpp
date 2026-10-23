#include "Weapons/AnimNotify_WeaponSound.h"
#include "BopisCharacterBase.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Components/SkeletalMeshComponent.h"

void UAnimNotify_WeaponSound::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
	const FAnimNotifyEventReference& EventReference)
{
	Super::Notify(MeshComp, Animation, EventReference);

	AActor* Owner = MeshComp ? MeshComp->GetOwner() : nullptr;

	// On a gun's own animation: that gun, and the hand whose mesh is playing it.
	if (AWeaponBase* Weapon = Cast<AWeaponBase>(Owner))
	{
		Weapon->PlayWeaponSound(Sound, MeshComp == Weapon->GetOffhandMesh());
		return;
	}

	// On a character's montage: whatever it's holding right now.
	const ABopisCharacterBase* Character = Cast<ABopisCharacterBase>(Owner);
	const UWeaponHolderComponent* Holder = Character ? Character->GetWeaponHolder() : nullptr;
	if (AWeaponBase* Weapon = Holder ? Holder->GetEquippedWeapon() : nullptr)
	{
		Weapon->PlayWeaponSound(Sound, bOffhand);
	}
}

FString UAnimNotify_WeaponSound::GetNotifyName_Implementation() const
{
	return FString::Printf(TEXT("Weapon Sound: %s%s"),
		*UEnum::GetDisplayValueAsText(Sound).ToString(), bOffhand ? TEXT(" (off hand)") : TEXT(""));
}
