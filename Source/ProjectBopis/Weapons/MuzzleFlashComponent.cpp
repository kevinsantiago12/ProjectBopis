#include "Weapons/MuzzleFlashComponent.h"
#include "Kismet/GameplayStatics.h"

namespace
{
	// The growth over the first part of the flash's life (Tools/FX/MuzzleFlash/design.py has the rest).
	constexpr float StartLength = 0.45f;	// of the shot's full length, at the bang
	constexpr float StartWidth = 0.6f;
	constexpr float GrowTime = 0.3f;		// of the life, eased out

	// SM_MuzzleFlash is 100 cm long and wide.
	constexpr float MeshSize = 100.0f;
}

UMuzzleFlashComponent::UMuzzleFlashComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;

	SetMobility(EComponentMobility::Movable);
	SetVisibility(false);
	SetCollisionProfileName(TEXT("NoCollision"));
	SetGenerateOverlapEvents(false);
	SetCanEverAffectNavigation(false);
	CastShadow = false;
	bReceivesDecals = false;
	bVisibleInReflectionCaptures = false;
	// Sizes are in cm whatever the gun's own scale (the M4 is 1.33).
	SetUsingAbsoluteScale(true);
}

void UMuzzleFlashComponent::Fire(const FMuzzleFlashSettings& Settings)
{
	if (!GetStaticMesh())
	{
		return;
	}
	Current = Settings;
	Age = 0.0f;
	FiredFrame = GFrameCounter;
	FullLength = FMath::FRandRange(Settings.Length.Min, Settings.Length.Max);
	FullWidth = FMath::FRandRange(Settings.Width.Min, Settings.Width.Max);

	// Its own roll, noise, front spikes and brightness, so no two shots match, even slowed down. The material
	// reads these as custom primitive data: 0 Age (set by Show), 1 Seed, 2 Petals, 3 Brightness.
	SetRelativeRotation(FRotator(0.0f, 0.0f, FMath::FRandRange(0.0f, 360.0f)));
	SetCustomPrimitiveDataVector4(0, FVector4(0.0, FMath::FRand(), FMath::RandRange(3, 6),
		Settings.Brightness * FMath::FRandRange(0.85f, 1.15f)));
	Show();
	SetVisibility(true);
	SetComponentTickEnabled(true);
}

void UMuzzleFlashComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// The bang gets a frame of its own, whenever in the frame the shot came.
	if (GFrameCounter == FiredFrame)
	{
		return;
	}

	// DeltaTime is game time: in slow motion the flash plays slowed, like the world. Past the cap, it ages
	// faster by as much as the world is slowed beyond it.
	float Rate = 1.0f / FMath::Max(Current.Duration, 0.01f);
	const float Dilation = UGameplayStatics::GetGlobalTimeDilation(this);
	if (Current.SlowMotionMaxStretch > 0.0f && Dilation > 0.0f)
	{
		Rate *= FMath::Max(1.0f, 1.0f / (Dilation * Current.SlowMotionMaxStretch));
	}
	Age += DeltaTime * Rate;
	if (Age >= 1.0f)
	{
		Stop();
		return;
	}
	Show();
}

void UMuzzleFlashComponent::Show()
{
	// Grows out of the muzzle over the first part of its life, easing out.
	const float Grow = 1.0f - FMath::Square(1.0f - FMath::Min(Age / GrowTime, 1.0f));
	const float Length = FullLength * FMath::Lerp(StartLength, 1.0f, Grow);
	const float Width = FullWidth * FMath::Lerp(StartWidth, 1.0f, Grow);
	SetRelativeScale3D(FVector(Length, Width, Width) / MeshSize);
	SetCustomPrimitiveDataFloat(0, Age);
}

void UMuzzleFlashComponent::Stop()
{
	Age = 1.0f;
	SetVisibility(false);
	SetComponentTickEnabled(false);
}
