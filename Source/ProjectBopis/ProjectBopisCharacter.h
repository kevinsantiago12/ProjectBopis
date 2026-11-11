// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "BopisCharacterBase.h"
#include "Logging/LogMacros.h"
#include "ProjectBopisCharacter.generated.h"

class UPlayerHUDWidget;
class UWeaponWheelWidget;
class UInputComponent;
class USkeletalMeshComponent;
class USpringArmComponent;
class UCameraComponent;
class UInputAction;
class UFocusComponent;
class UShootdodgeComponent;
class URollComponent;
class UGamepadAimComponent;
class UKillCamComponent;
class UInteractComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UPostProcessComponent;
class AGrenade;
class UCameraShakeBase;
class USoundBase;
struct FInputActionValue;

DECLARE_LOG_CATEGORY_EXTERN(LogTemplateCharacter, Log, All);

/** A direction marker on the HUD: where a shot came from, and whether it hit. */
struct FHitIndicator
{
	FVector Source = FVector::ZeroVector;
	float StartTime = 0.0f;
	float Duration = 1.0f;
	int32 Sector = 0;
	bool bHit = false;
};

/** Which rotation/movement rules currently apply. Mutually exclusive by design —
    the underlying flags fight each other if more than one is active. */
UENUM(BlueprintType)
enum class EMovementStance : uint8
{
	/** Camera-relative input; character turns to face travel. */
	FreeRun,
	/** Camera-relative input; character faces the camera and strafes. */
	Aiming,
	/** Rotation authority handed to the animation (prone turn-in-place). Not yet reachable. */
	AnimationDriven
};

/** What the G key does, picked on the weapon wheel's slot 1. */
UENUM(BlueprintType)
enum class EQuickAction : uint8
{
	Grenade,
	Melee
};

/** One melee strike: the blow, the swing's whoosh and the thud when it connects. */
USTRUCT(BlueprintType)
struct FMeleeStrike
{
	GENERATED_BODY()

	/** Additive, played on MeleeSlotName over whatever the body is doing. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melee")
	TObjectPtr<UAnimSequenceBase> Animation;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melee")
	TObjectPtr<USoundBase> SwingSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melee")
	TObjectPtr<USoundBase> HitSound;
};

/**
 *  The player character: camera, input, third-person movement stances, crouch and Focus.
 *  Weapon carrying and its animation are shared with enemies in ABopisCharacterBase.
 */
UCLASS(abstract)
class AProjectBopisCharacter : public ABopisCharacterBase
{
	GENERATED_BODY()

	/** Third person camera boom — owns control rotation, distance and wall collision */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	USpringArmComponent* CameraBoom;

	/** Third person camera, mounted at the end of the boom */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UCameraComponent* FollowCamera;

	/** Focus (slow motion) — meter, toggle and world slow-down. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UFocusComponent> Focus;

	/** The Max Payne dive. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UShootdodgeComponent> Shootdodge;

	/** Dodge roll. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<URollComponent> Roll;

	/** The controller's aim: stick turning and soft lock. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UGamepadAimComponent> GamepadAim;

	/** The slow-motion swing round the body of the kill that ends a fight. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UKillCamComponent> KillCam;

	/** The Interact button: picks the inspect in front of the player and shows its prompt. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UInteractComponent> Interaction;

	/** The Focus look (desaturate, vignette…). Unbound; Focus drives its weight. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UPostProcessComponent> FocusPostProcess;

	/** Widget class to spawn for the player HUD */
	UPROPERTY(EditDefaultsOnly, Category = "UI")
	TSubclassOf<UPlayerHUDWidget> HUDWidgetClass;

protected:

	/** Jump Input Action */
	UPROPERTY(EditAnywhere, Category ="Input")
	UInputAction* JumpAction;

	/** Move Input Action */
	UPROPERTY(EditAnywhere, Category ="Input")
	UInputAction* MoveAction;

	/** Look Input Action */
	UPROPERTY(EditAnywhere, Category ="Input")
	class UInputAction* LookAction;

	/** Mouse Look Input Action */
	UPROPERTY(EditAnywhere, Category ="Input")
	class UInputAction* MouseLookAction;

	/** Fire Input Action **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* FireAction;

	/** Aim Input Action **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* AimAction;

	/** Reload Input Action **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* ReloadAction;

	/** Crouch Input Action **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* CrouchAction;

	/** Weapon slot keys: element 0 selects slot 1 (key 1), element 1 slot 2, and so on. */
	UPROPERTY(EditAnywhere, Category = "Input")
	TArray<UInputAction*> WeaponSlotActions;

	/** Focus toggle Input Action **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* FocusAction;

	/** Shootdodge Input Action **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* ShootdodgeAction;

	/** Dodge roll Input Action **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* RollAction;

	/** The G key: a grenade or a melee strike, whichever QuickAction is (see DoQuickAction). **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* GrenadeAction;

	/** First aid: tap to use a kit. */
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* HealAction;

	/** Interact: inspect what the prompt shows. */
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* InteractAction;

	/** Shoulder swap: the camera moves over the other shoulder (a toggle). */
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* ShoulderSwapAction;

	/** Weapon wheel: hold to open, release to equip what's pointed at. The number keys keep
	    working beside it; the wheel is there for a controller. */
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* WeaponWheelAction;

	/** Weapon wheel: steps the hovered type's weapon (mouse wheel, D-pad up/down as ±1). */
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* WeaponWheelCycleAction;

	/** The wheel widget: the C++ class, or a Blueprint child restyled in the editor. */
	UPROPERTY(EditDefaultsOnly, Category = "UI")
	TSubclassOf<UWeaponWheelWidget> WeaponWheelClass;

	/** Slow motion while the wheel is open (a free Focus, no meter cost). */
	UPROPERTY(EditDefaultsOnly, Category = "UI")
	bool bWeaponWheelSlowMotion = true;

	/** True: tap to toggle crouch. False: hold to stay crouched.
	    Eventually belongs in player settings — BlueprintReadWrite so an options
	    menu can drive it later without a C++ change. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input")
	bool bCrouchIsToggle = true;

	/** True: moving clears the crouch request, so stopping leaves the character standing.
	    False: the request survives movement, and the character drops back into the crouch
	    whenever they stop. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input")
	bool bMovementCancelsCrouch = false;

	/** Crouched, the character takes a firing stance: the weapon comes up and stays up,
	    facing the camera (no aim zoom — that's still the aim button), and the camera eases
	    down by CrouchCameraOffset. Off: crouching leaves the weapon as it was and the camera
	    at standing height. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Crouch")
	bool bCrouchCombatStance = true;

	/** Red markers toward whoever just hit you. */
	UPROPERTY(EditAnywhere, Category = "Combat|Hit Indicators")
	bool bShowHitIndicators = true;

	/** Grey markers toward shots that crack past. */
	UPROPERTY(EditAnywhere, Category = "Combat|Hit Indicators")
	bool bShowNearMissIndicators = true;

	/** Near misses only from shooters off screen — the ones you can see need no marker. */
	UPROPERTY(EditAnywhere, Category = "Combat|Hit Indicators")
	bool bNearMissOnlyOffScreen = true;

	/** Real seconds a marker takes to fade out. */
	UPROPERTY(EditAnywhere, Category = "Combat|Hit Indicators", meta = (ClampMin = "0.1"))
	float HitIndicatorDuration = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Combat|Hit Indicators", meta = (ClampMin = "0.1"))
	float NearMissIndicatorDuration = 0.6f;

	/** Directions are grouped into this many sectors around you; a new shot from a sector that
	    already shows a marker refreshes it instead of adding another. */
	UPROPERTY(EditAnywhere, Category = "Combat|Hit Indicators", meta = (ClampMin = "4", ClampMax = "36"))
	int32 HitIndicatorSectors = 12;

	/** Most grey markers at once, and how soon one sector can show another. */
	UPROPERTY(EditAnywhere, Category = "Combat|Hit Indicators", meta = (ClampMin = "0"))
	int32 MaxNearMissIndicators = 3;

	UPROPERTY(EditAnywhere, Category = "Combat|Hit Indicators", meta = (ClampMin = "0.0"))
	float NearMissIndicatorCooldown = 0.5f;

	/** Max walk speed when not aiming. */
	UPROPERTY(EditAnywhere, Category = "Movement")
	float FreeRunSpeed = 500.0f;

	/** Max walk speed while the aim button is held. Hip-fire strafing uses FreeRunSpeed. */
	UPROPERTY(EditAnywhere, Category = "Movement")
	float AimingSpeed = 250.0f;

	/** How quickly the character turns to face travel in FreeRun. Yaw only. */
	UPROPERTY(EditAnywhere, Category = "Movement")
	float FreeRunRotationRate = 360.0f;

	/** How fast the body turns to the camera when the gun comes up facing elsewhere (firing
	    from the lowered stance, out of a roll), in degrees per second — a quick turn rather
	    than a snap. 0: snaps. */
	UPROPERTY(EditAnywhere, Category = "Movement", meta = (ClampMin = "0.0"))
	float AimTurnRate = 1080.0f;

	/** Max walk speed while crouched. Normally unused — moving stands the character up —
	    but applies if a low ceiling blocks the uncrouch. */
	UPROPERTY(EditAnywhere, Category = "Movement")
	float CrouchedSpeed = 170.0f;

	/** Boom length when not aiming. */
	UPROPERTY(EditAnywhere, Category = "Camera")
	float HipArmLength = 300.0f;

	/** Boom length while aiming — closer over the shoulder. */
	UPROPERTY(EditAnywhere, Category = "Camera")
	float AimArmLength = 140.0f;

	/** Boom socket offset when not aiming. */
	UPROPERTY(EditAnywhere, Category = "Camera")
	FVector HipSocketOffset = FVector(0.0f, 50.0f, 0.0f);

	/** Boom socket offset while aiming — further right, slightly higher. */
	UPROPERTY(EditAnywhere, Category = "Camera")
	FVector AimSocketOffset = FVector(0.0f, 65.0f, 15.0f);

	/** How fast the camera settles between hip and aim. Higher is snappier. */
	UPROPERTY(EditAnywhere, Category = "Camera")
	float CameraTransitionSpeed = 12.0f;

	/** Camera height change while crouched in the combat stance (bCrouchCombatStance),
	    eased in and out. Negative lowers it with the crouch; 0 keeps it at standing height. */
	UPROPERTY(EditAnywhere, Category = "Camera")
	float CrouchCameraOffset = -40.0f;

	/** Extra camera height while shootdodging (diving, landing, prone), eased in and out.
	    Negative lowers it toward the body lying near the floor. */
	UPROPERTY(EditAnywhere, Category = "Camera|Shootdodge")
	float ShootdodgeCameraHeight = -60.0f;

	/** Boom length while shootdodging. */
	UPROPERTY(EditAnywhere, Category = "Camera|Shootdodge")
	float ShootdodgeArmLength = 300.0f;

	/** Boom socket offset while shootdodging. */
	UPROPERTY(EditAnywhere, Category = "Camera|Shootdodge")
	FVector ShootdodgeSocketOffset = FVector(0.0f, 50.0f, 0.0f);

	/** Pulls boom length, offset and FOV toward whatever the current state implies. */
	void UpdateCameraTransition(float DeltaSeconds);

	/** Applies the rotation/speed rules for a stance. Single place the flag pair is set. */
	void ApplyMovementStance(EMovementStance NewStance);

	/** Picks the stance the current state implies and applies it on change. */
	void UpdateMovementStance();

	/** Crouches while stationary and the request holds; stands up the moment input moves the character. */
	void UpdateCrouch();

	EMovementStance CurrentStance = EMovementStance::FreeRun;
	
public:
	AProjectBopisCharacter();

	/** The weapon wheel is up (HUD elements hide under it — the crosshair). */
	bool IsWeaponWheelOpen() const;

	/** The kill cam has the view: no moving, looking or anything but shooting and reloading. */
	bool IsInKillCam() const;

protected:

	/** Called from Input Actions for movement input */
	void MoveInput(const FInputActionValue& Value);

	/** Called from Input Actions for looking input */
	void LookInput(const FInputActionValue& Value);

	/** The right stick's look: as LookInput, except that the open wheel points where the stick points. */
	void StickLookInput(const FInputActionValue& Value);

	/** Handles aim inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoAim(float Yaw, float Pitch);

	/** Handles move inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoMove(float Right, float Forward);

	/** Handles jump start inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoJumpStart();

	/** Handles jump end inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoJumpEnd();

	/**Handle fire inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoFire();

	/** Handles the trigger being held down — only continues firing for full-auto weapons. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoFireHeld();

	/** The trigger let go: a click that picked from the wheel can fire again. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoFireReleased();

	/** Handles reload inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoReload();

	/** Selects a weapon slot (1-based) from a number key. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoSelectWeaponSlot(int32 Slot);

	/** Equips one carried weapon (the wheel's pick), with the number keys' gating. */
	void DoSelectWeapon(AWeaponBase* Weapon);

	/** The weapon wheel. Keyboard: a number key opens it in key mode (that type highlighted;
	    more keys move it, the same type steps its weapons) and a click equips. Pad/held key:
	    held open in pointer mode (look steers), released to pick. While open, combat input
	    and the camera are blocked (movement stays) and time runs slow. */
	void OpenWeaponWheel(bool bKeyMode);
	void CloseWeaponWheel(bool bEquip);
	void DoWeaponWheelStart();
	void DoWeaponWheelEnd();
	void WeaponWheelCycleInput(const FInputActionValue& Value);

	UPROPERTY(Transient)
	TObjectPtr<UWeaponWheelWidget> WeaponWheel;

	/** The wheel's slow motion is a free Focus it started (ended when it closes). */
	bool bWheelOwnsFocus = false;

	/** The fire click that picked from the key-mode wheel is still held down: it never fires. */
	bool bWheelPickHeld = false;

	/** Toggles Focus from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoToggleFocus();

	/** Starts a shootdodge from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoShootdodge();

	/** Starts a dodge roll from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoRoll();

	/** The G key: throws a grenade or strikes, by QuickAction. Out of grenades it does nothing
	    (no fallback to melee). */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoQuickAction();

	/** Throws a grenade from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoThrowGrenade();

	/** Strikes with the gun in hand: the enemy in reach nearest the aim is hit and staggered. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoMelee();

	/** Uses a first-aid kit from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoHeal();

	/** Interact pressed: uses what the prompt shows. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoInteract();

	/** Shoulder swap pressed: the camera goes over the other shoulder. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoShoulderSwap();

	/** Crouch key pressed. Records the crouch request (toggle or hold, per bCrouchIsToggle);
	    UpdateCrouch decides whether the character is actually down. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoCrouchStart();

	/** Crouch key released. Only meaningful in hold mode. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoCrouchEnd();

	/** Handles aim-start inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoAimStart();

	/** Handles aim-end inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoAimEnd();


protected:

	virtual void BeginPlay() override;

	virtual void Tick(float DeltaSeconds) override;

	virtual void Landed(const FHitResult& Hit) override;

	virtual void OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;
	virtual void OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;

	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
		AController* EventInstigator, AActor* DamageCauser) override;

	virtual void Die(AController* Killer, const FVector& ShotDirection) override;

	/** No death animation for a body that's diving or lying down: it goes straight to ragdoll. */
	virtual bool PlayDeathAnimation(const FVector& ShotDirection) override;

	/** Real seconds from death to the level reloading (slow motion doesn't stretch it). */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.0"))
	float DeathRestartDelay = 3.0f;

	/** Real seconds of fade to black after DeathRestartDelay, before the level reloads. */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.0"))
	float RestartFadeTime = 0.6f;

	/** Real seconds of slow motion when the player dies. 0 turns it off. */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.0"))
	float DeathSlowMoDuration = 2.0f;

	/** World speed during the death slow motion. */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float DeathTimeDilation = 0.2f;

	/** First-aid kits carried at the start. They live in the ammo pool (EAmmoType::FirstAid), so
	    the holder's MaxAmmoByType caps them and ammo pickups of that type add to them. */
	UPROPERTY(EditAnywhere, Category = "Health|First Aid", meta = (ClampMin = "0"))
	int32 StartingFirstAidKits = 0;

	/** Share of max health one kit gives back, capped at full. */
	UPROPERTY(EditAnywhere, Category = "Health|First Aid", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float FirstAidHealFraction = 0.5f;

	/** Played as the kit is used — 2D, it's the player's own. */
	UPROPERTY(EditAnywhere, Category = "Health|First Aid")
	TObjectPtr<USoundBase> FirstAidSound;

	/** The white flash on use: how white it starts (0..1) and how long it takes to clear. */
	UPROPERTY(EditAnywhere, Category = "Health|First Aid", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float FirstAidFlashAlpha = 0.6f;

	UPROPERTY(EditAnywhere, Category = "Health|First Aid", meta = (ClampMin = "0.0"))
	float FirstAidFlashDuration = 0.3f;

	/** The damage flash's colour: 0 black, 1 full red. */
	UPROPERTY(EditAnywhere, Category = "Health|Damage Flash", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float DamageFlashRed = 0.6f;

	/** A flash when this much of full health (0..1) is lost within HeavyDamageWindow. */
	UPROPERTY(EditAnywhere, Category = "Health|Damage Flash", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float HeavyDamageFraction = 0.25f;

	/** World seconds the damage is added up over. */
	UPROPERTY(EditAnywhere, Category = "Health|Damage Flash", meta = (ClampMin = "0.0"))
	float HeavyDamageWindow = 1.0f;

	/** The heavy-damage flash: how strong it starts (0..1) and how long it takes to clear (real seconds). */
	UPROPERTY(EditAnywhere, Category = "Health|Damage Flash", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float HeavyDamageFlashAlpha = 0.4f;

	UPROPERTY(EditAnywhere, Category = "Health|Damage Flash", meta = (ClampMin = "0.0"))
	float HeavyDamageFlashDuration = 0.4f;

	/** The death flash, the same way. */
	UPROPERTY(EditAnywhere, Category = "Health|Damage Flash", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float DeathFlashAlpha = 0.7f;

	UPROPERTY(EditAnywhere, Category = "Health|Damage Flash", meta = (ClampMin = "0.0"))
	float DeathFlashDuration = 0.8f;

	/** Hit pulse: every hit taken reddens the screen's edges for a moment, stronger the bigger
	    the hit. A post-process material with a scalar Intensity and a vector PulseColor. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Pulse")
	TObjectPtr<UMaterialInterface> HitPulseMaterial;

	/** The weakest pulse (0..1): a graze still shows. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Pulse", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float HitPulseMin = 0.35f;

	/** How much stronger per share of full health a hit takes: a hit of 10% adds 0.1 x this. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Pulse", meta = (ClampMin = "0.0"))
	float HitPulsePerHealth = 4.0f;

	/** Real seconds the pulse takes to fade from full. */
	UPROPERTY(EditAnywhere, Category = "Health|Hit Pulse", meta = (ClampMin = "0.01"))
	float HitPulseFadeTime = 0.3f;

	/** Low health: below this share of full health the screen's edges stay red and the colour
	    drains toward grey, more the lower it goes (all of it at none). Drives M_HitPulse's
	    LowHealth and LowHealthBeat. */
	UPROPERTY(EditAnywhere, Category = "Health|Low Health", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float LowHealthFraction = 0.2f;

	/** How fast the effect follows health (a heal fades it, a hit deepens it). */
	UPROPERTY(EditAnywhere, Category = "Health|Low Health", meta = (ClampMin = "0.1"))
	float LowHealthBlendSpeed = 3.0f;

	/** The red edge throbs like a heartbeat: beats per second at the threshold, and near death. */
	UPROPERTY(EditAnywhere, Category = "Health|Low Health", meta = (ClampMin = "0.0"))
	float LowHealthBeatRateMin = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Health|Low Health", meta = (ClampMin = "0.0"))
	float LowHealthBeatRateMax = 2.0f;

	/** How much of the red edge each beat takes away between beats (0: steady). */
	UPROPERTY(EditAnywhere, Category = "Health|Low Health", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float LowHealthThrob = 0.4f;

	/** Below LowHealthFraction and out of combat for OutOfCombatDelay, health slowly comes back
	    up to that line, and the low-health look fades with it. Never past it: that's the
	    first-aid kits' job. */
	UPROPERTY(EditAnywhere, Category = "Health|Recovery")
	bool bRecoverOutOfCombat = true;

	/** World seconds out of combat (no shot fired, no hit taken, no near miss) before it starts. */
	UPROPERTY(EditAnywhere, Category = "Health|Recovery", meta = (ClampMin = "0.0", EditCondition = "bRecoverOutOfCombat"))
	float OutOfCombatDelay = 5.0f;

	/** Share of full health recovered per world second. */
	UPROPERTY(EditAnywhere, Category = "Health|Recovery", meta = (ClampMin = "0.0", EditCondition = "bRecoverOutOfCombat"))
	float RecoverRate = 0.02f;

	/** Camping: staying within this distance (cm) of one spot counts as staying put. */
	UPROPERTY(EditAnywhere, Category = "Combat|Camping", meta = (ClampMin = "0.0"))
	float CampRadius = 250.0f;

	/** Seconds at a spot before heat starts to build — time to line up a few shots, free. */
	UPROPERTY(EditAnywhere, Category = "Combat|Camping", meta = (ClampMin = "0.0"))
	float CampGraceTime = 1.5f;

	/** Seconds after the grace for heat to reach full. */
	UPROPERTY(EditAnywhere, Category = "Combat|Camping", meta = (ClampMin = "0.1"))
	float CampTimeToFullHeat = 4.0f;

	/** Heat lost per second once the player has moved on. */
	UPROPERTY(EditAnywhere, Category = "Combat|Camping", meta = (ClampMin = "0.0"))
	float CampHeatDrainPerSecond = 0.5f;

	/** After taking a hit, seconds before any enemy may roll another — so one burst can't
	    shred the player. Rounds already in flight still land. */
	UPROPERTY(EditAnywhere, Category = "Combat|Hit Grace", meta = (ClampMin = "0.0"))
	float HitGraceTime = 0.5f;

	/** Seconds the evasive effect (enemies' EvadingHitMultiplier) lingers after a shootdodge
	    lands or a roll ends. 0: only while actually diving or rolling. */
	UPROPERTY(EditAnywhere, Category = "Combat|Evasion", meta = (ClampMin = "0.0"))
	float EvadeLingerTime = 2.0f;

	/** Vanquish-style: let go of the stick during a roll and it cuts into a kneel partway (the
	    Roll component's CrouchOutAfter): firing from the knee, down until the stick, the
	    crouch key or another roll gets it up. */
	UPROPERTY(EditAnywhere, Category = "Combat|Roll")
	bool bPostRollCrouch = true;

	/** Knelt, the stick doesn't steer the slide; once it's settled (under PostRollStandSpeed),
	    a push stands up and moves off. */
	UPROPERTY(EditAnywhere, Category = "Combat|Roll")
	bool bPostRollCrouchHoldsPosition = true;

	/** The roll button rolls only with the stick pushed past this (0..1; WASD is a full push);
	    below it, the button is the crouch key. The same push stands up from a settled kneel. */
	UPROPERTY(EditAnywhere, Category = "Combat|Roll", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float RollInputThreshold = 0.3f;

	/** A kneel's slide counts as settled under this speed (cm/s). */
	UPROPERTY(EditAnywhere, Category = "Combat|Roll", meta = (ClampMin = "0.0"))
	float PostRollStandSpeed = 50.0f;

	/** An empty gun reloads by itself once the player is free to (standing or lying prone,
	    not mid-dive or mid-roll), AutoReloadDelay after it ran dry. */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload")
	bool bAutoReload = true;

	UPROPERTY(EditAnywhere, Category = "Combat|Reload", meta = (ClampMin = "0.0"))
	float AutoReloadDelay = 0.2f;

	/** Rolling mid-reload: with at least this much of a magazine reload done, it's carried
	    through and the gun is reloaded when the roll ends; with less, it's cancelled. (A
	    shotgun's shell in progress always goes in after the roll.) */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float RollReloadKeepFraction = 1.0f / 3.0f;

	/** Reloading mid-dive (the flight) runs this many times as fast, timer and montage
	    together: a quick reload in the air instead of flying on dry. */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload", meta = (ClampMin = "1.0"))
	float AirReloadSpeed = 3.0f;

	/** Reloading in Focus (any slow motion) runs this many times as fast, timer and montage
	    together. It follows Focus mid-reload: on, the rest speeds up; off, it's back to normal
	    from that frame. */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload", meta = (ClampMin = "1.0"))
	float FocusReloadSpeed = 3.0f;

	/** An empty gun quick-reloads itself mid-dive too (with auto-reload on). */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload")
	bool bAirAutoReload = true;

	/** What a throw spawns. */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade")
	TSubclassOf<AGrenade> GrenadeClass;

	/** The toss: an additive montage on the Additive slot, so it plays over any pose (the dive too). */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade")
	TObjectPtr<UAnimMontage> GrenadeTossMontage;

	/** Seconds into the toss that the grenade leaves the hand. */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade", meta = (ClampMin = "0.0"))
	float GrenadeReleaseTime = 0.35f;

	/** Seconds from one throw until the next is allowed. */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade", meta = (ClampMin = "0.0"))
	float GrenadeThrowCooldown = 0.9f;

	/** The bone it leaves from. */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade")
	FName GrenadeHandSocket = TEXT("hand_l");

	/** How hard it's thrown (cm/s), along the camera's aim: look higher and it flies further
	    (Max Payne 2). */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade", meta = (ClampMin = "0.0"))
	float GrenadeThrowSpeed = 1400.0f;

	/** Degrees above the aim it leaves at, so a level look still lobs it. */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade", meta = (ClampMin = "0.0", ClampMax = "45.0"))
	float GrenadeLoftAngle = 12.0f;

	/** How much of the thrower's own velocity it carries: thrown from a dive, it flies further. */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float GrenadeInheritVelocity = 0.5f;

	/** From free-run the character turns to the camera first, as for a trigger pull; the toss
	    waits until it faces within this many degrees... */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade", meta = (ClampMin = "0.0"))
	float GrenadeFacingTolerance = 20.0f;

	/** ...or this many seconds at most. */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade", meta = (ClampMin = "0.0"))
	float GrenadeMaxTurnWait = 0.35f;

	/** Grenades carried at the start. They live in the ammo pool (EAmmoType::Grenade), so the
	    holder's MaxAmmoByType caps them and ammo pickups refill them. */
	UPROPERTY(EditAnywhere, Category = "Combat|Grenade", meta = (ClampMin = "0"))
	int32 StartingGrenades = 3;

	/** What the G key does. Picked on the weapon wheel's slot 1; this is the starting choice. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
	EQuickAction QuickAction = EQuickAction::Grenade;

	/** The strike for each way of holding a gun: a pistol whip, a rifle or shotgun butt. Grips
	    with no entry use DefaultMeleeStrike. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee")
	TMap<EWeaponAnimType, FMeleeStrike> MeleeStrikes;

	UPROPERTY(EditAnywhere, Category = "Combat|Melee")
	FMeleeStrike DefaultMeleeStrike;

	/** The AnimBP slot the strike plays on; additive, like the grenade toss. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee")
	FName MeleeSlotName = TEXT("Additive");

	/** How fast the strike's animation plays. Lyra's clips run 1.2–1.5 s, mostly recovery; a
	    trigger pull after the blow lands cuts that short anyway. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.1"))
	float MeleePlayRate = 1.5f;

	/** Seconds into the strike that the blow lands; the trigger is locked until then. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.0"))
	float MeleeHitTime = 0.2f;

	/** Seconds from one strike until the next is allowed. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.0"))
	float MeleeCooldown = 0.8f;

	/** How far the blow reaches, from the character's centre to the enemy's body. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.0"))
	float MeleeRange = 150.0f;

	/** How far off the aim (degrees, either side) an enemy can be and still be struck. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.0", ClampMax = "180.0"))
	float MeleeConeAngle = 45.0f;

	/** Damage of a blow, ignoring where it lands. It always staggers; a gunman has 100 health,
	    so three blows kill. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.0"))
	float MeleeDamage = 35.0f;

	/** The bone the blow lands on, which the stagger knocks back. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee")
	FName MeleeHitBone = TEXT("spine_03");

	/** Through the strike the body turns toward the enemy being hit, this fast (degrees a second). */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.0"))
	float MeleeTurnRate = 900.0f;

	/** When a blow connects, both bodies all but freeze for this long (seconds) so it lands. 0: off. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.0"))
	float MeleeHitStopTime = 0.06f;

	/** How fast the two bodies run during the hit-stop. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MeleeHitStopDilation = 0.05f;

	/** Played on the player's camera when a blow connects. Empty: none. */
	UPROPERTY(EditAnywhere, Category = "Combat|Melee")
	TSubclassOf<UCameraShakeBase> MeleeHitShake;

	/** Switching weapons mid-dive (the flight): the equip montage plays this many times as
	    fast, and the gun can fire as soon as it ends. */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload", meta = (ClampMin = "1.0"))
	float AirEquipSpeed = 3.0f;

	/** How quickly the camera catches up with the falling body. */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.0"))
	float DeathCameraFollowSpeed = 8.0f;


	/** Set up input action bindings */
	virtual void SetupPlayerInputComponent(UInputComponent* InputComponent) override;

	/** The player's crouch request. The actual crouch only happens while standing still —
	    crouch is momentary cover, not a way of moving. */
	bool bCrouchRequested = false;

	float DefaultFOV = 0.0f;

	/** Boom height and capsule half-height at spawn. The boom is re-derived from the
	    capsule's current size every frame, so crouching never moves the camera. */
	float BoomBaseHeight = 0.0f;
	float DefaultCapsuleHalfHeight = 0.0f;

	/** Current eased value of CrouchCameraOffset — 0 standing, CrouchCameraOffset crouched. */
	float CurrentCrouchCameraOffset = 0.0f;

	/** Current eased value of ShootdodgeCameraHeight — 0 normally, the full offset while dodging. */
	float CurrentShootdodgeCameraHeight = 0.0f;

	/** The camera sits over the left shoulder: every framing's sideways offset is mirrored. */
	bool bLeftShoulder = false;

public:

	/** Returns the camera boom **/
	USpringArmComponent* GetCameraBoom() const { return CameraBoom; }

	/** Returns the follow camera **/
	UCameraComponent* GetFollowCamera() const { return FollowCamera; }

	UFocusComponent* GetFocus() const { return Focus; }

	UKillCamComponent* GetKillCam() const { return KillCam; }

	UInteractComponent* GetInteraction() const { return Interaction; }

	UInputAction* GetInteractAction() const { return InteractAction; }

	/** The camera is over the left shoulder (Shoulder Swap). */
	UFUNCTION(BlueprintPure, Category = "Camera")
	bool IsOnLeftShoulder() const { return bLeftShoulder; }

	/** No shot fired, hit taken or near miss for OutOfCombatDelay. */
	bool IsOutOfCombat() const;

	/** Where his head turns: a nearby thing worth inspecting, unless the gun is up. */
	virtual bool GetHeadLookTarget(FVector& OutLocation) const override;

	/** Turning to throw or mid-toss: the free arm stays off physics and the blade's turns ease out. */
	bool IsThrowingGrenade() const;

	/** From the press until the strike's animation ends. The anim instance treats it like a toss. */
	bool IsMeleeing() const;

	/** What the G key does (for the HUD). */
	UFUNCTION(BlueprintPure, Category = "Combat")
	EQuickAction GetQuickAction() const { return QuickAction; }

	UShootdodgeComponent* GetShootdodge() const { return Shootdodge; }

	/** Mid-flight of a dive, the landing is on the body — the dive plays that thud. */
	virtual bool LandsOnTheBody() const override;

	URollComponent* GetRoll() const { return Roll; }

	virtual bool WantsFreeArmPhysics() const override;

	virtual bool ShouldSkipEquipAnimation() const override;

	virtual float GetEquipPlayRate() const override;
	virtual bool ShouldSilentEquip() const override;

	/** Lying within this of face-down (degrees from straight ahead), weapon swaps are silent:
	    no equip montage (it would draw through the floor), the same time to be ready. */
	UPROPERTY(EditAnywhere, Category = "Combat|Equip", meta = (ClampMin = "0.0", ClampMax = "180.0"))
	float SilentEquipFaceDownAngle = 45.0f;

	/** Re-derives the camera boom's height from the capsule's current size, right away. Call
	    after anything resizes the capsule mid-frame (crouch, a dive), or the camera shows one
	    frame at the old height. */
	void ApplyCameraHeight();

	/** Drops into the post-roll kneel (the roll calls this when the stick is let go past its
	    CrouchOutAfter). */
	void StartPostRollCrouch();

	/** The move stick is pushed past RollInputThreshold right now. */
	bool IsPushingStick() const { return GetMovePush() >= RollInputThreshold; }

	/** The roll may cut into a kneel (bPostRollCrouch on, alive). */
	bool CanPostRollCrouch() const { return bPostRollCrouch && !IsDead(); }

	/** Knelt after a roll (see bPostRollCrouch). */
	bool IsPostRollCrouching() const { return bPostRollCrouching; }

	/** Turning to the camera as the gun comes up (see AimTurnRate). */
	bool IsTurningToAim() const { return bTurningToAim; }

	/** Marks a shot from Source on the HUD: bHit red, otherwise a grey near miss (rationed). */
	void AddHitIndicator(const FVector& Source, bool bHit);

	/** In combat now: one of your shots, a hit taken, or a near miss. Restarts the count to
	    out-of-combat recovery. */
	void NoteCombat();

	/** Puts a line of dialogue on the HUD for this many seconds (empty, or 0, clears it). */
	void ShowSubtitle(const FText& Line, float Seconds)
	{
		CurrentSubtitle = Line;
		SubtitleTimeLeft = Seconds;
	}

	/** The subtitle showing now, or empty. */
	FText GetSubtitle() const { return SubtitleTimeLeft > 0.0f ? CurrentSubtitle : FText::GetEmpty(); }

	const TArray<FHitIndicator>& GetHitIndicators() const { return HitIndicators; }

	/** Mid-evasion (a shootdodge's flight, a roll) or within EvadeLingerTime after one —
	    enemies' shots are much less likely to land. */
	bool IsEvading() const;

	/** 0..1: how long the player has stayed put. Every enemy's hit chance rises with it, so
	    standing and shooting is fine for a moment and punished if it becomes camping. */
	UFUNCTION(BlueprintPure, Category = "Combat|Camping")
	float GetCampingHeat() const { return CampingHeat; }

	/** Just been hit: enemies hold off rolling hits until HitGraceTime has passed. */
	bool IsInHitGrace() const;

	/** Hands rotation to the animation (dives), or back to the movement stances. */
	void SetAnimationDrivenRotation(bool bAnimationDriven);

	/** Runs the reload the player asked for while prone, once the get-up is done. */
	void ReloadAfterShootdodge() { DoReload(); }

private:

	/** One trigger pull's worth of firing: DoFire's work. bFreshPull: a new press (DoFire), not
	    the held trigger (DoFireHeld), so semi-autos may beat their held rate. */
	void PullTrigger(bool bFreshPull);

	/** The toss's release point: the grenade leaves the hand for the crosshair. */
	void ReleaseGrenade();

	/** The toss proper: the montage, then the release timer. */
	void StartToss();

	/** A throw waiting for the turn to the camera; starts the toss once facing. */
	void UpdatePendingThrow(float DeltaSeconds);

	bool bThrowPending = false;
	float ThrowPendingTime = 0.0f;

	FTimerHandle GrenadeReleaseTimer;
	float LastGrenadeThrowTime = -1000.0f;

	/** The blow lands: the enemy it turned to if still in reach, else whoever is. */
	void LandMelee();

	/** The enemy in reach nearest the aim, within MeleeConeAngle of it; null if none. */
	ABopisCharacterBase* FindMeleeTarget() const;

	/** Alive, within MeleeRange of its body, and nothing solid in between. */
	bool CanStrike(const ABopisCharacterBase* Target) const;

	/** Through the strike, turns the body toward MeleeTarget; after it, back to the camera. */
	void UpdateMeleeTurn(float DeltaSeconds);

	/** Hit-stop over: both bodies back to full speed. */
	void EndHitStop();

	/** The strike's dynamic montage, so IsMeleeing can tell when it's over. */
	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> ActiveMeleeMontage;

	TWeakObjectPtr<ABopisCharacterBase> MeleeTarget;
	TWeakObjectPtr<ABopisCharacterBase> HitStopTarget;
	bool bMeleeTurning = false;
	FTimerHandle MeleeHitTimer;
	FTimerHandle HitStopTimer;
	float LastMeleeTime = -1000.0f;

	FText CurrentSubtitle;
	float SubtitleTimeLeft = 0.0f;

	/** At a roll's start: a reload far enough along is held for the roll's end, the rest
	    cancelled. */
	void HoldReloadForRoll();

	/** The gun whose reload a roll is carrying (cleared when it's done or the gun changes). */
	TWeakObjectPtr<AWeaponBase> RollHeldReloadWeapon;

	/** Dead: the camera boom rides the body (pelvis) instead of the capsule left behind. */
	void FollowBodyWithCamera(float DeltaSeconds);

	void RestartLevel();

	/** Died diving, landing or prone: no death animation, and the dive's momentum goes
	    into the ragdoll. */
	bool bDiedMidDive = false;
	FVector DiveDeathVelocity = FVector::ZeroVector;

	/** Real seconds since death: ends the slow motion, then reloads the level. */
	float TimeSinceDeath = 0.0f;

	/** Builds heat while the player stays near CampAnchor; drains it once they move on. */
	void UpdateCampingHeat(float DeltaSeconds);

	float CampingHeat = 0.0f;
	FVector CampAnchor = FVector::ZeroVector;
	float TimeAtCampAnchor = 0.0f;

	/** World time of the last hit taken; well in the past until the first. */
	float LastHitTakenTime = -1000.0f;

	/** Adds a hit to RecentDamage and flashes red once HeavyDamageFraction of full health has
	    gone within HeavyDamageWindow (then starts the count again). */
	void UpdateHeavyDamageFlash(float Damage);

	/** A red flash over the screen, clearing over Duration real seconds (slow motion included). */
	void FlashDamage(float Alpha, float Duration);

	/** Hits within the last HeavyDamageWindow: world time and damage. */
	TArray<TPair<float, float>> RecentDamage;

	/** Raises the hit pulse to at least this hit's strength. */
	void PulseHit(float Damage);

	/** The hit pulse material on the camera, and its strength now (fading in real time). */
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> HitPulseInstance;
	float HitPulse = 0.0f;

	/** The hit pulse is on the camera at full weight. Off (weight 0) the renderer skips it. */
	bool bHitPulseBlended = false;

	/** Low health: eases the effect toward the health now and beats the edge. */
	void UpdateLowHealth(float RealDelta);

	/** The low-health effect's strength now (0..1), and the heartbeat's phase (0..1). */
	float LowHealthLevel = 0.0f;
	float LowHealthBeatPhase = 0.0f;

	/** Below the low-health line and out of combat long enough: health creeps back up to it. */
	void UpdateRecovery(float DeltaSeconds);

	/** World time of the last shot fired, hit taken or near miss (NoteCombat). */
	float LastCombatTime = -1000.0f;

	/** Mid-dive (the flight) or mid-roll, this very moment — IsEvading adds the linger. */
	bool IsEvadingNow() const;

	/** World time evasion was last under way. */
	float LastEvadingTime = -1000.0f;

	/** How far the move stick is pushed right now (0..1; Enhanced Input's live value, not the
	    last event). */
	float GetMovePush() const;

	/** Knelt after a roll, until the stick, the crouch key or another roll gets it up. */
	bool bPostRollCrouching = false;

	/** Turns the body toward the camera while bTurningToAim, then locks it there. */
	void UpdateAimTurn(float DeltaSeconds);

	bool bTurningToAim = false;

	TArray<FHitIndicator> HitIndicators;

	/** Reloads an empty gun by itself, once the player is free to. */
	void UpdateAutoReload(float DeltaSeconds);

	/** How fast a reload should run right now: AirReloadSpeed in a dive's flight,
	    FocusReloadSpeed in Focus, else 1. */
	float GetReloadSpeed() const;

	/** Keeps a running reload at GetReloadSpeed as Focus comes and goes. */
	void UpdateReloadSpeed();

	/** Seconds the equipped gun has been empty with a reload possible. */
	float EmptyGunTime = 0.0f;
	bool bDeathSlowMo = false;

};

