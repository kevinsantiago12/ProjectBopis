#pragma once

#include "CoreMinimal.h"
#include "BoneControllers/AnimNode_SkeletalControlBase.h"
#include "AnimNode_UpperArmTwist.generated.h"

/** Keeps the shoulder from twisting with the upper arm. When the upper arm rolls about its own
    axis (aiming a one-handed pistol up rolls it ~50 degrees), its twist bones turn with it and the
    skin tears at the shoulder. This turns each twist bone back against that roll, in proportion to
    how near the shoulder it sits: all of it at the shoulder, none at the elbow. (The mannequin's
    post-process rig does this for its own mesh; our bodies don't run it.) */
USTRUCT(BlueprintInternalUseOnly)
struct PROJECTBOPIS_API FAnimNode_UpperArmTwist : public FAnimNode_SkeletalControlBase
{
	GENERATED_BODY()

	/** The upper arm: the twist bones' parent. Its roll is measured against its rest pose. */
	UPROPERTY(EditAnywhere, Category = "Twist")
	FBoneReference UpperArm;

	/** The next bone down the arm, which gives the upper arm's axis. */
	UPROPERTY(EditAnywhere, Category = "Twist")
	FBoneReference LowerArm;

	/** The upper arm's twist bones, children of UpperArm. */
	UPROPERTY(EditAnywhere, Category = "Twist")
	TArray<FBoneReference> TwistBones;

	virtual void EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms) override;
	virtual bool IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones) override;

private:
	virtual void InitializeBoneReferences(const FBoneContainer& RequiredBones) override;
};
