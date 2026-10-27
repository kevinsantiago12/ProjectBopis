// Copyright Epic Games, Inc. All Rights Reserved.

#include "Weapons/ShellCasing.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "ProjectBopis.h"

AShellCasing::AShellCasing()
{
	Body = CreateDefaultSubobject<UBoxComponent>(TEXT("Body"));
	Body->InitBoxExtent(FVector(1.0f, 0.5f, 0.5f));

	// Solid against the world, but no obstacle to people, cameras, bullets or ragdolls
	// (bodies move and get cleaned up, which would leave a casing hanging in the air).
	Body->SetCollisionProfileName(TEXT("PhysicsActor"));
	Body->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	Body->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	Body->SetCollisionResponseToChannel(ECC_Projectile, ECR_Ignore);
	Body->SetCollisionResponseToChannel(ECC_PhysicsBody, ECR_Ignore);

	// Small and fast: without continuous collision it can tunnel through a thin floor.
	Body->BodyInstance.bUseCCD = true;
	Body->SetNotifyRigidBodyCollision(true);
	Body->SetSimulatePhysics(true);
	RootComponent = Body;

	MeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	MeshComponent->SetupAttachment(Body);
	MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AShellCasing::BeginPlay()
{
	Super::BeginPlay();

	Body->OnComponentHit.AddDynamic(this, &AShellCasing::OnBodyHit);
}

void AShellCasing::Launch(UStaticMesh* Mesh, float Scale, USoundBase* InImpactSound, const FVector& Velocity,
	const FVector& AngularVelocityDegrees, float LifeSpan, bool bMagazine)
{
	MeshComponent->SetStaticMesh(Mesh);
	MeshComponent->SetRelativeScale3D(FVector(Scale));
	ImpactSound = InImpactSound;

	// A body the size of the casing (at its scale), centred on it — the meshes have no simple
	// collision of their own to simulate with.
	const FBox LocalBox = MeshComponent->CalcBounds(FTransform(FQuat::Identity, FVector::ZeroVector, FVector(Scale))).GetBox();
	if (LocalBox.IsValid)
	{
		Body->SetBoxExtent(LocalBox.GetExtent().ComponentMax(FVector(0.3f)));
		MeshComponent->SetRelativeLocation(-LocalBox.GetCenter());

		// Keep the mesh where it was spawned — its pivot on the spawn point, as a socket preview
		// shows it — by moving the body to its centre.
		SetActorLocation(GetActorTransform().TransformPosition(LocalBox.GetCenter()), false, nullptr,
			ETeleportType::TeleportPhysics);
	}

	Body->SetPhysicsLinearVelocity(Velocity);
	Body->SetPhysicsAngularVelocityInDegrees(AngularVelocityDegrees);
	SetLifeSpan(LifeSpan);

	if (UShellCasingSubsystem* CasingSubsystem = GetWorld()->GetSubsystem<UShellCasingSubsystem>())
	{
		CasingSubsystem->Register(this, bMagazine);
	}
}

void AShellCasing::OnBodyHit(UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
	FVector NormalImpulse, const FHitResult& Hit)
{
	// A tink on a real bounce — not on every frame of rolling, and only the first few.
	const float Now = GetWorld()->GetTimeSeconds();
	if (ImpactSound && ImpactSoundsLeft > 0 && Now - LastImpactSoundTime > 0.15f && GetVelocity().Size() > 60.0f)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ImpactSound, Hit.ImpactPoint);
		LastImpactSoundTime = Now;
		--ImpactSoundsLeft;
	}
}

void UShellCasingSubsystem::Register(AShellCasing* Casing, bool bMagazine)
{
	TArray<TWeakObjectPtr<AShellCasing>>& List = bMagazine ? Magazines : Casings;
	const int32 Max = bMagazine ? MaxMagazines : MaxCasings;

	List.RemoveAll([](const TWeakObjectPtr<AShellCasing>& Entry) { return !Entry.IsValid(); });
	List.Add(Casing);

	while (List.Num() > Max)
	{
		if (AShellCasing* Oldest = List[0].Get())
		{
			Oldest->Destroy();
		}
		List.RemoveAt(0);
	}
}
