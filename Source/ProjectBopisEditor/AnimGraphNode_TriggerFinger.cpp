#include "AnimGraphNode_TriggerFinger.h"

#define LOCTEXT_NAMESPACE "AnimGraphNode_TriggerFinger"

FText UAnimGraphNode_TriggerFinger::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
	return GetControllerDescription();
}

FText UAnimGraphNode_TriggerFinger::GetTooltipText() const
{
	return LOCTEXT("Tooltip", "Curls and swings the index finger so its pad lands on a target in the hand's space: the trigger.");
}

FText UAnimGraphNode_TriggerFinger::GetControllerDescription() const
{
	return LOCTEXT("Title", "Trigger Finger");
}

#undef LOCTEXT_NAMESPACE
