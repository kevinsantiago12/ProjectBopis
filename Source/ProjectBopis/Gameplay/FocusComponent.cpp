// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/FocusComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Components/PostProcessComponent.h"
#include "Components/AudioComponent.h"

UFocusComponent::UFocusComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UFocusComponent::BeginPlay()
{
	Super::BeginPlay();

	Meter = MaxMeter;

	PostProcess = GetOwner() ? GetOwner()->FindComponentByClass<UPostProcessComponent>() : nullptr;
	if (PostProcess)
	{
		PostProcess->BlendWeight = 0.0f;
	}
}

void UFocusComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// Never leave the world slowed behind us (death, level change, end of PIE).
	if (bActive)
	{
		ApplyTimeDilation(1.0f);
		UGameplayStatics::SetGlobalPitchModulation(this, 1.0f, 0.0f);
	}

	Super::EndPlay(EndPlayReason);
}

void UFocusComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// DeltaTime is game time, already slowed by the dilation. The meter runs in real
	// seconds, so undo it — otherwise Focus would last 1/0.3 times longer.
	const float GlobalDilation = UGameplayStatics::GetGlobalTimeDilation(this);
	const float RealDelta = GlobalDilation > KINDA_SMALL_NUMBER ? DeltaTime / GlobalDilation : DeltaTime;

	if (bActive)
	{
		if (!bInfinite)
		{
			Meter = FMath::Max(0.0f, Meter - DrainPerSecond * RealDelta);
			if (Meter <= 0.0f)
			{
				StopFocus();
			}
		}
	}
	else if (bPassiveRegen)
	{
		AddMeter(PassiveRegenPerSecond * RealDelta);
	}

	UpdateFeedback(RealDelta);
}

void UFocusComponent::Toggle()
{
	if (bActive)
	{
		StopFocus();
	}
	else
	{
		StartFocus();
	}
}

void UFocusComponent::StartFocus()
{
	if (bActive || (!bInfinite && Meter < MinMeterToActivate))
	{
		return;
	}

	bActive = true;
	ApplyTimeDilation(WorldTimeDilation);

	UGameplayStatics::SetGlobalPitchModulation(this, FocusPitch, FeedbackFadeTime);
	if (EnterSound)
	{
		UGameplayStatics::PlaySound2D(this, EnterSound);
	}
	if (LoopSound)
	{
		LoopAudio = UGameplayStatics::SpawnSound2D(this, LoopSound);
	}
}

void UFocusComponent::StopFocus()
{
	if (!bActive)
	{
		return;
	}

	bActive = false;
	ApplyTimeDilation(1.0f);

	UGameplayStatics::SetGlobalPitchModulation(this, 1.0f, FeedbackFadeTime);
	if (ExitSound)
	{
		UGameplayStatics::PlaySound2D(this, ExitSound);
	}
	if (LoopAudio)
	{
		LoopAudio->FadeOut(FeedbackFadeTime, 0.0f);
		LoopAudio = nullptr;
	}
}

void UFocusComponent::UpdateFeedback(float RealDelta)
{
	// Fades in real time, so it takes the same quarter-second whether the world is
	// slowed or not.
	const float Target = bActive ? 1.0f : 0.0f;
	const float Step = FeedbackFadeTime > 0.0f ? RealDelta / FeedbackFadeTime : 1.0f;
	FeedbackAlpha = FMath::Clamp(FeedbackAlpha + (Target > FeedbackAlpha ? Step : -Step), 0.0f, 1.0f);

	if (PostProcess)
	{
		PostProcess->BlendWeight = FeedbackAlpha;
	}
}

void UFocusComponent::AddMeter(float Amount)
{
	Meter = FMath::Clamp(Meter + Amount, 0.0f, MaxMeter);
}

void UFocusComponent::ApplyTimeDilation(float Dilation)
{
	// Global: everything slows, the player too (by design). Aim stays responsive
	// because look input is applied per input event, not per second.
	UGameplayStatics::SetGlobalTimeDilation(this, Dilation);
}
