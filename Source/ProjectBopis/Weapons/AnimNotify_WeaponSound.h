#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "Weapons/WeaponBase.h"
#include "AnimNotify_WeaponSound.generated.h"

/** Plays a sound of the weapon involved: on a character's montage, its equipped gun; on a
    gun's own animation, that gun. Which sound is the weapon's call (its Weapon|Sounds
    slots), so one reload montage serves every gun that shares it. */
UCLASS(meta = (DisplayName = "Weapon Sound"))
class PROJECTBOPIS_API UAnimNotify_WeaponSound : public UAnimNotify
{
	GENERATED_BODY()

public:
	virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
		const FAnimNotifyEventReference& EventReference) override;
	virtual FString GetNotifyName_Implementation() const override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon Sound")
	EWeaponSound Sound = EWeaponSound::MagOut;

	/** Dual wield: the off-hand gun's sound (on the off-hand reload and draw montages). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon Sound")
	bool bOffhand = false;
};
