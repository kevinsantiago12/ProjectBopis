#include "AnimGraphNode_ForearmTwist.h"

#define LOCTEXT_NAMESPACE "AnimGraphNode_ForearmTwist"

FText UAnimGraphNode_ForearmTwist::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
	return GetControllerDescription();
}

FText UAnimGraphNode_ForearmTwist::GetTooltipText() const
{
	return LOCTEXT("Tooltip", "Spreads the hand's roll along the forearm's twist bones, so a hand turned after the clip doesn't pinch at the wrist.");
}

FText UAnimGraphNode_ForearmTwist::GetControllerDescription() const
{
	return LOCTEXT("Title", "Forearm Twist");
}

#undef LOCTEXT_NAMESPACE
