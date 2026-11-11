#pragma once

#include "CoreMinimal.h"
#include "AnimGraphNode_SkeletalControlBase.h"
#include "AnimNode_ForearmTwist.h"
#include "AnimGraphNode_ForearmTwist.generated.h"

/** The Forearm Twist node in Animation Blueprints (FAnimNode_ForearmTwist does the work). */
UCLASS()
class UAnimGraphNode_ForearmTwist : public UAnimGraphNode_SkeletalControlBase
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, Category = "Settings")
	FAnimNode_ForearmTwist Node;

	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;
	virtual FText GetTooltipText() const override;
	virtual const FAnimNode_SkeletalControlBase* GetNode() const override { return &Node; }

protected:
	virtual FText GetControllerDescription() const override;
};
