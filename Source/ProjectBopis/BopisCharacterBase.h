// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Weapons/WeaponBase.h"
#include "BopisCharacterBase.generated.h"

class UWeaponHolderComponent;
class UAnimMontage;

/**
 *  What the player and enemies share: carrying a weapon, its raised/aim/reload state,
 *  and the montages that animate it. The AnimBP reads everything it needs from here,
 *  so one AnimBP drives every humanoid. Who's in control — input, or an AI — lives in
 *  the subclasses.
 */
UCLASS(abstract)
class PROJECTBOPIS_API ABopisCharacterBase : public ACharacter
{
	GENERATED_BODY()

	/** Handles carrying/switching weapons */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	UWeaponHolderComponent* WeaponHolder;

	/** Fire montages played on the character mesh, keyed by the equipped weapon's anim type.
	    The character owns these rather than the weapon, since a montage is authored
	    against one specific skeleton — this character's. */
	UPROPERTY(EditAnywhere, Category = "Animation")
	TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> FireMontages;

	/** Fire montages for the off hand of a dual-wield weapon, keyed like FireMontages.
	    Falls back to FireMontages when a type has no entry here. */
	UPROPERTY(EditAnywhere, Category = "Animation")
	TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> OffhandFireMontages;

	/** Fire montages used instead while aiming (ADS), keyed like FireMontages. Types with no
	    entry use FireMontages. Duals use it to keep the original, narrower kick when aimed. */
	UPROPERTY(EditAnywhere, Category = "Animation")
	TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> AimFireMontages;

	/** Off-hand counterpart of AimFireMontages. Falls back to OffhandFireMontages. */
	UPROPERTY(EditAnywhere, Category = "Animation")
	TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> AimOffhandFireMontages;

	/** Reload montages for the off hand of a dual-wield weapon, played alongside the main
	    reload montage. Their slot must sit in a different slot group from the main one,
	    or starting one stops the other. */
	UPROPERTY(EditAnywhere, Category = "Animation")
	TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> OffhandReloadMontages;

	/** Equip montages, keyed by anim type like FireMontages. Played whenever the holder
	    equips a weapon (number keys, pickups). Firing waits until it ends. */
	UPROPERTY(EditAnywhere, Category = "Animation")
	TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> EquipMontages;

	/** Off-hand equip montages for dual weapons, played alongside in OffhandSlot. */
	UPROPERTY(EditAnywhere, Category = "Animation")
	TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> OffhandEquipMontages;

	/** Reload montages played on the character mesh, keyed by the equipped weapon's anim type. */
	UPROPERTY(EditAnywhere, Category = "Animation")
	TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> ReloadMontages;

public:

	ABopisCharacterBase();

	virtual void Tick(float DeltaSeconds) override;

	/**  Returns the weapon holder component **/
	UWeaponHolderComponent* GetWeaponHolder() const { return WeaponHolder; }

	/** Whether the aim stance is held. Drives the camera move and zoom. */
	UFUNCTION(BlueprintPure, Category = "Aim")
	bool IsAiming() const { return bIsAiming; }

	/** Holds the aim stance (weapon up) or releases it. The player drives this from input;
	    an AI calls it to raise its gun. */
	UFUNCTION(BlueprintCallable, Category = "Aim")
	void SetAiming(bool bNewAiming) { bIsAiming = bNewAiming; }

	/** Whether the weapon is up — aiming, or recently fired from the hip. The
	    AnimBP blends between lowered and raised poses on this. */
	UFUNCTION(BlueprintPure, Category = "Aim")
	bool IsWeaponRaised() const { return bIsAiming || TimeUntilWeaponLowered > 0.0f; }

	/** True while a reload montage plays — including its End section, after the weapon
	    has already finished loading. The AnimBP keeps the left-hand IK off for all of it. */
	UFUNCTION(BlueprintPure, Category = "Animation")
	bool IsReloadAnimating() const { return ActiveReloadMontage != nullptr; }

	/** Plays the equip montage(s) for a weapon that was just equipped. Called by the holder. */
	void PlayEquipAnimation(const AWeaponBase* Weapon);

	/** An equip montage is playing. Firing waits for it. */
	UFUNCTION(BlueprintPure, Category = "Weapon")
	bool IsEquipAnimating() const;

	/** Plays the body's fire montage for a shot the weapon just fired, plus the procedural kick. */
	void PlayFireAnimation(const AWeaponBase* Weapon);

	/** Plays the reload montage(s) for a reload the weapon just started. */
	void PlayReloadAnimation(const AWeaponBase* Weapon);

protected:

	/** Drives a looping (per-round) reload montage: crossfades each Loop restart, and
	    sends it to End once the weapon stops loading. */
	void UpdateReloadMontage();

	/** Seconds after the last trigger pull before the weapon lowers and the
	    character returns to free-run. Firing from the hip raises the weapon and
	    switches to the strafe stance for this long. */
	UPROPERTY(EditAnywhere, Category = "Combat", meta = (ClampMin = "0.0"))
	float LowerWeaponDelay = 1.5f;

	/** Crossfade time when a reload Loop section restarts (its first and last poses don't match). */
	UPROPERTY(EditAnywhere, Category = "Animation", meta = (ClampMin = "0.0"))
	float ReloadLoopBlendTime = 0.15f;

	bool bIsAiming = false;

	/** Counts down from LowerWeaponDelay after each trigger pull. Above zero, the
	    weapon stays raised even when not aiming. */
	float TimeUntilWeaponLowered = 0.0f;

	/** The reload montage PlayReloadAnimation started, tracked until it finishes or is cut off. */
	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> ActiveReloadMontage;

	/** The equip montage started by the last weapon change, while it plays. */
	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> ActiveEquipMontage;
};
