// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Weapons/WeaponBase.h"
#include "BopisCharacterBase.generated.h"

class UWeaponHolderComponent;
class UHealthComponent;
class UPhysicalAnimationComponent;
class UAnimMontage;
class UAnimSequenceBase;
struct FDamageEvent;

/** Animations picked by which side a hit came from. One is chosen at random per side. */
USTRUCT(BlueprintType)
struct FDirectionalAnimSet
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Animation")
	TArray<TObjectPtr<UAnimSequenceBase>> Front;

	UPROPERTY(EditAnywhere, Category = "Animation")
	TArray<TObjectPtr<UAnimSequenceBase>> Back;

	UPROPERTY(EditAnywhere, Category = "Animation")
	TArray<TObjectPtr<UAnimSequenceBase>> Left;

	UPROPERTY(EditAnywhere, Category = "Animation")
	TArray<TObjectPtr<UAnimSequenceBase>> Right;
};

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

	/** Health — damage arrives through TakeDamage. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UHealthComponent> Health;

	/** Pulls simulated bones back toward the animated pose — the riddled hit-dance. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UPhysicalAnimationComponent> PhysicalAnimation;

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

	UHealthComponent* GetHealthComponent() const { return Health; }

	/** Routes every hit: bone multiplier, health, and death on the killing blow. Hits on
	    a corpse just shove it. */
	virtual float TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
		AController* EventInstigator, AActor* DamageCauser) override;

	UFUNCTION(BlueprintPure, Category = "Health")
	bool IsDead() const { return bIsDead; }

	/** Staggered: upper body on physics and rooted to the spot, wide open to more fire. */
	UFUNCTION(BlueprintPure, Category = "Health|Hit Reactions")
	bool IsStaggered() const { return bIsStaggered; }

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

	/** Health has run out: the AI stops, the capsule drops out, and a death animation plays.
	    Subclasses add what dying means for them. */
	virtual void Die(AController* Killer, const FVector& ShotDirection);

	/** Goes limp: physics takes over from the animation, launched by the bullet that did it
	    (none when the death animation simply ran out). */
	void StartRagdoll(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage);

	/** Throws the ragdoll along a bullet's path, harder for harder-hitting rounds. */
	void LaunchBody(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage);

	/** Starts a death animation for a hit from this direction. False if none is set. */
	bool PlayDeathAnimation(const FVector& ShotDirection);

	/** Plays one of a set's animations, picked by the side a shot came from, in the full-body
	    DeathSlotName. Null if the set has nothing to play. */
	UAnimMontage* PlayDirectionalAnimation(const FDirectionalAnimSet& Set, const FVector& ShotDirection);

	/** Upper body (RiddledRootBone and below) onto physics, motors holding it to the animation.
	    Shared by hit reactions, stagger and riddled. */
	void SimulateUpperBody(float HoldStrength);

	/** Light hit reaction: the upper body jerks on physics, then settles back over
	    HitReactDuration. Feedback only — movement, aim and fire carry on underneath. */
	void StartHitReaction(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage);

	/** Heavy hit reaction from StaggerDamage within StaggerWindow: the upper body loosens on
	    motors, a stagger animation plays, and the body can't move for StaggerDuration.
	    Triggering it again restarts it — enemies can be stun-locked. */
	void StartStagger(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage);

	/** Ends a hit reaction or stagger: bones back to the animation, movement back on unless dead. */
	void EndHitReactions();

	/** Hit reaction: seconds the upper body stays on physics after a hit, fading back to the
	    animation. 0 turns light hit reactions off. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions", meta = (ClampMin = "0.0"))
	float HitReactDuration = 0.3f;

	/** Hit reaction motor strength. High, so the body snaps back and keeps doing its job. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions", meta = (ClampMin = "0.0"))
	float HitReactHoldStrength = 2000.0f;

	/** Hit reaction kick on the struck bone, as a multiple of the normal launch speed. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions", meta = (ClampMin = "0.0"))
	float HitReactKickScale = 0.6f;

	/** Damage within StaggerWindow that staggers. Each stagger needs a fresh amount. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions|Stagger", meta = (ClampMin = "0.0"))
	float StaggerDamage = 60.0f;

	/** World-time seconds over which hits add up toward StaggerDamage. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions|Stagger", meta = (ClampMin = "0.0"))
	float StaggerWindow = 0.5f;

	/** Seconds a stagger roots the body. 0 turns staggers off (hits stay light reactions). */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions|Stagger", meta = (ClampMin = "0.0"))
	float StaggerDuration = 0.8f;

	/** Stagger motor strength. Lower than a hit reaction's, so the body reels. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions|Stagger", meta = (ClampMin = "0.0"))
	float StaggerHoldStrength = 600.0f;

	/** Kick on the struck bone while staggered, as a multiple of the normal launch speed. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions|Stagger", meta = (ClampMin = "0.0"))
	float StaggerKickScale = 1.2f;

	/** Stagger animations by the side the staggering shot came from. Optional: without them
	    the stagger is physics only. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Reactions|Stagger")
	FDirectionalAnimSet StaggerAnimations;

	virtual void BeginPlay() override;

	/** Switches the body to the Ragdoll collision profile, keeping it solid to bullets
	    (the profile as shipped ignores Visibility, so traces would pass straight through). */
	void UseRagdollCollision();

	/** Kicks the hit bone if it's simulating; otherwise (an animated leg while riddled) the
	    riddled root, so every hit still moves the body. */
	void KickBone(FName BoneName, const FVector& ShotDirection, float BulletDamage, float Scale);

	/** Damage beyond lethal, landing within OverkillWindow of the kill, that skips the death
	    animation and riddled phase and goes straight to ragdoll — a full close shotgun blast. */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.0"))
	float InstantRagdollOverkill = 50.0f;

	/** World-time seconds after the kill during which hits still count as the killing burst
	    (pellets of one blast). */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.0"))
	float OverkillWindow = 0.1f;

	/** Upper body to physics on motors, legs still animated: the body keeps its feet and
	    jerks with every hit for RiddledDuration, then drops into a full ragdoll. */
	void StartRiddled(const FHitResult& Hit, const FVector& ShotDirection, float BulletDamage);

	/** Riddled: seconds the body stays up before collapsing. 0 skips straight to ragdoll. */
	UPROPERTY(EditAnywhere, Category = "Health|Riddled", meta = (ClampMin = "0.0"))
	float RiddledDuration = 1.0f;

	/** Bone from which the upper body simulates — riddled, staggered or reacting to a hit.
	    Everything below stays animated, so the body keeps its feet. */
	UPROPERTY(EditAnywhere, Category = "Health|Riddled")
	FName RiddledRootBone = TEXT("spine_01");

	/** How hard the motors pull the simulated bones back to the animated pose. Lower is floppier. */
	UPROPERTY(EditAnywhere, Category = "Health|Riddled", meta = (ClampMin = "0.0"))
	float RiddledHoldStrength = 800.0f;

	/** Kick on the hit bone while riddled, as a multiple of the normal launch speed. */
	UPROPERTY(EditAnywhere, Category = "Health|Riddled", meta = (ClampMin = "0.0"))
	float RiddledKickScale = 1.5f;

	/** Damage landing within OverkillWindow while riddled that cuts the dance short
	    and drops straight into ragdoll — a heavy hit or a burst. */
	UPROPERTY(EditAnywhere, Category = "Health|Riddled", meta = (ClampMin = "0.0"))
	float RiddledBreakDamage = 30.0f;

	/** Death animation play rate while riddled: a slow stagger instead of a fall. */
	UPROPERTY(EditAnywhere, Category = "Health|Riddled", meta = (ClampMin = "0.0"))
	float RiddledAnimRate = 0.2f;

	/** Damage multiplier by the bone hit (the physics-asset body's bone). Bones not
	    listed take normal damage. */
	UPROPERTY(EditAnywhere, Category = "Health")
	TMap<FName, float> BoneDamageMultipliers;

	/** Death animations by the side the killing shot came from. */
	UPROPERTY(EditAnywhere, Category = "Health|Death")
	FDirectionalAnimSet DeathAnimations;

	/** Full-body slot, last in the AnimGraph, for death and stagger animations. */
	UPROPERTY(EditAnywhere, Category = "Health|Death")
	FName DeathSlotName = TEXT("DeathSlot");

	/** Damage a dying body takes after the killing blow before it goes ragdoll
	    mid-animation. */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.0"))
	float RagdollDamageThreshold = 30.0f;

	/** Launch speed, in cm/s, per point of bullet damage, for every hit on a ragdoll. */
	UPROPERTY(EditAnywhere, Category = "Health|Ragdoll", meta = (ClampMin = "0.0"))
	float LaunchSpeedPerDamage = 24.0f;

	/** Cap on one bullet's launch speed. Pellets each obey it, so a shotgun still adds up. */
	UPROPERTY(EditAnywhere, Category = "Health|Ragdoll", meta = (ClampMin = "0.0"))
	float MaxLaunchSpeedPerHit = 900.0f;

	/** Upward share of the launch, so bodies leave the ground instead of sliding. */
	UPROPERTY(EditAnywhere, Category = "Health|Ragdoll", meta = (ClampMin = "0.0"))
	float LaunchLift = 0.25f;

	/** Extra kick on the bone that was hit, as a multiple of the launch, so the body twists. */
	UPROPERTY(EditAnywhere, Category = "Health|Ragdoll", meta = (ClampMin = "0.0"))
	float BoneKickScale = 1.0f;

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

private:

	bool bIsDead = false;
	bool bIsRagdoll = false;
	bool bIsRiddled = false;
	float RiddledTimeLeft = 0.0f;

	bool bIsHitReacting = false;
	float HitReactTimeLeft = 0.0f;

	bool bIsStaggered = false;
	float StaggerTimeLeft = 0.0f;

	/** Damage in the current stagger window, and when that window opened. */
	float StaggerWindowDamage = 0.0f;
	float StaggerWindowStart = 0.0f;

	/** Damage in the current riddled burst window, and when that window opened. */
	float RiddledBurstDamage = 0.0f;
	float RiddledBurstStart = 0.0f;

	/** Overkill of the killing burst so far, and when the kill landed. */
	float BurstOverkill = 0.0f;
	float DeathTime = 0.0f;

	/** Bullet damage soaked while riddled, and the last hit — the collapse launches on them. */
	float RiddledDamage = 0.0f;
	FHitResult RiddledLastHit;
	FVector RiddledLastDirection = FVector::ZeroVector;

	/** Damage taken since health ran out, toward RagdollDamageThreshold. */
	float PostDeathDamage = 0.0f;

	/** The death animation playing, while dying and still animated. */
	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> DeathMontage;
};
