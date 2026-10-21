// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

/** Editor-only tools for ProjectBopis (never in a packaged game). */
public class ProjectBopisEditor : ModuleRules
{
	public ProjectBopisEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PrivateDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"UnrealEd",
			"PlacementMode",
			"Slate",
			"SlateCore",
			"ProjectBopis"
		});
	}
}
