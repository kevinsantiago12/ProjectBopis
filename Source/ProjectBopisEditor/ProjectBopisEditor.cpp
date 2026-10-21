// Copyright Epic Games, Inc. All Rights Reserved.

#include "Modules/ModuleManager.h"
#include "IPlacementModeModule.h"
#include "AssetRegistry/AssetData.h"
#include "Engine/Blueprint.h"
#include "Styling/AppStyle.h"
#include "Gameplay/EncounterTrigger.h"
#include "Gameplay/EncounterEvent.h"

#define LOCTEXT_NAMESPACE "ProjectBopisEditor"

/**
 *  Editor-only tools. For now: an "Encounter" tab in the Place Actors panel holding the
 *  encounter trigger and the spawn, ambush and patrol points, to drag straight into a level.
 */
class FProjectBopisEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		IPlacementModeModule& Placement = IPlacementModeModule::Get();

		const FPlacementCategoryInfo Category(LOCTEXT("EncounterCategory", "Encounter"),
			FSlateIcon(FAppStyle::GetAppStyleSetName(), "PlacementBrowser.Icons.Volumes"),
			CategoryName, TEXT("PMEncounter"), 45);
		if (!Placement.RegisterPlacementCategory(Category))
		{
			return;
		}

		// The trigger is a native class; the points are Blueprints (their arrows and colours).
		Placement.RegisterPlaceableItem(CategoryName,
			MakeShared<FPlaceableItem>(nullptr, FAssetData(AEncounterTrigger::StaticClass()), 0));
		Placement.RegisterPlaceableItem(CategoryName,
			MakeShared<FPlaceableItem>(nullptr, FAssetData(AEncounterEvent::StaticClass()), 10));

		const TCHAR* Points[] = {
			TEXT("/Game/ThirdPerson/Blueprints/Encounter/BP_EnemySpawnPoint.BP_EnemySpawnPoint"),
			TEXT("/Game/ThirdPerson/Blueprints/Encounter/BP_AmbushPoint.BP_AmbushPoint"),
			TEXT("/Game/ThirdPerson/Blueprints/Encounter/BP_PatrolPoint.BP_PatrolPoint"),
		};
		int32 Order = 1;
		for (const TCHAR* Path : Points)
		{
			if (UBlueprint* Point = LoadObject<UBlueprint>(nullptr, Path))
			{
				Placement.RegisterPlaceableItem(CategoryName, MakeShared<FPlaceableItem>(nullptr, FAssetData(Point), Order++));
			}
		}
	}

	virtual void ShutdownModule() override
	{
		if (IPlacementModeModule::IsAvailable())
		{
			IPlacementModeModule::Get().UnregisterPlacementCategory(CategoryName);
		}
	}

private:
	const FName CategoryName = TEXT("Encounter");
};

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FProjectBopisEditorModule, ProjectBopisEditor)
