#include "AnimGraphNode_GunUpright.h"

#define LOCTEXT_NAMESPACE "AnimGraphNode_GunUpright"

FText UAnimGraphNode_GunUpright::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
	return GetControllerDescription();
}

FText UAnimGraphNode_GunUpright::GetTooltipText() const
{
	return LOCTEXT("Tooltip", "Rolls the hand about the gun's barrel so the gun stays upright as the aim moves up and down.");
}

FText UAnimGraphNode_GunUpright::GetControllerDescription() const
{
	return LOCTEXT("Title", "Gun Upright");
}

#undef LOCTEXT_NAMESPACE
