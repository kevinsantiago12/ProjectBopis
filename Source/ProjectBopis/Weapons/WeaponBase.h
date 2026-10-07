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

UENUM(BlueprintType)
enum class EWeaponFireMode : uint8
{
	Semi,
	Auto
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
	PumpShotgun
};

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
	PumpShotgun
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

/** Per-weapon reticle appearance. Radii are in UV space, where 0.5 is the widget's
    edge — keep MaxRadius comfortably below that or the ring clips.

    Each weapon may use an entirely different crosshair material. The convention is
    that any such material exposes the parameters below by name — `Radius`,
    `Thickness`, `Color` — so bloom can drive it regardless of what it draws.
    Setting a parameter a material doesn't declare is harmless, so a material is
    free to ignore any of them. */
USTRUCT(BlueprintType)
struct FCrosshairSettings
{
	GENERATED_BODY()

	/** The material drawn as the reticle. Leave unset to keep the widget's default. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crosshair")
	TObjectPtr<UMaterialInterface> Material;

	/** Reticle size in pixels; the widget is square, so this is both width and height.
	    Radius and Thickness are fractions of this, so changing it scales the whole
	    reticle uniformly — stroke weight included. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crosshair")
	float Size = 100.0f;

	/** Ring radius at zero bloom. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crosshair")
	float MinRadius = 0.12f;

	/** Ring radius at full bloom. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crosshair")
	float MaxRadius = 0.36f;

	/** Stroke width. Constant in pixels regardless of radius, since the ring is
	    drawn procedurally rather than scaled. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crosshair")
	float Thickness = 0.02f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crosshair")
	FLinearColor Color = FLinearColor::White;
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

	float GetDamageAtDistance(float Distance) const;

	EWeaponFireMode GetFireMode() const { return FireMode; }

	/** Which animation set the holder should use for this weapon. */
	UFUNCTION(BlueprintPure, Category = "Weapon")
	EWeaponAnimType GetAnimType() const { return AnimType; }

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	EAmmoType GetAmmoType() const { return AmmoType; }

	bool HasZoom() const { return bHasZoom; }
	float GetZoomedFOV() const { return ZoomedFOV; }
	bool UsesAnimationDrivenFeedback() const { return bUseAnimationDrivenFeedback; }
	FVector GetGripLocationOffset() const { return GripLocationOffset; }
	FRotator GetGripRotationOffset() const { return GripRotationOffset; }

	/** Whether enough time has passed since the last shot for this weapon to fire again. */
	UFUNCTION(BlueprintCallable, Category = "Weapon")
	bool CanFire() const;

	/** Fires the weapon. See EFireResult for why a shot may not have happened. */
	UFUNCTION(BlueprintCallable, Category = "Weapon")
	EFireResult Fire(const FVector& TraceStart, const FVector& TraceDirection);

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	int32 GetAmmoInMagazine() const { return CurrentAmmoInMagazine; }

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	int32 GetReserveAmmo() const { return CurrentReserveAmmo; }

	/** Starts a reload. Returns false if one is already running, the magazine is
	    full, or there's nothing in reserve. */
	UFUNCTION(BlueprintCallable, Category = "Weapon|Ammo")
	bool Reload();

	/** Aborts an in-progress reload without transferring ammo. */
	UFUNCTION(BlueprintCallable, Category = "Weapon|Ammo")
	void CancelReload();

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	bool CanReload() const;

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	bool IsReloading() const { return bIsReloading; }

	UFUNCTION(BlueprintPure, Category = "Weapon|Ammo")
	bool ShouldAutoReloadWhenEmpty() const { return bAutoReloadWhenEmpty; }

	UFUNCTION(BlueprintPure, Category = "Weapon|Feedback")
	FCrosshairSettings GetCrosshairSettings() const { return Crosshair; }
	void FireHitscan(const FVector& TraceStart, const FVector& SpreadDirection);
	void FireProjectile(const FVector& TraceStart, const FVector& SpreadDirection);

	float GetCurrentBloom() const { return CurrentBloom; }

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

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	EWeaponFireMode FireMode = EWeaponFireMode::Semi;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	EWeaponAnimType AnimType = EWeaponAnimType::Pistol;

	/** Minimum seconds between shots — a hard mechanical cap; tapping faster than this does nothing.
	    Should be shorter than IntendedTimeBetweenShots, which is the softer accuracy-based limit.
	    Set to 0 to disable the cap entirely. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
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

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<USoundBase> FireSound;

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
	FCrosshairSettings Crosshair;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	TObjectPtr<UMaterialInterface> HitDecalMaterial;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	FVector DecalSize = FVector(5.0f, 5.0, 5.0f);

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Feedback")
	float DecalLifeSpan = 10.0f;

	/** Accuracy cone at zero bloom - best-case spread, in degrees. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float BaseSpreadAngle = 0.5f;

	/** Accuracy cont at full bloom - worst-case spread, in degress. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float MaxSpreadAngle = 5.0f;

	/** Bloom (0-1) added per shot fired. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float BloomPerShot = 0.15f;

	/** Bloom recovered per second while not firing (after the decay delay). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float BloomDecayRate = 0.6f;

	/** Grace period after the last shot before bloom start decaying. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float BloomDecayDelay = 0.3f;

	/** Seconds between shots this weapon is "meant" to be fired at - firing sooner adds extra bloom penalty.
	    Should be longer than TimeBetweenShots, which is the hard mechanical cap. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Bloom")
	float IntendedTimeBetweenShots = 0.167f;

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

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	int32 StartingReserveAmmo = 60;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	int32 MaxReserveAmmo = 120;

	/** Reserve never depletes — for AI and debugging. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
	bool bInfiniteReserve = false;

	/** Played when the trigger is pulled on an empty magazine. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Ammo")
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

	void FinishReload();

	/** PerRound reloads: moves up to RoundsPerLoad rounds in, then re-arms itself until full or dry. */
	void LoadRound();

	/** Room in the magazine and something to fill it with. */
	bool CanAcceptRound() const;

	int32 CurrentAmmoInMagazine = 0;
	int32 CurrentReserveAmmo = 0;

	bool bIsReloading = false;
	FTimerHandle ReloadTimerHandle;

	bool bOffhandFiresNext = false;
	bool bLastShotWasOffhand = false;

	float CurrentBloom = 0.0f;
	float TimeSinceLastShot = 0.0f;


public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
