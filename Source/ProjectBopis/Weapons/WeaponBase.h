// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WeaponBase.generated.h"

class USoundBase;
class UParticleSystem;
class UMaterialInterface;
class UAnimSequence;
class AProjectileBase;
class UWeaponHolderComponent;
class UImpactEffectsData;
class UStaticMesh;

/** How enemies fire a weapon: a burst of shots at a set spacing, then a pause. */
USTRUCT(BlueprintType)
struct FAIFiringPattern
{
	GENERATED_BODY()

	/** Shots per burst (random in range). 1–1: single shots. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AI Firing", meta = (ClampMin = "1"))
	int32 BurstShotsMin = 3;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AI Firing", meta = (ClampMin = "1"))
	int32 BurstShotsMax = 5;

	/** Seconds between shots within a burst. 0: as fast as the weapon fires (TimeBetweenShots). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AI Firing", meta = (ClampMin = "0.0"))
	float ShotInterval = 0.0f;

	/** Pause after each burst (after each shot, for single shots), in seconds (random in range). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AI Firing", meta = (ClampMin = "0.0"))
	float BurstPauseMin = 0.5f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AI Firing", meta = (ClampMin = "0.0"))
	float BurstPauseMax = 1.5f;
};

/** How a weapon refills. */
UENUM(BlueprintType)
enum class EReloadStyle : uint8
{
	/** Whole magazine at once, after ReloadDuration. */
	Magazine,
	/** One round at a time — tube-fed shotguns. Each round is committed as it goes
	    in, and firing with anything loaded interrupts the reload. */
	PerRound
};

/** How a weapon is held/animated. The weapon states only which it is — each animator
    (player, and later each enemy archetype) owns its own clips for that type. */
UENUM(BlueprintType)
enum class EWeaponAnimType : uint8
{
	Pistol,
	Rifle,
	/** Two-handed long gun. Poses come from Lyra (the Shotgun Locomotion Pack was
	    rejected 2026-10-04); the montages are Lyra's shotgun clips. */
	Shotgun,
	/** Pump-action shotgun (added 2026-10-06). Same poses and reload as Shotgun, but
	    its own fire montage with a pump at the end. Map the same reload montage for both. */
	PumpShotgun,
	/** Single pistol held one-handed — free left hand at the side (2026-10-07). Pistol is
	    the two-handed hold, used by the hi-power pistol. */
	PistolOneHanded,
	/** Dual wield, one gun in each hand: dual pistols and dual SMGs (2026-10-07).
	    Pistol-style poses with the arms spread apart, so the mirrored left gun clears
	    the head from the right-shoulder camera. Its own raised idle and fire montages. */
	Dual
};

/** Pistol-style hold (one-handed, two-handed or dual, including dual SMGs), for code that
    means "pistol poses vs long-gun poses". */
inline bool IsPistolAnimType(EWeaponAnimType Type)
{
	return Type == EWeaponAnimType::Pistol
		|| Type == EWeaponAnimType::PistolOneHanded
		|| Type == EWeaponAnimType::Dual;
}

/** Which ammo a weapon takes. Each weapon keeps its own reserve; an ammo pickup of a
    type tops up the carried weapon(s) that use that type. */
UENUM(BlueprintType)
enum class EAmmoType : uint8
{
	Pistol,
	HighPowerPistol,
	SMG,
	Rifle,
	Sniper,
	AutoShotgun,
	PumpShotgun,
	Grenade,
	LauncherGrenade
};

/** Outcome of a fire attempt. Callers branch on this for feedback — a rate-limited
    click must be silent, an empty one must not be. */
UENUM(BlueprintType)
enum class EFireResult : uint8
{
	Fired,
	RateLimited,
	Empty,
	Reloading,
	NoWeapon,
	/** The muzzle is inside or behind geometry — the shot would originate on the
	    far side of whatever the character is pressed against. */
	Blocked
};

/** Moments in a weapon's handling that make a sound. Animations mark when (the
    AN_WeaponSound notify), each weapon says which sound, and the weapon plays it. */
UENUM(BlueprintType)
enum class EWeaponSound : uint8
{
	Fire,
	DryFire,
	MagOut,
	MagIn,
	/** Slide release or bolt. */
	Chamber,
	/** One shell, round or speedloader going in. */
	RoundIn,
	Pump,
	Equip
};

UCLASS()
class PROJECTBOPIS_API AWeaponBase : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AWeaponBase();

	/** Returns the weapon's mesh component **/
	USkeletalMeshComponent* GetWeaponMesh() const { return WeaponMesh; };

	/** World location of the muzzle socket — where shots actually leave from. */
	FVector GetMuzzleLocation() const;

	/** World transform of a muzzle socket — its X axis runs down the barrel. The main-hand
	    mesh's, or the off-hand's for duals. (Not "the firing mesh": aim correction wants a
	    steady gun, not the alternating one.) */
	FTransform GetMuzzleTransform(bool bOffhand = false) const;

	/** Dual-wield weapons carry a second mesh in the other hand and alternate shots between them. */
	bool IsDualWield() const { return bDualWield; }

	/** Whether the next shot leaves from the off-hand weapon. GetMuzzleLocation follows this. */
	bool IsOffhandNext() const { return bDualWield && bOffhandFiresNext; }

	/** Which hand fired the most recent shot — the holder picks the matching arm animation. */
	bool WasLastShotOffhand() const { return bLastShotWasOffhand; }

	USkeletalMeshComponent* GetOffhandMesh() const { return OffhandMesh; }
	FVector GetOffhandGripLocationOffset() const { return OffhandGripLocationOffset; }
	FRotator GetOffhandGripRotationOffset() const { return OffhandGripRotationOffset; }

	float GetMaxRange() const { return MaxRange; }

	/** How fast this weapon's rounds travel (cm/s); 0 for hitscan, which arrives instantly. */
	float GetProjectileSpeed() const;

	const FAIFiringPattern& GetAIFiring() const { return AIFiring; }

	float GetDamageAtDistance(float Distance) const;

	float GetTimeBetweenShots() const { return TimeBetweenShots; }

	/** Which animation set the holder should use for this weapon. */
	UFUNCTION(BlueprintPure, Category = "Weapon")
	EWeaponAnimType GetAnimType() const { return AnimType; }

	UFUNCTION(BlueprintPure, Category = "Weapon")
	int32 GetWeaponSlot() const { return WeaponSlot; }

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	EAmmoType GetAmmoType() const { return AmmoType; }

	bool HasZoom() const { return bHasZoom; }
	float GetZoomedFOV() const { return ZoomedFOV; }
	bool UsesAnimationDrivenFeedback() const { return bUseAnimationDrivenFeedback; }

	/** Plays one of this weapon's sounds on the gun: the main-hand mesh, or the off-hand
	    one for duals. Owned by the weapon, so a cue's per-shooter voice limit counts per gun.
	    Silent if the weapon has no sound for it. */
	UFUNCTION(BlueprintCallable, Category = "Weapon|Sounds")
	void PlayWeaponSound(EWeaponSound Sound, bool bOffhand = false);
	FVector GetGripLocationOffset() const { return GripLocationOffset; }
	FRotator GetGripRotationOffset() const { return GripRotationOffset; }

	/** Whether enough time has passed since the last shot for this weapon to fire again. */
	UFUNCTION(BlueprintCallable, Category = "Weapon")
	bool CanFire() const;

	/** Fires the weapon. See EFireResult for why a shot may not have happened.
	    bExact: the round flies exactly down TraceDirection — no bloom scatter. For shooters
	    that place their own shots (enemies); pellets still fan out. */
	UFUNCTION(BlueprintCallable, Category = "Weapon")
	EFireResult Fire(const FVector& TraceStart, const FVector& TraceDirection, bool bExact = false);

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	int32 GetAmmoInMagazine() const { return CurrentAmmoInMagazine; }

	/** Rounds left in the holder's shared pool for this weapon's ammo type. 0 when not
	    carried (no pool to draw from). */
	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	int32 GetReserveAmmo() const;

	/** Rounds this weapon brings into the pool when it's picked up. */
	int32 GetStartingReserveAmmo() const { return StartingReserveAmmo; }

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	int32 GetMagazineSize() const { return MagazineSize; }

	/** Loads the magazine directly (clamped to its size) — for a weapon picked up with a
	    given number of rounds rather than a full magazine. */
	void SetAmmoInMagazine(int32 Rounds) { CurrentAmmoInMagazine = FMath::Clamp(Rounds, 0, MagazineSize); }

	/** The dual-wield version of this weapon, if it has one. */
	TSubclassOf<AWeaponBase> GetDualWieldClass() const { return DualWieldClass; }

	/** The class a dropped copy of this weapon should be: DropAsClass, or its own. */
	TSubclassOf<AWeaponBase> GetDropClass() const { return DropAsClass ? DropAsClass : TSubclassOf<AWeaponBase>(GetClass()); }

	const UImpactEffectsData* GetImpactEffects() const { return ImpactEffects; }

	/** For a dual-wield weapon, its single version, if it has one. */
	TSubclassOf<AWeaponBase> GetSingleWieldClass() const { return SingleWieldClass; }

	/** The pool this weapon reloads from. Set by the holder when the weapon is added. */
	void SetReserveSource(UWeaponHolderComponent* Source) { ReserveSource = Source; }

	/** Starts a reload, Speed times as fast (timers divided by it; 1 = as tuned). Returns
	    false if one is already running, the magazine is full, or there's nothing in reserve. */
	UFUNCTION(BlueprintCallable, Category = "Weapon|Ammo")
	bool Reload(float Speed = 1.0f);

	/** Aborts an in-progress reload without transferring ammo. */
	UFUNCTION(BlueprintCallable, Category = "Weapon|Ammo")
	void CancelReload();

	/** How far through the current reload, 0..1 (0 if none). Per-round reloads count the
	    wind-up and each round as they come; it's only used for magazine reloads. */
	float GetReloadProgress() const;

	/** Finishes a reload on the spot: a magazine fills now; a per-round weapon gets the cycle
	    that was under way. (A roll that carried the reload through.) */
	void CompleteReloadNow();

	bool IsMagazineReload() const { return ReloadStyle == EReloadStyle::Magazine; }

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	bool CanReload() const;

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	bool IsReloading() const { return bIsReloading; }

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	bool ShouldAutoReloadWhenEmpty() const { return bAutoReloadWhenEmpty; }

	void FireHitscan(const FVector& TraceStart, const FVector& SpreadDirection);
	void FireProjectile(const FVector& TraceStart, const FVector& SpreadDirection);

	/** Actors this weapon's rounds pass straight through: when an enemy with friendly fire off
	    fires, every other enemy — pellets and rounds in flight included. */
	void GetFriendlyActors(TArray<AActor*>& OutFriends) const;

	/** The cone a shot goes out in right now, in degrees: Spread, widened by a long burst and
	    by the holder moving, tightened by Focus. */
	float GetCurrentSpread() const;

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<USkeletalMeshComponent> WeaponMesh;

	/** The second weapon of a dual-wield pair. Unused unless bDualWield is set; the holder
	    attaches it to the off hand. Shares this weapon's ammo, bloom and fire rate. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon|Dual Wield")
	TObjectPtr<USkeletalMeshComponent> OffhandMesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Dual Wield")
	bool bDualWield = false;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Dual Wield",
		meta = (EditCondition = "bDualWield"))
	FVector OffhandGripLocationOffset = FVector::ZeroVector;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Dual Wield",
		meta = (EditCondition = "bDualWield"))
	FRotator OffhandGripRotationOffset = FRotator::ZeroRotator;

	/** The mesh the next (or, after firing, the current) shot belongs to. */
	USkeletalMeshComponent* GetFiringMesh() const;

	USoundBase* GetSound(EWeaponSound Sound) const;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	EWeaponAnimType AnimType = EWeaponAnimType::Pistol;

	/** Number key that selects this weapon (Max Payne style categories). Weapons that share
	    a slot are cycled by pressing the key again, in pickup order. 2 pistols, 3 shotguns,
	    4 SMGs and rifles, 5 sniper; 1 is kept free for melee. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "1", ClampMax = "9"))
	int32 WeaponSlot = 2;

	/** The dual-wield version of this weapon (e.g. BP_Pistol → BP_DualPistols). Picking up
	    this weapon again while carrying it unlocks the dual version as a separate selection.
	    Leave empty for weapons that can't be dual-wielded. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TSubclassOf<AWeaponBase> DualWieldClass;

	/** What this weapon turns into when an enemy drops it. Empty: itself. For enemy-only
	    variants (e.g. a pistol with an enemy animation type) that should drop as the
	    ordinary weapon the player picks up. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Drop")
	TSubclassOf<AWeaponBase> DropAsClass;

	/** For a dual-wield weapon: its single version (e.g. BP_DualPistols → BP_Pistol).
	    Carrying the pair always includes one, so adding this weapon also adds the single
	    if it's missing. Leave empty on single weapons. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TSubclassOf<AWeaponBase> SingleWieldClass;

	/** Seconds between shots: the weapon's rate of fire. Holding the trigger fires at exactly
	    this pace, and pulling it faster gets no more out of it (Max Payne). 0: no limit. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon", meta = (ClampMin = "0.0"))
	float TimeBetweenShots = 0.125f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float BaseDamage = 10.0f;

	/** Distance from the muzzle at which damage starts to drop. Falloff is off
	    unless FalloffEndRange is greater than this. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Damage", meta = (ClampMin = "0.0"))
	float FalloffStartRange = 0.0f;

	/** Distance at which damage bottoms out at MinDamageMultiplier. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Damage", meta = (ClampMin = "0.0"))
	float FalloffEndRange = 0.0f;

	/** Fraction of BaseDamage dealt at and beyond FalloffEndRange. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Damage", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MinDamageMultiplier = 1.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float MaxRange = 5000.0f;

	/** How far the shot is heard (cm) — enemies within it are alerted. 0: silent. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|AI", meta = (ClampMin = "0.0"))
	float NoiseRange = 3000.0f;

	/** How enemies fire this weapon. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|AI")
	FAIFiringPattern AIFiring;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	bool bHasZoom = false;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float ZoomedFOV = 40.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	bool bIsProjectileWeapon = false;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	TSubclassOf<AProjectileBase> ProjectileClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	FVector GripLocationOffset = FVector::ZeroVector;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	FRotator GripRotationOffset = FRotator::ZeroRotator;

	/** Each shot, from the muzzle. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Sounds")
	TObjectPtr<USoundBase> FireSound;

	/** Handling sounds, played when animations call for them (AN_WeaponSound). Empty: silent. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Sounds")
	TObjectPtr<USoundBase> MagOutSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Sounds")
	TObjectPtr<USoundBase> MagInSound;

	/** Slide release or bolt. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Sounds")
	TObjectPtr<USoundBase> ChamberSound;

	/** One shell, round or speedloader going in. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Sounds")
	TObjectPtr<USoundBase> RoundInSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Sounds")
	TObjectPtr<USoundBase> PumpSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Sounds")
	TObjectPtr<USoundBase> EquipSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<UParticleSystem> MuzzleFlash;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	FName MuzzleSocketName = TEXT("Muzzle");

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	bool bUseAnimationDrivenFeedback = false;

	/** Played on the weapon's own mesh when firing, if this weapon uses animation-driven feedback. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<UAnimSequence> FireAnimation;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<UMaterialInterface> HitDecalMaterial;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	FVector DecalSize = FVector(5.0f, 5.0, 5.0f);

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	float DecalLifeSpan = 10.0f;

	/** Per-surface impact bursts and decals. When set, replaces HitDecalMaterial for this
	    weapon's hits — hitscan and projectiles alike. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Impact")
	TObjectPtr<UImpactEffectsData> ImpactEffects;

	/** The spent casing this weapon throws from CasingSocketName (AmmoSet: the calibre's
	    _Cartridge, cal12Gauge_Used for shotguns). Empty: no casings. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings")
	TObjectPtr<UStaticMesh> CasingMesh;

	/** Size of the thrown casing: 1 is the mesh as authored. Its physics body scales with it. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings", meta = (ClampMin = "0.01"))
	float CasingScale = 1.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings")
	FName CasingSocketName = TEXT("AmmoEject");

	/** Seconds after the shot the casing comes out. 0: with the shot. A pump-action: as it racks. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings", meta = (ClampMin = "0.0"))
	float CasingEjectDelay = 0.0f;

	/** Throw speed, cm/s, out to the gun's right (plus the shooter's own velocity). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings", meta = (ClampMin = "0.0"))
	float CasingEjectSpeed = 250.0f;

	/** How much of the throw goes up, and back over the shoulder, against the sideways part. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings")
	float CasingEjectUp = 0.6f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings")
	float CasingEjectBack = 0.2f;

	/** Variety: the throw's direction within this cone (degrees), its speed ± this fraction. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings", meta = (ClampMin = "0.0"))
	float CasingEjectSpread = 15.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float CasingSpeedVariation = 0.25f;

	/** Tumble: up to this many degrees per second, about a random axis. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings", meta = (ClampMin = "0.0"))
	float CasingSpin = 1080.0f;

	/** Seconds a casing stays in the world. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings", meta = (ClampMin = "0.1"))
	float CasingLifeSpan = 10.0f;

	/** Played on a casing's first few bounces. Empty: silent. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Casings")
	TObjectPtr<USoundBase> CasingImpactSound;

	/** The cone a shot goes out in, in degrees. Max Payne's guns are accurate: keep it small. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Accuracy", meta = (ClampMin = "0.0"))
	float Spread = 0.5f;

	/** Spread multiplier with the holder moving at MovingSpreadFullSpeed and up (×1 standing
	    still, in between at lower speeds). Not mid-dive: a shootdodge is as true as standing. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Accuracy", meta = (ClampMin = "1.0"))
	float MovingSpreadMultiplier = 1.5f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Accuracy", meta = (ClampMin = "1.0"))
	float MovingSpreadFullSpeed = 400.0f;

	/** Extra spread (degrees) a long burst wanders to, reached after SustainedSpreadTime of
	    unbroken fire; letting go of the trigger starts the next burst clean. 0 for pistols
	    and shotguns. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Accuracy", meta = (ClampMin = "0.0"))
	float SustainedSpread = 0.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Accuracy", meta = (ClampMin = "0.01"))
	float SustainedSpreadTime = 1.0f;

	/** Traces fired per shot. 1 for every single-shot weapon; a shotgun's pellet
	    count. BaseDamage applies per pellet. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Pellets", meta = (ClampMin = "1"))
	int32 PelletsPerShot = 1;

	/** Fixed cone, in degrees, the pellets spread across around the shot's aim point.
	    Independent of bloom: bloom moves where the pattern lands, this sets how wide it is. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Pellets", meta = (ClampMin = "0.0"))
	float PelletSpreadAngle = 0.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	int32 MagazineSize = 12;

	/** The ammo this weapon takes. Pickups of this type refill its reserve. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	EAmmoType AmmoType = EAmmoType::Pistol;

	/** Rounds added to the holder's shared pool when this weapon is picked up. The cap
	    lives on the holder, per ammo type. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	int32 StartingReserveAmmo = 60;

	/** Reserve never depletes — for AI and debugging. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	bool bInfiniteReserve = false;

	/** Played when the trigger is pulled on an empty magazine. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Sounds")
	TObjectPtr<USoundBase> DryFireSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	EReloadStyle ReloadStyle = EReloadStyle::Magazine;

	/** Seconds a reload takes. Tune to match the holder's reload montage; the timer
	    is authoritative, not the animation. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo",
		meta = (EditCondition = "ReloadStyle == EReloadStyle::Magazine", EditConditionHides))
	float ReloadDuration = 2.0f;

	/** Seconds from starting the reload to the first round going in — bringing the
	    weapon into the loading position. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo",
		meta = (EditCondition = "ReloadStyle == EReloadStyle::PerRound", EditConditionHides, ClampMin = "0.0"))
	float ReloadStartDelay = 0.4f;

	/** Seconds per round loaded. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo",
		meta = (EditCondition = "ReloadStyle == EReloadStyle::PerRound", EditConditionHides, ClampMin = "0.05"))
	float TimePerRound = 0.5f;

	/** Rounds loaded per load cycle — one TimePerRound tick, and one pass of the
	    reload montage's Loop section. A cycle stops short if the magazine fills or
	    the reserve runs out partway through. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo",
		meta = (EditCondition = "ReloadStyle == EReloadStyle::PerRound", EditConditionHides, ClampMin = "1"))
	int32 RoundsPerLoad = 1;

	/** Whether firing on an empty magazine should start a reload by itself. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	bool bAutoReloadWhenEmpty = false;

	/** Throws one spent casing from the ejection port of the main or off-hand gun. */
	void EjectCasing(bool bOffhand);

	void FinishReload();

	/** PerRound reloads: moves up to RoundsPerLoad rounds in, then re-arms itself until full or dry. */
	void LoadRound();

	/** Room in the magazine and something to fill it with. */
	bool CanAcceptRound() const;

	int32 CurrentAmmoInMagazine = 0;

	UPROPERTY(Transient)
	TObjectPtr<UWeaponHolderComponent> ReserveSource;

	/** Takes up to Wanted rounds from the pool (all of them with an infinite reserve). */
	int32 TakeReserve(int32 Wanted);

	bool bIsReloading = false;
	FTimerHandle ReloadTimerHandle;

	/** The running reload's speed (see Reload). */
	float ReloadSpeed = 1.0f;

	bool bOffhandFiresNext = false;
	bool bLastShotWasOffhand = false;

	/** Seconds of unbroken fire so far: how long the current burst has run. */
	float BurstTime = 0.0f;
	float TimeSinceLastShot = 0.0f;


public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
