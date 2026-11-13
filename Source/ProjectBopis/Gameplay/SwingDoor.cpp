// Copyright Epic Games, Inc. All Rights Reserved.

#include "Gameplay/SwingDoor.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "NavLinkComponent.h"

ASwingDoor::ASwingDoor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;      // ticks only while someone's at it or it's moving

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	Hinge = CreateDefaultSubobject<USceneComponent>(TEXT("Hinge"));
	Hinge->SetupAttachment(Root);

	Leaf = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Leaf"));
	Leaf->SetupAttachment(Hinge);
	Leaf->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	Leaf->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);     // never traps anyone
	Leaf->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);   // the camera doesn't snap in as it swings past
	Leaf->SetCanEverAffectNavigation(false);                       // the AI paths through the doorway

	PushZone = CreateDefaultSubobject<UBoxComponent>(TEXT("PushZone"));
	PushZone->SetupAttachment(Root);
	PushZone->SetCollisionProfileName(TEXT("Trigger"));
	PushZone->SetGenerateOverlapEvents(true);
	PushZone->SetCanEverAffectNavigation(false);
	PushZone->ShapeColor = FColor(255, 160, 40);

	// Joins the doorway's two sides for the AI (the navmesh's wall margin closes a one-leaf doorway). Both ways,
	// on the floor; the leaf ignores pawns and the push zone swings it open as they come through.
	NavLink = CreateDefaultSubobject<UNavLinkComponent>(TEXT("NavLink"));
	NavLink->SetupAttachment(Root);
	NavLink->SetMobility(EComponentMobility::Movable);
	if (NavLink->Links.Num() > 0)
	{
		NavLink->Links[0].Left = FVector(0.0f, -75.0f, 0.0f);
		NavLink->Links[0].Right = FVector(0.0f, 75.0f, 0.0f);
		NavLink->Links[0].Direction = ENavLinkDirection::BothWays;
	}
}

void ASwingDoor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	// The hinge at one side of the doorway; the leaf's mesh scaled to LeafWidth x LeafHeight, its edge on the hinge
	Hinge->SetRelativeLocation(FVector((bHingeOnRight ? 0.5f : -0.5f) * LeafWidth, 0.0f, 0.0f));
	if (const UStaticMesh* Mesh = Leaf->GetStaticMesh())
	{
		// The mesh's box once turned: its width along the door's X, its thickness along Y
		const FRotator Turn(0.0f, 90.0f * LeafQuarterTurns, 0.0f);
		const FBox Bounds = Mesh->GetBoundingBox().TransformBy(FTransform(Turn));
		const FVector Size = Bounds.GetSize();
		const float ScaleX = LeafWidth / FMath::Max(Size.X, 1.0f);
		const float ScaleZ = LeafHeight / FMath::Max(Size.Z, 1.0f);
		const float HingeEdge = bHingeOnRight ? Bounds.Max.X : Bounds.Min.X;
		// Scale works in the mesh's own axes, before the turn: on a quarter turn the mesh's Y is the door's width
		const bool bQuarterTurn = (LeafQuarterTurns % 2) == 1;
		Leaf->SetRelativeRotation(Turn);
		Leaf->SetRelativeScale3D(bQuarterTurn ? FVector(1.0f, ScaleX, ScaleZ) : FVector(ScaleX, 1.0f, ScaleZ));
		Leaf->SetRelativeLocation(FVector(-HingeEdge * ScaleX, -Bounds.GetCenter().Y, FloorGap - Bounds.Min.Z * ScaleZ));
	}
	PushZone->SetBoxExtent(FVector(LeafWidth * 0.5f, PushDepth, LeafHeight * 0.5f));
	PushZone->SetRelativeLocation(FVector(0.0f, 0.0f, LeafHeight * 0.5f));
	ApplySwing();
}

void ASwingDoor::BeginPlay()
{
	Super::BeginPlay();
	PushZone->OnComponentBeginOverlap.AddDynamic(this, &ASwingDoor::OnPushZoneEnter);
}

void ASwingDoor::OnPushZoneEnter(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
	int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (Cast<APawn>(OtherActor))
	{
		SetActorTickEnabled(true);
	}
}

void ASwingDoor::ApplySwing()
{
	// With the hinge on the right the leaf points along -X, so the same swing is the other way round
	Hinge->SetRelativeRotation(FRotator(0.0f, bHingeOnRight ? -Swing : Swing, 0.0f));
}

void ASwingDoor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	TArray<AActor*> Pawns;
	PushZone->GetOverlappingActors(Pawns, APawn::StaticClass());
	const FTransform& Door = GetActorTransform();

	if (Pawns.Num() > 0)
	{
		EmptyTime = 0.0f;
		// Each pawn pushes away from the side it stands on. The direction is picked only while the door is
		// (nearly) shut, from whoever is coming at it fastest, and kept while anyone's here, so it doesn't
		// flip as they walk through.
		if (OpenDir == 0.0f || FMath::Abs(Swing) < 15.0f)
		{
			float BestDir = 0.0f, BestToward = -TNumericLimits<float>::Max();
			AActor* Pusher = nullptr;
			for (AActor* Pawn : Pawns)
			{
				const float Dir = Door.InverseTransformPosition(Pawn->GetActorLocation()).Y < 0.0f ? 1.0f : -1.0f;
				const float Toward = Dir * Door.InverseTransformVectorNoScale(Pawn->GetVelocity()).Y;
				if (Toward > BestToward)
				{
					BestToward = Toward;
					BestDir = Dir;
					Pusher = Pawn;
				}
			}
			if (OpenDir == 0.0f)
			{
				if (OpenSound)
				{
					UGameplayStatics::PlaySoundAtLocation(this, OpenSound, GetActorLocation());
				}
				OnPushedOpen(BestDir, Pusher);
			}
			OpenDir = BestDir;
		}
		Target = OpenDir * OpenAngle;
		// A push: the leaf moves at least as fast as they come at it (running in throws it open)
		for (AActor* Pawn : Pawns)
		{
			const float Toward = OpenDir * Door.InverseTransformVectorNoScale(Pawn->GetVelocity()).Y;
			if (Toward > 0.0f)
			{
				SwingSpeed = OpenDir * FMath::Max(OpenDir * SwingSpeed, Toward * PushKick);
			}
		}
	}
	else
	{
		EmptyTime += DeltaSeconds;
		if (EmptyTime >= CloseDelay && Target != 0.0f)
		{
			Target = 0.0f;
			bCloseSoundDue = FMath::Abs(Swing) > 30.0f;
		}
	}

	// The spring, in small steps so a long frame can't throw it
	const int32 Steps = FMath::Clamp(FMath::CeilToInt(DeltaSeconds / 0.01f), 1, 8);
	const float Dt = DeltaSeconds / Steps;
	const float Stop = OpenAngle + 5.0f;
	for (int32 i = 0; i < Steps; ++i)
	{
		SwingSpeed += (Stiffness * (Target - Swing) - Damping * SwingSpeed) * Dt;
		const float Before = Swing;
		Swing += SwingSpeed * Dt;
		if (FMath::Abs(Swing) > Stop)                    // the stop: it knocks back off it
		{
			Swing = FMath::Sign(Swing) * Stop;
			SwingSpeed *= -0.3f;
		}
		if (Target == 0.0f && bCloseSoundDue && Before * Swing <= 0.0f)     // swinging back through shut
		{
			bCloseSoundDue = false;
			if (CloseSound)
			{
				UGameplayStatics::PlaySoundAtLocation(this, CloseSound, GetActorLocation());
			}
		}
	}
	ApplySwing();

	// Shut, still, nobody here: stop ticking until someone walks in
	if (Pawns.Num() == 0 && Target == 0.0f && FMath::Abs(Swing) < 0.2f && FMath::Abs(SwingSpeed) < 1.0f)
	{
		Swing = 0.0f;
		SwingSpeed = 0.0f;
		OpenDir = 0.0f;
		ApplySwing();
		SetActorTickEnabled(false);
	}
}
