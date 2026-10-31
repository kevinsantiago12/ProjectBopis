// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "KillCamComponent.generated.h"

class ACharacter;
class AEnemyBase;
class UFocusComponent;
class USoundBase;
struct FCollisionQueryParams;
struct FMinimalViewInfo;

/** How the kill cam frames the kill. */
UENUM(BlueprintType)
enum class EKillCamStyle : uint8
{
	/** Swings round the body, pushing in and sinking to a low angle. */
	Orbit UMETA(DisplayName = "Orbit Cam"),

	/** From behind the body, over its shoulder, back at the player: the body big in the
	    foreground, the player shooting into it. Still. */
	ReverseShot UMETA(DisplayName = "Reverse Shot Cam"),

	/** Up high and still, turning only to watch the body fall. */
	Steady UMETA(DisplayName = "Steady Cam"),

	/** One of the three, picked fresh each kill. */
	Random
};

/**
 *  Kill cam (Max Payne 2): the player's kill that clears a room, with no one else still
 *  fighting, drops the world into deep slow motion and puts the camera on the falling body.
 *  Meanwhile the player can't move or look, but can keep shooting: the shots go into the body
 *  (riddling it if it's still on its feet), and each one holds the cam a little longer.
 *  Style picks the shot. One with no clear place to stand plays as the Orbit Cam, and with
 *  nowhere clear for that either, there's no kill cam.
 *  The camera manager blends this view in by GetBlendWeight; the player's aim follows the body.
 *  Times are real seconds, whatever the slow motion.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class PROJECTBOPIS_API UKillCamComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UKillCamComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** The player killed Victim: plays the cam if that cleared its room and no one else is fighting. */
	void NotifyKill(AEnemyBase* Victim);

	/** Ends it at once, with no blend (the player's death). */
	void Stop();

	/** Playing, blend out included. (Not IsActive: that's the component's own on/off.) */
	UFUNCTION(BlueprintPure, Category = "Kill Cam")
	bool IsPlaying() const { return bActive; }

	/** 0..1: how much of the view is the kill cam's. */
	float GetBlendWeight() const { return Weight; }

	/** Blends the kill cam's view into View by GetBlendWeight (the camera manager calls this). */
	void BlendView(FMinimalViewInfo& View) const;

	/** Where a shot fired now goes: into the body, scattered a little. Holds the cam
	    ExtendPerShot longer. */
	FVector TakeShotPoint();

	/** The body's point (TargetBone, unscattered): where the player's aim locks on while it plays. */
	FVector GetAimPoint() const { return LastTargetPoint; }

	/** Off: it never plays. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam")
	bool bEnabled = true;

	/** The shot, for every room that doesn't pick its own (a trigger's Encounter|Cleared). One
	    with no room (a reverse shot with the body against a wall, a steady cam under a low
	    ceiling) plays as the Orbit Cam instead. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam")
	EKillCamStyle Style = EKillCamStyle::Orbit;

	/** World speed while it plays. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam", meta = (ClampMin = "0.02", ClampMax = "1.0"))
	float TimeDilation = 0.15f;

	/** How long it plays with no shots fired, before its blend out. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam", meta = (ClampMin = "0.0"))
	float MinDuration = 2.0f;

	/** Each shot keeps it playing at least this much longer. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam", meta = (ClampMin = "0.0"))
	float ExtendPerShot = 0.6f;

	/** The longest it plays, however long the shooting goes on (blend out not counted). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam", meta = (ClampMin = "0.0"))
	float MaxDuration = 5.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam", meta = (ClampMin = "0.0"))
	float BlendInTime = 0.25f;

	/** The view and the world's speed come back together over this. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam", meta = (ClampMin = "0.0"))
	float BlendOutTime = 0.4f;

	/** Played as it starts (a whoosh), 2D. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam")
	TObjectPtr<USoundBase> StartSound;

	// ---- Camera (every style) ----

	/** The bone the camera watches and the shots go to (and, for the reverse shot, the one it
	    frames on the player). Without it, the body's middle. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Camera")
	FName TargetBone = TEXT("spine_03");

	/** How fast the camera's aim catches up with the body (it smooths a ragdoll's jitter). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Camera", meta = (ClampMin = "0.0"))
	float FollowSpeed = 8.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Camera", meta = (ClampMin = "10.0", ClampMax = "170.0"))
	float FieldOfView = 70.0f;

	/** Radius (cm) of the camera's own room: it never goes where this would touch a wall, or the
	    player. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Camera", meta = (ClampMin = "0.0"))
	float ProbeRadius = 12.0f;

	/** The view only has to be clear to within this (cm) of TargetBone, so a body slumped against
	    a wall still counts as seen. Nearer than this is inside the body. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Camera", meta = (ClampMin = "0.0"))
	float BodyClearance = 25.0f;

	/** Standing still (a still shot, or a stopped swing), the body can be out of sight from there
	    this long (real seconds) before anything's done: a stopped orbit swings back the other
	    way, once; anything else ends early. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Camera", meta = (ClampMin = "0.0"))
	float HiddenTolerance = 0.3f;

	// ---- Orbit Cam ----

	/** Distance (cm) from the body at the start (nearer if the player's camera was), pushing in
	    to EndDistance over MinDuration. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Orbit Cam", meta = (ClampMin = "10.0"))
	float StartDistance = 280.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Orbit Cam", meta = (ClampMin = "10.0"))
	float EndDistance = 170.0f;

	/** Height (cm) above TargetBone at the start, sinking to EndHeight (a low angle) over MinDuration. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Orbit Cam")
	float StartHeight = 40.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Orbit Cam")
	float EndHeight = 0.0f;

	/** Degrees per second it swings round the body, toward the side with more room. Anything in
	    the way stops the swing for good: it holds that angle rather than pass through or jump in. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Orbit Cam", meta = (ClampMin = "0.0"))
	float OrbitSpeed = 45.0f;

	/** The swing gets up to speed over this. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Orbit Cam", meta = (ClampMin = "0.0"))
	float OrbitEaseTime = 0.5f;

	/** Swinging back, it can go this long (real seconds) at a time without seeing the body as it
	    comes round. Any longer, it stops there (and, out of sight, the cam ends). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Orbit Cam", meta = (ClampMin = "0.0"))
	float SwingBackGrace = 1.0f;

	// ---- Reverse Shot Cam ----

	/** How far (cm) behind the body it stands, on the line from the player through it. In closer
	    (60%) if nothing's clear there. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Reverse Shot Cam", meta = (ClampMin = "10.0"))
	float ReverseDistance = 160.0f;

	/** How far (cm) off to one side: over the body's shoulder, so the player shows past it. The
	    other side if that's blocked, then half as far. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Reverse Shot Cam", meta = (ClampMin = "0.0"))
	float ReverseSide = 70.0f;

	/** Height (cm) above TargetBone. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Reverse Shot Cam")
	float ReverseHeight = 20.0f;

	/** Where it aims, from the player (0) to the body (1). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Reverse Shot Cam", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float ReverseFraming = 0.3f;

	// ---- Steady Cam ----

	/** How far (cm) out from the body it stands. In closer (60%) if nothing's clear there. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Steady Cam", meta = (ClampMin = "10.0"))
	float SteadyDistance = 300.0f;

	/** Height (cm) above TargetBone: the high angle. Half that if nothing's clear up there (a low
	    ceiling). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Steady Cam")
	float SteadyHeight = 220.0f;

	/** Degrees round from the player's side, either way, so it isn't just the player's view from
	    higher up. Further round if that's blocked. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Steady Cam", meta = (ClampMin = "0.0", ClampMax = "180.0"))
	float SteadyAngle = 35.0f;

	// ---- Shooting ----

	/** How far (cm) shots scatter round TargetBone, so they land on different bones. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Shooting", meta = (ClampMin = "0.0"))
	float ShotScatter = 12.0f;

	/** How fast the player's aim turns onto the body. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Kill Cam|Shooting", meta = (ClampMin = "0.0"))
	float AimFollowSpeed = 10.0f;

protected:

	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:

	/** Plays Shot on Victim (Random picks one). */
	void Start(AEnemyBase* Victim, EKillCamStyle Shot);
	void BeginBlendOut();
	void Finish();

	/** Each style's place to stand, if it has a clear one: sets CameraLocation (and the orbit's
	    swing). PlayerSideYaw / PlayerSideRadius: where the player's camera is, round the body. */
	bool PlaceOrbit(float PlayerSideYaw, float PlayerSideRadius);
	bool PlaceReverseShot();
	bool PlaceSteady(float PlayerSideYaw);

	/** A living enemy other than Except is alerted: still fighting, or about to. */
	bool IsAnyoneFighting(const AEnemyBase* Except) const;

	/** TargetBone on the body, or the body's middle; the last place seen once the body's gone. */
	FVector GetTargetPoint() const;

	/** TargetBone on Character, or its middle. */
	FVector GetBodyPoint(const ACharacter* Character) const;

	/** TargetBone on the player. */
	FVector GetPlayerPoint() const;

	/** Degrees swung by Time (seconds in), eased up to OrbitSpeed. */
	float GetOrbitAngle(float Time) const;

	/** Where the swing puts the camera Time seconds in (since the kill cam started), going round
	    the Sign way. */
	FVector GetSwingLocation(float Time, float Sign) const;

	/** A camera at Location would have room: ProbeRadius clear of walls and the player. */
	bool HasRoom(const FVector& Location) const;

	/** A camera at Location would see the body (to BodyClearance short of it). */
	bool SeesBody(const FVector& Location) const;

	/** Both: room, and the body in view. */
	bool IsClearView(const FVector& Location) const { return HasRoom(Location) && SeesBody(Location); }

	/** Nothing in the way from From to To (the player and the body don't count). */
	bool CanSee(const FVector& From, const FVector& To) const;

	/** The probes' settings: the player and the body never block the view. */
	FCollisionQueryParams GetProbeParams() const;

	void UpdateCamera(float RealDelta);

	/** The orbit, while it's swinging: on to the next spot if it can, else it stops. */
	void UpdateSwing(float RealDelta);

	/** Standing still (a still shot, or a stopped swing): what to do if the body's out of sight. */
	void UpdateStill(float RealDelta);

	/** Turns a stopped orbit back the other way, from where it is. */
	void SwingBack();
	void UpdatePlayerAim(float RealDelta);

	UFocusComponent* GetFocus() const;

	TWeakObjectPtr<AEnemyBase> Target;

	/** The shot playing: the one picked (Random settled), or the Orbit Cam if that had no room. */
	EKillCamStyle Playing = EKillCamStyle::Orbit;

	bool bActive = false;
	bool bBlendingOut = false;

	/** Seconds since it started, when the blend out starts (pushed back by shots), and into the
	    blend out. */
	float Elapsed = 0.0f;
	float EndAt = 0.0f;
	float BlendOutElapsed = 0.0f;

	float Weight = 0.0f;

	/** Weight when the blend out began (short of 1 if cut short mid blend in). */
	float BlendOutFrom = 1.0f;

	/** The orbit's swing: where it starts round the body, which way it goes, and its first distance. */
	float StartYaw = 0.0f;
	float OrbitSign = 1.0f;
	float StartRadius = 0.0f;

	/** The orbit's swing got blocked: it's stopped, and the camera holds where it last had a
	    clear view. */
	bool bSpinHeld = false;

	/** It has turned back the other way (only ever once), keeping the distance and height
	    (BackRadius, BackHeight) it turned at; and when the swing going now began (Elapsed). */
	bool bSwungBack = false;
	float BackRadius = 0.0f;
	float BackHeight = 0.0f;
	float SwingStartedAt = 0.0f;

	/** Real seconds the body's been out of sight: standing still, or swinging back. */
	float HiddenTime = 0.0f;

	/** The smoothed point the camera looks at, and the body's last known point. */
	FVector LookPoint = FVector::ZeroVector;
	FVector LastTargetPoint = FVector::ZeroVector;

	/** The reverse shot's smoothed point on the player. */
	FVector PlayerLookPoint = FVector::ZeroVector;

	FVector CameraLocation = FVector::ZeroVector;
	FRotator CameraRotation = FRotator::ZeroRotator;
};
