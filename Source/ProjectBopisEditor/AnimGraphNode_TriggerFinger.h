#pragma once

#include "CoreMinimal.h"
#include "AnimGraphNode_SkeletalControlBase.h"
#include "AnimNode_TriggerFinger.h"
#include "AnimGraphNode_TriggerFinger.generated.h"

/** The Trigger Finger node in Animation Blueprints (FAnimNode_TriggerFinger does the work). */
UCLASS()
class UAnimGraphNode_TriggerFinger : public UAnimGraphNode_SkeletalControlBase
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, Category = "Settings")
	FAnimNode_TriggerFinger Node;

	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;
	virtual FText GetTooltipText() const override;
	virtual const FAnimNode_SkeletalControlBase* GetNode() const override { return &Node; }

protected:
	virtual FText GetControllerDescription() const override;
};
