// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProjectBopisGameMode.h"
#include "Components/SkeletalMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"
#include "TimerManager.h"

AProjectBopisGameMode::AProjectBopisGameMode()
{
	// stub
}

void AProjectBopisGameMode::RegisterCorpse(AActor* Corpse)
{
	if (Corpse)
	{
		Corpses.Add(Corpse);
		TrimCorpses();
	}
}

/** In the player's view: inside the camera's view cone and not hidden behind anything. */
static bool IsInView(const AActor* Actor)
{
	const UWorld* World = Actor->GetWorld();
	const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(World, 0);
	const USkeletalMeshComponent* Body = Actor->FindComponentByClass<USkeletalMeshComponent>();
	if (!Camera || !Body)
	{
		return false;
	}

	const FVector Eye = Camera->GetCameraLocation();
	const FVector Target = Body->Bounds.Origin;
	const FVector ToTarget = Target - Eye;
	const float Distance = ToTarget.Size();
	if (Distance < KINDA_SMALL_NUMBER)
	{
		return true;
	}

	// Inside the cone: half the field of view, widened by how big the body looks from here.
	// The horizontal FOV is the wider one, so using it errs on the side of "visible".
	const float BodyAngle = FMath::RadiansToDegrees(FMath::Atan2(Body->Bounds.SphereRadius, Distance));
	const float OffAxis = FMath::RadiansToDegrees(FMath::Acos(
		FVector::DotProduct(Camera->GetCameraRotation().Vector(), ToTarget / Distance)));
	if (OffAxis > Camera->GetFOVAngle() * 0.5f + BodyAngle)
	{
		return false;
	}

	// Not behind a wall: the first thing the line of sight meets is the body itself.
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CorpseLineOfSight), false, Camera->GetViewTarget());
	FHitResult Hit;
	if (!World->LineTraceSingleByChannel(Hit, Eye, Target, ECC_Visibility, Params))
	{
		return true;
	}
	return Hit.GetActor() == Actor;
}

void AProjectBopisGameMode::TrimCorpses()
{
	// Forget any that are already gone.
	Corpses.RemoveAll([](const TWeakObjectPtr<AActor>& Entry) { return !Entry.IsValid(); });

	// Oldest first, skipping any in view: those wait until the player looks away.
	for (int32 Index = 0; Index < Corpses.Num() && Corpses.Num() > MaxCorpses; )
	{
		AActor* Corpse = Corpses[Index].Get();
		if (!IsInView(Corpse))
		{
			Corpse->Destroy();
			Corpses.RemoveAt(Index);
		}
		else
		{
			++Index;
		}
	}

	// Still over (all the extras are in view): keep checking. Within the limit: stop.
	FTimerManager& Timers = GetWorldTimerManager();
	if (Corpses.Num() > MaxCorpses)
	{
		if (!Timers.IsTimerActive(CorpseCheckTimer))
		{
			Timers.SetTimer(CorpseCheckTimer, this, &AProjectBopisGameMode::TrimCorpses, CorpseCheckInterval, true);
		}
	}
	else
	{
		Timers.ClearTimer(CorpseCheckTimer);
	}
}
