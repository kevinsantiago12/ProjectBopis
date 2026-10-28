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
class UPostProcessComponent;
class AGrenade;
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

	/** Grenade throw Input Action **/
	UPROPERTY(EditAnywhere, Category = "Input")
	UInputAction* GrenadeAction;

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

	/** Toggles Focus from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoToggleFocus();

	/** Starts a shootdodge from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoShootdodge();

	/** Starts a dodge roll from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoRoll();

	/** Throws a grenade from input. */
	UFUNCTION(BlueprintCallable, Category = "Input")
	virtual void DoThrowGrenade();

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

	/** Real seconds of slow motion when the player dies. 0 turns it off. */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.0"))
	float DeathSlowMoDuration = 2.0f;

	/** World speed during the death slow motion. */
	UPROPERTY(EditAnywhere, Category = "Health|Death", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float DeathTimeDilation = 0.2f;

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

	/** Starting a reload ends Focus (slow motion) if it's on. */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload")
	bool bStopFocusOnReload = true;

	/** Rolling mid-reload: with at least this much of a magazine reload done, it's carried
	    through and the gun is reloaded when the roll ends; with less, it's cancelled. (A
	    shotgun's shell in progress always goes in after the roll.) */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float RollReloadKeepFraction = 1.0f / 3.0f;

	/** Reloading mid-dive (the flight) runs this many times as fast, timer and montage
	    together: a quick reload in the air instead of flying on dry. */
	UPROPERTY(EditAnywhere, Category = "Combat|Reload", meta = (ClampMin = "1.0"))
	float AirReloadSpeed = 3.0f;

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

public:

	/** Returns the camera boom **/
	USpringArmComponent* GetCameraBoom() const { return CameraBoom; }

	/** Returns the follow camera **/
	UCameraComponent* GetFollowCamera() const { return FollowCamera; }

	UFocusComponent* GetFocus() const { return Focus; }

	/** Turning to throw or mid-toss: the free arm stays off physics and the blade's turns ease out. */
	bool IsThrowingGrenade() const;

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

	/** Seconds the equipped gun has been empty with a reload possible. */
	float EmptyGunTime = 0.0f;
	bool bDeathSlowMo = false;

};

