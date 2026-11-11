#include "AnimGraphNode_UpperArmTwist.h"

#define LOCTEXT_NAMESPACE "AnimGraphNode_UpperArmTwist"

FText UAnimGraphNode_UpperArmTwist::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
	return GetControllerDescription();
}

FText UAnimGraphNode_UpperArmTwist::GetTooltipText() const
{
	return LOCTEXT("Tooltip", "Turns the upper arm's twist bones back against its roll, so the shoulder doesn't twist with the arm.");
}

FText UAnimGraphNode_UpperArmTwist::GetControllerDescription() const
{
	return LOCTEXT("Title", "Upper Arm Twist");
}

#undef LOCTEXT_NAMESPACE
