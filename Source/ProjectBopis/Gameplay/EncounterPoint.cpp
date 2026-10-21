#include "Gameplay/EncounterPoint.h"
#include "Components/TextRenderComponent.h"

AEncounterPoint::AEncounterPoint()
{
	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(GetRootComponent());
	Label->SetRelativeLocation(FVector(0.0f, 0.0f, 120.0f));
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(24.0f);
	Label->SetHiddenInGame(true);
	Label->bIsEditorOnly = true;
}

void AEncounterPoint::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

#if WITH_EDITOR
	const TCHAR* RoleName = TEXT("SPAWN");
	FColor RoleColor(255, 40, 40);
	if (PointRole == EEncounterPointRole::Ambush)
	{
		RoleName = TEXT("AMBUSH");
		RoleColor = FColor(255, 190, 0);
	}
	else if (PointRole == EEncounterPointRole::Patrol)
	{
		RoleName = TEXT("PATROL");
		RoleColor = FColor(40, 220, 80);
	}
	Label->SetText(FText::FromString(FString::Printf(TEXT("%s\n%s"), RoleName, *GetActorLabel())));
	Label->SetTextRenderColor(RoleColor);
#endif
}
