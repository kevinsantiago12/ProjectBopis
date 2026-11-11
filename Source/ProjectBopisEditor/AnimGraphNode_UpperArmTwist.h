#pragma once

#include "CoreMinimal.h"
#include "AnimGraphNode_SkeletalControlBase.h"
#include "AnimNode_UpperArmTwist.h"
#include "AnimGraphNode_UpperArmTwist.generated.h"

/** The Upper Arm Twist node in Animation Blueprints (FAnimNode_UpperArmTwist does the work). */
UCLASS()
class UAnimGraphNode_UpperArmTwist : public UAnimGraphNode_SkeletalControlBase
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, Category = "Settings")
	FAnimNode_UpperArmTwist Node;

	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;
	virtual FText GetTooltipText() const override;
	virtual const FAnimNode_SkeletalControlBase* GetNode() const override { return &Node; }

protected:
	virtual FText GetControllerDescription() const override;
};
