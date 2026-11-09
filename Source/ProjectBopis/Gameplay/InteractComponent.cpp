#include "Gameplay/InteractComponent.h"
#include "Gameplay/Interactable.h"
#include "Gameplay/InteractSubsystem.h"
#include "Gameplay/KillCamComponent.h"
#include "ProjectBopisCharacter.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"

UInteractComponent::UInteractComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// A prompt doesn't need every frame.
	PrimaryComponentTick.TickInterval = 0.1f;
}

void UInteractComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	Focused = PickFocus();
	LookTarget = PickLookTarget();
}

UObject* UInteractComponent::PickFocus() const
{
	const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(GetOwner());
	const APlayerController* Controller = Player ? Cast<APlayerController>(Player->GetController()) : nullptr;
	const UInteractSubsystem* Interactables = GetWorld()->GetSubsystem<UInteractSubsystem>();
	if (!Controller || !Interactables)
	{
		return nullptr;
	}

	if (!IsCalm(*Player))
	{
		return nullptr;
	}

	FVector ViewLocation;
	FRotator ViewRotation;
	Controller->GetPlayerViewPoint(ViewLocation, ViewRotation);
	const FVector ViewDirection = ViewRotation.Vector();

	// The one nearest the middle of the view wins.
	UObject* Best = nullptr;
	float BestDot = FMath::Cos(FMath::DegreesToRadians(MaxViewAngle));
	for (const TWeakObjectPtr<UObject>& Each : Interactables->GetInteractables())
	{
		const IInteractable* Interactable = Cast<IInteractable>(Each.Get());
		if (!Interactable || !Interactable->CanInteract())
		{
			continue;
		}

		// Near it, and looking its way.
		const FVector Target = Interactable->GetInteractLocation();
		if (FVector::Dist(Player->GetActorLocation(), Target) > Interactable->GetInteractRange())
		{
			continue;
		}
		const float Dot = ViewDirection | (Target - ViewLocation).GetSafeNormal();
		if (Dot < BestDot)
		{
			continue;
		}

		// Nothing in between.
		if (!CanSee(*Player, Target, Each.Get()))
		{
			continue;
		}

		Best = Each.Get();
		BestDot = Dot;
	}
	return Best;
}

UObject* UInteractComponent::PickLookTarget() const
{
	const AProjectBopisCharacter* Player = Cast<AProjectBopisCharacter>(GetOwner());
	const UInteractSubsystem* Interactables = GetWorld()->GetSubsystem<UInteractSubsystem>();
	if (!Player || !Interactables || !IsCalm(*Player))
	{
		return nullptr;
	}

	// The nearest one in front of him, by where his body faces (flat), not where the camera looks.
	const FVector Facing = Player->GetActorForwardVector().GetSafeNormal2D();
	const float MinDot = FMath::Cos(FMath::DegreesToRadians(LookAngle));
	UObject* Best = nullptr;
	float BestDistance = LookRange;
	for (const TWeakObjectPtr<UObject>& Each : Interactables->GetInteractables())
	{
		const IInteractable* Interactable = Cast<IInteractable>(Each.Get());
		if (!Interactable || !Interactable->CanInteract())
		{
			continue;
		}
		const FVector Target = Interactable->GetInteractLocation();
		const FVector Offset = Target - Player->GetActorLocation();
		const float Distance = Offset.Size();
		if (Distance > BestDistance || (Facing | Offset.GetSafeNormal2D()) < MinDot)
		{
			continue;
		}
		if (!CanSee(*Player, Target, Each.Get()))
		{
			continue;
		}
		Best = Each.Get();
		BestDistance = Distance;
	}
	return Best;
}

bool UInteractComponent::GetLookTarget(FVector& OutLocation) const
{
	const IInteractable* Interactable = Cast<IInteractable>(LookTarget.Get());
	if (!Interactable || !Interactable->CanInteract())
	{
		return false;
	}
	OutLocation = Interactable->GetInteractLocation();
	return true;
}

bool UInteractComponent::IsCalm(const AProjectBopisCharacter& Player)
{
	// Alive, on the ground, no kill cam, and no shots, hits or near misses for a while (the health
	// recovery's test).
	const UKillCamComponent* KillCam = Player.GetKillCam();
	return !Player.IsDead() && Player.GetCharacterMovement()->IsMovingOnGround()
		&& !(KillCam && KillCam->IsPlaying()) && Player.IsOutOfCombat();
}

bool UInteractComponent::CanSee(const AProjectBopisCharacter& Player, const FVector& Target, const UObject* Thing) const
{
	const FCollisionQueryParams Params(SCENE_QUERY_STAT(InteractSight), false, &Player);
	FHitResult Hit;
	return !GetWorld()->LineTraceSingleByChannel(Hit, Player.GetPawnViewLocation(), Target, ECC_Visibility, Params)
		|| Hit.GetActor() == Cast<AActor>(Thing)
		|| FVector::Dist(Hit.ImpactPoint, Target) <= 30.0f;
}

void UInteractComponent::Interact()
{
	// Picked again now rather than taken from the last tick: things may have changed since.
	IInteractable* Interactable = Cast<IInteractable>(PickFocus());
	Focused = nullptr;
	if (Interactable)
	{
		Interactable->Interact(Cast<AProjectBopisCharacter>(GetOwner()));
	}
}

FText UInteractComponent::GetPromptText() const
{
	const IInteractable* Interactable = Cast<IInteractable>(Focused.Get());
	return Interactable ? Interactable->GetInteractPrompt() : FText::GetEmpty();
}
