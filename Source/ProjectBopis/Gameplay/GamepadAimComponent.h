#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GamepadAimComponent.generated.h"

class AEnemyBase;
class APlayerController;

/**
 *  Aiming with a controller. The right stick turns the view in degrees per second through a
 *  response curve, faster once held hard over, slower while aiming. Soft lock only ever helps a
 *  controller: pulling the aim trigger snaps onto the nearest enemy near the crosshair, the
 *  stick slows while the crosshair is near one, and the view follows that enemy's movement.
 *  The mouse is untouched.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class PROJECTBOPIS_API UGamepadAimComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UGamepadAimComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Turns the view by a stick's value (−1..1 each way). */
	void ApplyStick(const FVector2D& Stick, bool bAiming);

	/** On pulling the aim trigger: swings the view onto the nearest enemy near the crosshair. */
	void SnapToTarget();

	/** Whether the last look input came from a stick; soft lock only helps a controller. */
	void SetUsingGamepad(bool bInUsingGamepad) { bUsingGamepad = bInUsingGamepad; }

protected:
	/** Degrees per second at a full push, hip-fire. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Turning", meta = (ClampMin = "0.0"))
	float YawSpeed = 250.0f;

	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Turning", meta = (ClampMin = "0.0"))
	float PitchSpeed = 160.0f;

	/** Both speeds while aiming. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Turning", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float AimSpeedScale = 0.55f;

	/** Push to speed: 1 is linear; higher keeps light pushes fine and saves the speed for full ones. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Turning", meta = (ClampMin = "1.0"))
	float ResponseExponent = 2.0f;

	/** Extra yaw (degrees per second) once the stick has been held hard sideways a moment. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Turning", meta = (ClampMin = "0.0"))
	float BoostYawSpeed = 180.0f;

	/** Seconds held hard over before the boost starts, then seconds to reach it fully. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Turning", meta = (ClampMin = "0.0"))
	float BoostDelay = 0.25f;

	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Turning", meta = (ClampMin = "0.01"))
	float BoostRampTime = 0.3f;

	/** The input mapping negates the stick's Y, so pushing up arrives as −1. Flip if pushing up looks down. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Turning")
	bool bInvertPitch = false;

	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock")
	bool bSoftLock = true;

	/** Enemies further than this (cm) get no help. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock", meta = (ClampMin = "0.0"))
	float MaxRange = 4000.0f;

	/** Where on an enemy the help aims. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock")
	FName TargetBone = TEXT("spine_03");

	/** Pulling the aim trigger snaps to an enemy within this many degrees of the crosshair, over SnapTime. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock", meta = (ClampMin = "0.0"))
	float SnapAngle = 12.0f;

	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock", meta = (ClampMin = "0.01"))
	float SnapTime = 0.12f;

	/** Within this many degrees of an enemy the stick turns slower, by up to SlowdownStrength dead on. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock", meta = (ClampMin = "0.0"))
	float SlowdownAngle = 6.0f;

	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float SlowdownStrength = 0.5f;

	/** Within this many degrees of an enemy the view follows its movement, by this share. */
	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock", meta = (ClampMin = "0.0"))
	float FollowAngle = 6.0f;

	UPROPERTY(EditAnywhere, Category = "Gamepad Aim|Soft Lock", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float FollowStrength = 0.5f;

private:
	APlayerController* GetPlayerController() const;

	/** Soft lock helps now: a controller, a gun in hand, alive, the wheel shut. */
	bool CanAssist() const;

	/** The visible enemy whose aim point is nearest the crosshair, within MaxAngle and range. */
	AEnemyBase* FindTarget(float MaxAngle, float& OutAngle, FVector& OutAimPoint) const;

	FVector GetAimPoint(const AEnemyBase* Enemy) const;

	bool bUsingGamepad = false;

	/** Seconds the stick has been held hard sideways, and when it last sent input (real time). */
	float HardOverTime = 0.0f;
	double LastStickTime = 0.0;

	TWeakObjectPtr<AEnemyBase> SnapTarget;
	float SnapTimeLeft = 0.0f;
};
