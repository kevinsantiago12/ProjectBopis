#include "Weapons/Explosion.h"

#include "BopisCharacterBase.h"
#include "Camera/CameraShakeBase.h"
#include "Engine/OverlapResult.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Gameplay/FocusComponent.h"
#include "Kismet/GameplayStatics.h"

AExplosion::AExplosion()
{
	PrimaryActorTick.bCanEverTick = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AExplosion::BeginPlay()
{
	Super::BeginPlay();

	Detonate();

	// The effects live on their own; the blast itself is done.
	SetLifeSpan(0.5f);
}

void AExplosion::Detonate()
{
	UWorld* World = GetWorld();
	const FVector Center = GetActorLocation();

	if (ExplosionEffect)
	{
		UGameplayStatics::SpawnEmitterAtLocation(World, ExplosionEffect, Center, FRotator::ZeroRotator, FVector(EffectScale));
	}
	if (ExplosionSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ExplosionSound, Center);
	}
	if (CameraShake)
	{
		UGameplayStatics::PlayWorldCameraShake(this, CameraShake, Center, 0.0f, CameraShakeRadius);
	}

	// Everything in reach that moves or can be hurt, once each.
	TArray<FOverlapResult> Overlaps;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(Explosion), false, this);
	World->OverlapMultiByObjectType(Overlaps, Center, FQuat::Identity,
		FCollisionObjectQueryParams(FCollisionObjectQueryParams::AllDynamicObjects),
		FCollisionShape::MakeSphere(Radius), Params);

	TArray<AActor*> Caught;
	for (const FOverlapResult& Overlap : Overlaps)
	{
		AActor* Actor = Overlap.GetActor();
		if (!Actor || Actor == this)
		{
			continue;
		}
		Caught.AddUnique(Actor);

		// Loose props are pushed; bodies are thrown by their damage instead (LaunchBody).
		UPrimitiveComponent* Component = Overlap.GetComponent();
		if (Component && Component->IsSimulatingPhysics() && !Cast<ACharacter>(Actor))
		{
			Component->AddRadialImpulse(Center, Radius, PhysicsImpulse, RIF_Linear, true);
		}
	}

	const APawn* InstigatorPawn = GetInstigator();
	bool bKilled = false;
	for (AActor* Victim : Caught)
	{
		if (!CanReach(Center, Victim, Caught))
		{
			continue;
		}

		const FVector Target = Victim->GetActorLocation();
		const float Scale = FMath::GetMappedRangeValueClamped(FVector2D(FullDamageRadius, Radius),
			FVector2D(1.0f, EdgeDamageFraction), FVector::Dist(Center, Target));

		// Out from the blast and a little up, so bodies are thrown clear of the floor.
		const FVector Direction = ((Target - Center).GetSafeNormal2D() + FVector::UpVector * 0.5f).GetSafeNormal();
		const FHitResult Hit(Victim, nullptr, Target, -Direction);

		ABopisCharacterBase* Body = Cast<ABopisCharacterBase>(Victim);
		const bool bWasAlive = Body && !Body->IsDead();

		UGameplayStatics::ApplyPointDamage(Victim, Damage * Scale, Direction, Hit,
			GetInstigatorController(), this, UDamageType::StaticClass());

		// Killed by it, or already down: thrown clear, out and up.
		if (Body && Body->IsDead())
		{
			const FVector Out = (Target - Center).GetSafeNormal2D();
			Body->BlastLaunch(Out * (ThrowSpeed * Scale) + FVector::UpVector * (LiftSpeed * Scale));
		}

		if (bWasAlive && Body->IsDead() && Victim != InstigatorPawn)
		{
			bKilled = true;
		}
	}

	// The player's blast took someone out: a beat of slow motion to watch it.
	if (bKilled && KillSlowMotionDuration > 0.0f && InstigatorPawn && InstigatorPawn->IsPlayerControlled())
	{
		if (UFocusComponent* Focus = InstigatorPawn->FindComponentByClass<UFocusComponent>())
		{
			Focus->PlayKillSlowMotion(KillSlowMotionDuration);
		}
	}
}

bool AExplosion::CanReach(const FVector& Center, const AActor* Target, const TArray<AActor*>& Caught) const
{
	FCollisionQueryParams Params(SCENE_QUERY_STAT(ExplosionReach), false, this);
	Params.AddIgnoredActors(Caught);

	// Lifted off the floor a little, so a grenade lying on the ground still sees over the lip.
	FHitResult Hit;
	return !GetWorld()->LineTraceSingleByChannel(Hit, Center + FVector(0.0f, 0.0f, 20.0f),
		Target->GetActorLocation(), ECC_Visibility, Params);
}
