#pragma once

#include "CoreMinimal.h"
#include "BoneControllers/AnimNode_SkeletalControlBase.h"
#include "AnimNode_ForearmTwist.generated.h"

/** Spreads the hand's roll along the forearm. Something that turns the hand after the clip (the
    left hand's grip lock on long guns) leaves the forearm's twist bones where the clip had them,
    so all of the roll shows at the wrist as a pinch. This turns each twist bone by the hand's
    roll about the forearm, in proportion to how far along the forearm it sits: none at the
    elbow, all of it at the wrist. Run it after whatever sets the hand. */
USTRUCT(BlueprintInternalUseOnly)
struct PROJECTBOPIS_API FAnimNode_ForearmTwist : public FAnimNode_SkeletalControlBase
{
	GENERATED_BODY()

	/** The forearm: the hand's and the twist bones' parent. */
	UPROPERTY(EditAnywhere, Category = "Twist")
	FBoneReference LowerArm;

	UPROPERTY(EditAnywhere, Category = "Twist")
	FBoneReference Hand;

	/** The forearm's twist bones, children of LowerArm. Each takes its share of the hand's roll. */
	UPROPERTY(EditAnywhere, Category = "Twist")
	TArray<FBoneReference> TwistBones;

	virtual void EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms) override;
	virtual bool IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones) override;

private:
	virtual void InitializeBoneReferences(const FBoneContainer& RequiredBones) override;
};
