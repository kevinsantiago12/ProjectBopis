// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/MusicSubsystem.h"
#include "Components/AudioComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

void UMusicSubsystem::PlayMusic(USoundBase* Track, float FadeTime, float Volume)
{
	if (Track && Track == GetCurrentTrack())
	{
		return;
	}

	// Drop the old tracks that have finished fading.
	FadingOut.RemoveAll([](const UAudioComponent* Fading) { return !IsValid(Fading) || !Fading->IsPlaying(); });

	// The playing track fades out under the new one. Equal power, so the crossfade doesn't dip.
	if (IsValid(Current))
	{
		if (FadeTime > 0.0f)
		{
			Current->FadeOut(FadeTime, 0.0f, EAudioFaderCurve::Sin);
			FadingOut.Add(Current);
		}
		else
		{
			Current->Stop();
		}
	}
	Current = nullptr;

	if (!Track)
	{
		return;
	}

	// 2D, and destroyed once it stops. A UI sound is the one kind the global pitch (the Focus's
	// slow-motion drop) leaves alone; CreateSound2D already sets it, said again here because it's
	// what keeps the music at speed.
	Current = UGameplayStatics::CreateSound2D(this, Track, Volume);
	if (Current)
	{
		Current->bIsUISound = true;
		Current->FadeIn(FadeTime, 1.0f, 0.0f, EAudioFaderCurve::Sin);
	}
}

USoundBase* UMusicSubsystem::GetCurrentTrack() const
{
	return IsValid(Current) && Current->IsPlaying() ? Current->Sound : nullptr;
}
