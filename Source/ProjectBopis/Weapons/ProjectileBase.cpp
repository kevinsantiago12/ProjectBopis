// Fill out your copyright notice in the Description page of Project Settings.


#include "Weapons/ProjectileBase.h"
#include "Components/SphereComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Components/PrimitiveComponent.h"
#include "Components/DecalComponent.h"

// Sets default values
AProjectileBase::AProjectileBase()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

	CollisionComponent = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionComponent"));
	CollisionComponent->InitSphereRadius(5.0f);
	CollisionComponent->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	RootComponent = CollisionComponent;

	ProjectileMovement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("ProjectileMovement"));
	ProjectileMovement->UpdatedComponent = CollisionComponent;
	ProjectileMovement->InitialSpeed = 3000.0f;
	ProjectileMovement->MaxSpeed = 3000.0f;
	ProjectileMovement->ProjectileGravityScale = 0.0f;

	InitialLifeSpan = 5.0f;
}

// Called when the game starts or when spawned
void AProjectileBase::BeginPlay()
{
	Super::BeginPlay();
	
	CollisionComponent->OnComponentHit.AddDynamic(this, &AProjectileBase::OnHit);

	// The round spawns inside the firer's own collision, so it would otherwise
	// detonate on them immediately. The weapon also calls AddIgnoredActor
	// explicitly after spawning, in case Instigator/Owner aren't set.
	AddIgnoredActor(GetInstigator());
	AddIgnoredActor(GetOwner());
}

void AProjectileBase::AddIgnoredActor(AActor* ActorToIgnore)
{
	if (!ActorToIgnore || IgnoredActors.Contains(ActorToIgnore))
	{
		return;
	}

	IgnoredActors.Add(ActorToIgnore);

	// Ignore in both directions: this projectile's own movement sweeps, and the
	// other actor's sweeps, so neither side can generate a blocking hit.
	CollisionComponent->IgnoreActorWhenMoving(ActorToIgnore, true);

	if (UPrimitiveComponent* OtherRoot = Cast<UPrimitiveComponent>(ActorToIgnore->GetRootComponent()))
	{
		OtherRoot->IgnoreActorWhenMoving(this, true);
	}
}

// Called every frame
void AProjectileBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

void AProjectileBase::OnHit(UPrimitiveComponent* HitComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit)
{
	// Never detonate on the firer — pass straight through instead. The ignore set
	// should prevent the hit entirely; this is the backstop if one slips past.
	if (OtherActor == this || (OtherActor && IgnoredActors.Contains(OtherActor)))
	{
		return;
	}

	// Spawned on any surface hit, not just damageable actors, so rounds mark
	// plain level geometry too. SetFadeScreenSize(0) defeats the built-in
	// distance culling, which otherwise hides decals a short way off.
	// Uses ImpactPoint, not Location: on a swept collision Location is the centre
	// of the collision sphere at impact, so the decal would float a radius off the
	// surface and only land on some angles. Line traces don't have that gap.
	if (HitDecalMaterial)
	{
		if (UDecalComponent* SpawnedDecal = UGameplayStatics::SpawnDecalAtLocation(this, HitDecalMaterial, DecalSize,
			Hit.ImpactPoint, Hit.ImpactNormal.Rotation(), DecalLifeSpan))
		{
			SpawnedDecal->SetFadeScreenSize(0.0f);
		}
	}

	if (OtherActor)
	{
		UGameplayStatics::ApplyDamage(OtherActor, Damage, GetInstigatorController(), this, nullptr);
	}

	TArray<FHitResult> FragmentHits;
	FCollisionShape FragmentSphere = FCollisionShape::MakeSphere(FragmentRadius);
	GetWorld()->SweepMultiByChannel(FragmentHits, Hit.Location, Hit.Location, FQuat::Identity, ECC_Pawn, FragmentSphere);

	for (const FHitResult& FragmentHit : FragmentHits)
	{
		AActor* FragmentActor = FragmentHit.GetActor();
		if (FragmentActor && FragmentActor != OtherActor && FragmentActor != this && !IgnoredActors.Contains(FragmentActor))
		{
			UGameplayStatics::ApplyDamage(FragmentActor, FragmentDamage, GetInstigatorController(), this, nullptr);
		}
	}

	Destroy();
}

