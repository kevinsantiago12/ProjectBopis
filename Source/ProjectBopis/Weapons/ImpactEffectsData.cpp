// Copyright Epic Games, Inc. All Rights Reserved.

#include "Weapons/ImpactEffectsData.h"
#include "ProjectBopis.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Kismet/GameplayStatics.h"
#include "Components/DecalComponent.h"
#include "GameFramework/Character.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundAttenuation.h"
#include "HAL/PlatformTime.h"

void UImpactEffectsData::SpawnImpact(const UObject* WorldContext, const FHitResult& Hit) const
{
	// Needs the hit's physical material — only filled in when the trace/sweep asked for it.
	const EPhysicalSurface Surface = UGameplayStatics::GetSurfaceType(Hit);
	const FImpactEffect* Found = Surfaces.Find(Surface);
	const FImpactEffect& Effect = Found ? *Found : Default;

	const FRotator SurfaceRotation = Hit.ImpactNormal.Rotation();
	const FVector BurstScale(Effect.Scale * EffectScale);

	// Smoke is the expensive part of a hit: big, overlapping, translucent. With none in the air a
	// hit always gets a puff; otherwise it waits out a random interval since the last, so a full
	// magazine spreads its smoke evenly across the burst. Other hits keep their sparks and chips.
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	const double Now = World ? World->GetTimeSeconds() : 0.0;
	// A puff older than its life is gone; a time ahead of Now is from an earlier world (PIE).
	SmokePuffTimes.RemoveAll([&](double Time) { return Now - Time > SmokePuffLifetime || Time > Now; });
	const bool bSmokeAllowed = SmokePuffTimes.IsEmpty()
		|| (Now >= NextSmokeTime && SmokePuffTimes.Num() < MaxSmokePuffs);
	bool bMadeSmoke = false;

	// The main burst and every layer go off at the same point and scale.
	// Pooled: full-auto fire reuses components instead of creating one per hit.
	// Spawned inactive so the smoke can be switched off before the first frame.
	auto SpawnBurst = [&](UNiagaraSystem* System)
	{
		if (!System)
		{
			return;
		}
		UNiagaraComponent* Burst = UNiagaraFunctionLibrary::SpawnSystemAtLocation(WorldContext, System,
			Hit.ImpactPoint, SurfaceRotation, BurstScale, true, false, ENCPoolMethod::AutoRelease);
		if (!Burst)
		{
			return;
		}
		for (const FNiagaraEmitterHandle& Handle : System->GetEmitterHandles())
		{
			if (Handle.GetName().ToString().Contains(TEXT("Smoke")))
			{
				if (bSmokeAllowed)
				{
					bMadeSmoke = true;
				}
				else
				{
					Burst->SetEmitterEnable(Handle.GetName(), false);
				}
			}
		}
		Burst->Activate(true);
	};

	SpawnBurst(Effect.System);
	for (UNiagaraSystem* Extra : Effect.ExtraSystems)
	{
		SpawnBurst(Extra);
	}
	if (bMadeSmoke)
	{
		SmokePuffTimes.Add(Now);
		NextSmokeTime = Now + FMath::FRandRange(SmokeIntervalMin, SmokeIntervalMax);
	}

	const bool bOnCharacter = Hit.GetActor() && Hit.GetActor()->IsA<ACharacter>();

	// A poster is paper pasted on the wall: the shot goes through and the wall answers as usual, and
	// the poster only adds the falling paper. The probe goes just 2 cm into the wall, so a poster
	// on the far side of a thin wall doesn't count. A time ahead of Now is from an earlier world (PIE).
	if (PaperBurst && World && !bOnCharacter && (Now - LastPaperTime >= PaperMinInterval || LastPaperTime > Now))
	{
		FHitResult PosterHit;
		if (World->LineTraceSingleByChannel(PosterHit, Hit.ImpactPoint + Hit.ImpactNormal * 10.0f,
			Hit.ImpactPoint - Hit.ImpactNormal * 2.0f, ECC_Paper))
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(WorldContext, PaperBurst, PosterHit.ImpactPoint,
				SurfaceRotation, BurstScale, true, true, ENCPoolMethod::AutoRelease);
			LastPaperTime = Now;
		}
	}

	// A head takes its own sound; anything else, one of its surface's clips.
	USoundBase* Sound = nullptr;
	if (bOnCharacter && HeadBones.Contains(Hit.BoneName))
	{
		Sound = PickSound(nullptr, HeadshotSounds);
	}
	if (!Sound)
	{
		Sound = PickSound(Effect.Sound, Effect.SoundVariants);
	}
	if (Sound)
	{
		UGameplayStatics::PlaySoundAtLocation(WorldContext, Sound, Hit.ImpactPoint, SoundVolume, 1.0f, 0.0f,
			SoundAttenuation);
	}

	// Decal and its variants form one pool; pick one at random. Empty entries are skipped.
	TArray<UMaterialInterface*, TInlineAllocator<8>> DecalPool;
	if (Effect.Decal)
	{
		DecalPool.Add(Effect.Decal);
	}
	for (UMaterialInterface* Variant : Effect.DecalVariants)
	{
		if (Variant)
		{
			DecalPool.Add(Variant);
		}
	}

	// People don't take bullet holes: the decal would land on every piece of the body and its
	// clothes, and slide as they move. Their impact is the burst and the sound.
	if (DecalPool.Num() > 0 && !bOnCharacter)
	{
		// A decal projects along its X axis, so roll spins it around the surface
		// normal — repeated holes don't all line up the same way.
		FRotator DecalRotation = SurfaceRotation;
		DecalRotation.Roll = FMath::FRandRange(0.0f, 360.0f);

		UMaterialInterface* Chosen = DecalPool[FMath::RandRange(0, DecalPool.Num() - 1)];
		if (UDecalComponent* SpawnedDecal = UGameplayStatics::SpawnDecalAtLocation(WorldContext, Chosen,
			Effect.DecalSize, Hit.ImpactPoint, DecalRotation, DecalLifeSpan))
		{
			SpawnedDecal->SetFadeScreenSize(0.0f);
			if (UBulletHoleSubsystem* Holes = SpawnedDecal->GetWorld()->GetSubsystem<UBulletHoleSubsystem>())
			{
				Holes->Register(SpawnedDecal);
			}
		}
	}
}

void UImpactEffectsData::PlayNearMiss(const UObject* WorldContext, const FVector& From, const FVector& To,
	const AActor* Shooter, const AActor* HitActor) const
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	const APawn* Player = World ? UGameplayStatics::GetPlayerPawn(World, 0) : nullptr;
	if (!Player || Shooter == Player || HitActor == Player || NearMissSounds.IsEmpty())
	{
		return;
	}

	// The point of the round's path nearest his head — only if the round got that far: one
	// that stopped short of him (a wall in front) or started beside him isn't a near miss.
	const FVector Head = Player->GetPawnViewLocation();
	const FVector Path = To - From;
	const double LengthSquared = Path.SizeSquared();
	if (LengthSquared < KINDA_SMALL_NUMBER)
	{
		return;
	}
	const double Along = FVector::DotProduct(Head - From, Path) / LengthSquared;
	const FVector Nearest = From + Path * Along;
	if (Along <= 0.0 || Along >= 1.0 || FVector::DistSquared(Nearest, Head) > FMath::Square(NearMissRadius))
	{
		return;
	}

	const double Now = FPlatformTime::Seconds();
	if (Now - LastNearMissTime < NearMissMinInterval)
	{
		return;
	}
	LastNearMissTime = Now;

	if (USoundBase* Sound = PickSound(nullptr, NearMissSounds))
	{
		UGameplayStatics::PlaySoundAtLocation(WorldContext, Sound, Nearest, NearMissVolume, 1.0f, 0.0f,
			SoundAttenuation);
	}
}

USoundBase* UImpactEffectsData::PickSound(USoundBase* First, const TArray<TObjectPtr<USoundBase>>& Variants)
{
	TArray<USoundBase*, TInlineAllocator<16>> Pool;
	if (First)
	{
		Pool.Add(First);
	}
	for (USoundBase* Variant : Variants)
	{
		if (Variant)
		{
			Pool.Add(Variant);
		}
	}
	return Pool.IsEmpty() ? nullptr : Pool[FMath::RandRange(0, Pool.Num() - 1)];
}

void UBulletHoleSubsystem::Register(UDecalComponent* Decal)
{
	Holes.RemoveAll([](const TWeakObjectPtr<UDecalComponent>& Entry) { return !Entry.IsValid(); });
	Holes.Add(Decal);

	while (Holes.Num() > MaxBulletHoles)
	{
		if (UDecalComponent* Oldest = Holes[0].Get())
		{
			Oldest->DestroyComponent();
		}
		Holes.RemoveAt(0);
	}
}
