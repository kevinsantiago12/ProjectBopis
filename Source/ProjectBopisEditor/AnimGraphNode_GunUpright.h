#pragma once

#include "CoreMinimal.h"
#include "AnimGraphNode_SkeletalControlBase.h"
#include "AnimNode_GunUpright.h"
#include "AnimGraphNode_GunUpright.generated.h"

/** The Gun Upright node in Animation Blueprints (FAnimNode_GunUpright does the work). */
UCLASS()
class UAnimGraphNode_GunUpright : public UAnimGraphNode_SkeletalControlBase
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, Category = "Settings")
	FAnimNode_GunUpright Node;

	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;
	virtual FText GetTooltipText() const override;
	virtual const FAnimNode_SkeletalControlBase* GetNode() const override { return &Node; }

protected:
	virtual FText GetControllerDescription() const override;
};
