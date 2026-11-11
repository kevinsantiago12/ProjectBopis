#include "AnimNode_UpperArmTwist.h"

void FAnimNode_UpperArmTwist::EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms)
{
	const FBoneContainer& BoneContainer = Output.Pose.GetPose().GetBoneContainer();
	const FCompactPoseBoneIndex UpperArmIndex = UpperArm.GetCompactPoseIndex(BoneContainer);
	const FCompactPoseBoneIndex ParentIndex = BoneContainer.GetParentBoneIndex(UpperArmIndex);
	const FCompactPoseBoneIndex LowerArmIndex = LowerArm.GetCompactPoseIndex(BoneContainer);
	if (!ParentIndex.IsValid())
	{
		return;
	}

	// The upper arm's axis, in its own frame: the way to the elbow in the reference pose.
	const FTransform& LowerArmRef = BoneContainer.GetRefPoseTransform(LowerArmIndex);
	const double Length = LowerArmRef.GetLocation().Size();
	if (Length < UE_KINDA_SMALL_NUMBER)
	{
		return;
	}
	const FVector Axis = LowerArmRef.GetLocation() / Length;

	// How far the upper arm has rolled about that axis since its rest pose (in its own frame).
	const FTransform& UpperArmRef = BoneContainer.GetRefPoseTransform(UpperArmIndex);
	const FTransform UpperArmCS = Output.Pose.GetComponentSpaceTransform(UpperArmIndex);
	const FQuat InParent = Output.Pose.GetComponentSpaceTransform(ParentIndex).GetRotation().Inverse() * UpperArmCS.GetRotation();
	const FQuat FromRest = UpperArmRef.GetRotation().Inverse() * InParent;
	const double Roll = FromRest.GetTwistAngle(Axis);

	for (const FBoneReference& TwistBone : TwistBones)
	{
		// A lower LOD can drop a twist bone; one that isn't the upper arm's child is left alone.
		if (!TwistBone.IsValidToEvaluate(BoneContainer))
		{
			continue;
		}
		const FCompactPoseBoneIndex TwistIndex = TwistBone.GetCompactPoseIndex(BoneContainer);
		if (BoneContainer.GetParentBoneIndex(TwistIndex) != UpperArmIndex)
		{
			continue;
		}

		// Turned back by the share of the roll the shoulder end shouldn't take: all of it at the
		// shoulder, none at the elbow.
		const FTransform& TwistRef = BoneContainer.GetRefPoseTransform(TwistIndex);
		const double Along = FMath::Clamp(FVector::DotProduct(TwistRef.GetLocation(), Axis) / Length, 0.0, 1.0);

		FTransform Local = Output.Pose.GetComponentSpaceTransform(TwistIndex).GetRelativeTransform(UpperArmCS);
		Local.SetRotation(FQuat(Axis, -Roll * (1.0 - Along)) * TwistRef.GetRotation());
		OutBoneTransforms.Add(FBoneTransform(TwistIndex, Local * UpperArmCS));
	}

	// The base node applies them in bone order.
	OutBoneTransforms.Sort(FCompareBoneTransformIndex());
}

bool FAnimNode_UpperArmTwist::IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones)
{
	return UpperArm.IsValidToEvaluate(RequiredBones) && LowerArm.IsValidToEvaluate(RequiredBones);
}

void FAnimNode_UpperArmTwist::InitializeBoneReferences(const FBoneContainer& RequiredBones)
{
	UpperArm.Initialize(RequiredBones);
	LowerArm.Initialize(RequiredBones);
	for (FBoneReference& TwistBone : TwistBones)
	{
		TwistBone.Initialize(RequiredBones);
	}
}
