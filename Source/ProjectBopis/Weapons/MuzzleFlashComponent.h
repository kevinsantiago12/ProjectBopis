#pragma once

#include "CoreMinimal.h"
#include "Components/StaticMeshComponent.h"
#include "MuzzleFlashComponent.generated.h"

/** How big a gun's flash is and how long it lasts. Sizes in cm (whatever the gun's own scale), times in seconds. */
USTRUCT(BlueprintType)
struct FMuzzleFlashSettings
{
	GENERATED_BODY()

	/** Out of the muzzle, picked fresh between these for each shot. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flash")
	FFloatInterval Length = FFloatInterval(18.0f, 26.0f);

	/** Across the barrel. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flash")
	FFloatInterval Width = FFloatInterval(11.0f, 15.0f);

	/** From the bang to the last of the flame, at full speed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flash", meta = (ClampMin = "0.01"))
	float Duration = 0.06f;

	/** Times the material's own Intensity (MI_MuzzleFlash). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flash", meta = (ClampMin = "0.0"))
	float Brightness = 1.0f;

	/** The flash slows with the world, so Focus (0.3) shows it 3.3 times as long. This caps the stretch:
	    2 = never more than twice as long on screen. 0 = no cap. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flash", meta = (ClampMin = "0.0"))
	float SlowMotionMaxStretch = 0.0f;
};

/** A gun's muzzle flash: SM_MuzzleFlash at the muzzle, one shot at a time. Each shot gets its own size, roll,
    noise and front spikes; every frame this grows the mesh and hands M_MuzzleFlash the flash's age, and the
    material burns and cools the flame from it, so a slowed flash keeps changing instead of holding a still
    picture. Ticks only while a flash is showing. The look is made by Tools/FX/MuzzleFlash. */
UCLASS(ClassGroup = (Weapons), meta = (BlueprintSpawnableComponent))
class PROJECTBOPIS_API UMuzzleFlashComponent : public UStaticMeshComponent
{
	GENERATED_BODY()

public:
	UMuzzleFlashComponent();

	/** Starts a flash, cutting short one still showing. */
	void Fire(const FMuzzleFlashSettings& Settings);

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	/** Sizes the mesh and hands the material the current Age. */
	void Show();
	void Stop();

	FMuzzleFlashSettings Current;
	float Age = 1.0f;			// 0 at the bang, 1 at the end of the flash
	float FullLength = 0.0f;
	float FullWidth = 0.0f;
	uint64 FiredFrame = 0;
};
