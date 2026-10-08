// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Logging/LogMacros.h"
#include "Weapons/WeaponBase.h"
#include "ProjectBopisCharacter.generated.h"

class UPlayerHUDWidget;
class UInputComponent;
class USkeletalMeshComponent;
class USpringArmComponent;
class UCameraComponent;
class UInputAction;
class UWeaponHolderComponent;
class UAnimMontage;
struct FInputActionValue;

DECLARE_LOG_CATEGORY_EXTERN(LogTemplateCharacter, Log, All);

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
 *  The player character: third-person movement, aim/hip-fire stances, crouch and weapon handling.
 */
UCLASS(abstract)
class AProjectBopisCharacter : public ACharacter
{
	GENERATED_BODY()

	/** Third person camera boom — owns control rotation, distance and wall collision */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	USpringArmComponent* CameraBoom;

	/** Third person camera, mounted at the end of the boom */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UCameraComponent* FollowCamera;

	/** Handles carrying/switching weapons */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
	UWeaponHolderComponent* WeaponHolder;

	/** Widget class to spawn for the player HUD */
	UPROPERTY(EditDefaultsOnly, Category = "UI")
	TSubclassOf<UPlayerHUDWidget> HUDWidgetClass;

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

	/** Max walk speed when not aiming. */
	UPROPERTY(EditAnywhere, Category = "Movement")
	float FreeRunSpeed = 500.0f;

	/** Max walk speed while the aim button is held. Hip-fire strafing uses FreeRunSpeed. */
	UPROPERTY(EditAnywhere, Category = "Movement")
	float AimingSpeed = 250.0f;

	/** How quickly the character turns to face travel in FreeRun. Yaw only. */
	UPROPERTY(EditAnywhere, Category = "Movement")
	float FreeRunRotationRate = 360.0f;

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

	/** Extra camera height while crouched, eased in and out. 0 keeps the camera exactly
	    where it is when standing; negative lowers it with the crouch. */
	UPROPERTY(EditAnywhere, Category = "Camera")
	float CrouchCameraOffset = 0.0f;

	/** Seconds after the last trigger pull before the weapon lowers and the
	    character returns to free-run. Firing from the hip raises the weapon and
	    switches to the strafe stance for this long. */
	UPROPERTY(EditAnywhere, Category = "Combat", meta = (ClampMin = "0.0"))
	float LowerWeaponDelay = 1.5f;

	/** Pulls boom length, offset and FOV toward whatever the current state implies. */
	void UpdateCameraTransition(float DeltaSeconds);

	/** Applies the rotation/speed rules for a stance. Single place the flag pair is set. */
	void ApplyMovementStance(EMovementStance NewStance);

	/** Picks the stance the current state implies and applies it on change. */
	void UpdateMovementStance();

	/** Crouches while stationary and the request holds; stands up the moment input moves the character. */
	void UpdateCrouch();

	/** Drives a looping (per-round) reload montage: crossfades each Loop restart, and
	    sends it to End once the weapon stops loading. */
	void UpdateReloadMontage();

	EMovementStance CurrentStance = EMovementStance::FreeRun;
	
public:
	AProjectBopisCharacter();

protected:

	/** Called from Input Actions for movement input */
	void MoveInput(const FInputActionValue& Value);

	/** Called from Input Actions for looking input */
	void LookInput(const FInputActionValue& Value);

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

	/** Set up input action bindings */
	virtual void SetupPlayerInputComponent(UInputComponent* InputComponent) override;
	
	bool bIsAiming = false;

	/** The player's crouch request. The actual crouch only happens while standing still —
	    crouch is momentary cover, not a way of moving. */
	bool bCrouchRequested = false;

	/** Counts down from LowerWeaponDelay after each trigger pull. Above zero, the
	    weapon stays raised even when not aiming. */
	float TimeUntilWeaponLowered = 0.0f;

	float DefaultFOV = 0.0f;

	/** The reload montage DoReload started, tracked until it finishes or is cut off. */
	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> ActiveReloadMontage;

	/** The equip montage started by the last weapon change, while it plays. */
	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> ActiveEquipMontage;

	/** Crossfade time when a reload Loop section restarts (its first and last poses don't match). */
	UPROPERTY(EditAnywhere, Category = "Animation", meta = (ClampMin = "0.0"))
	float ReloadLoopBlendTime = 0.15f;

	/** Boom height and capsule half-height at spawn. The boom is re-derived from the
	    capsule's current size every frame, so crouching never moves the camera. */
	float BoomBaseHeight = 0.0f;
	float DefaultCapsuleHalfHeight = 0.0f;

	/** Current eased value of CrouchCameraOffset — 0 standing, CrouchCameraOffset crouched. */
	float CurrentCrouchCameraOffset = 0.0f;

public:

	/** Returns the camera boom **/
	USpringArmComponent* GetCameraBoom() const { return CameraBoom; }

	/** Returns the follow camera **/
	UCameraComponent* GetFollowCamera() const { return FollowCamera; }

	/**  Returns the weapon holder component **/
	UWeaponHolderComponent* GetWeaponHolder() const { return WeaponHolder; }

	/** Whether the aim stance is held. Drives the camera move and zoom. */
	UFUNCTION(BlueprintPure, Category = "Aim")
	bool IsAiming() const { return bIsAiming; }

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

};

