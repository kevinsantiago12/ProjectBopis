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

bool AProjectBopisGameMode::RequestAttackToken(AActor* Requester, float Distance)
{
	const float Now = GetWorld()->GetTimeSeconds();

	// Holders that are gone drop out; holds that have run their time are handed back, and
	// that enemy waits out the cooldown — so the tokens go round the room.
	for (int32 Index = AttackTokens.Num() - 1; Index >= 0; --Index)
	{
		AActor* Holder = AttackTokens[Index].Holder.Get();
		if (!Holder || Now - AttackTokens[Index].GrantedAt >= AttackTokenHoldTime)
		{
			if (Holder)
			{
				AttackTokenCooldowns.Add(Holder, Now + AttackTokenCooldown);
			}
			AttackTokens.RemoveAtSwap(Index);
		}
	}

	// Already holding: keep it, and keep its distance current for the comparison below.
	if (FAttackToken* Held = AttackTokens.FindByPredicate([Requester](const FAttackToken& Token) { return Token.Holder.Get() == Requester; }))
	{
		Held->Distance = Distance;
		return true;
	}

	const float* CooldownUntil = AttackTokenCooldowns.Find(Requester);
	if (CooldownUntil && Now < *CooldownUntil)
	{
		return false;
	}

	if (AttackTokens.Num() < MaxAttackTokens)
	{
		AttackTokens.Add({ Requester, Now, Distance });
		return true;
	}

	// All taken: the nearest threats are the ones that can kill. Clearly nearer than the
	// farthest holder takes its token; the one bumped can ask again straight away.
	int32 Farthest = INDEX_NONE;
	for (int32 Index = 0; Index < AttackTokens.Num(); ++Index)
	{
		if (Farthest == INDEX_NONE || AttackTokens[Index].Distance > AttackTokens[Farthest].Distance)
		{
			Farthest = Index;
		}
	}
	if (Farthest != INDEX_NONE && Distance + AttackTokenStealMargin < AttackTokens[Farthest].Distance)
	{
		AttackTokens[Farthest] = { Requester, Now, Distance };
		return true;
	}
	return false;
}

void AProjectBopisGameMode::ReleaseAttackToken(AActor* Holder, bool bCooldown)
{
	const int32 Removed = AttackTokens.RemoveAll([Holder](const FAttackToken& Token) { return Token.Holder.Get() == Holder; });
	if (Removed > 0 && bCooldown)
	{
		AttackTokenCooldowns.Add(Holder, GetWorld()->GetTimeSeconds() + AttackTokenCooldown);
	}
}
