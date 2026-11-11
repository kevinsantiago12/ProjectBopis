#include "AnimNode_ForearmTwist.h"

void FAnimNode_ForearmTwist::EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms)
{
	const FBoneContainer& BoneContainer = Output.Pose.GetPose().GetBoneContainer();
	const FCompactPoseBoneIndex LowerArmIndex = LowerArm.GetCompactPoseIndex(BoneContainer);
	const FCompactPoseBoneIndex HandIndex = Hand.GetCompactPoseIndex(BoneContainer);

	// The forearm's axis, from the reference pose: the way from the elbow to the wrist.
	const FTransform& HandRef = BoneContainer.GetRefPoseTransform(HandIndex);
	const double ForearmLength = HandRef.GetLocation().Size();
	if (ForearmLength < UE_KINDA_SMALL_NUMBER)
	{
		return;
	}
	const FVector Axis = HandRef.GetLocation() / ForearmLength;

	// The hand's roll about that axis, against its rest roll: what the twist bones share.
	const FTransform LowerArmCS = Output.Pose.GetComponentSpaceTransform(LowerArmIndex);
	const FQuat HandInForearm = LowerArmCS.GetRotation().Inverse() * Output.Pose.GetComponentSpaceTransform(HandIndex).GetRotation();
	const FQuat FromRest = HandInForearm * HandRef.GetRotation().Inverse();
	const double Roll = FromRest.GetTwistAngle(Axis);

	for (const FBoneReference& TwistBone : TwistBones)
	{
		// A lower LOD can drop a twist bone; one that isn't the forearm's child is left alone.
		if (!TwistBone.IsValidToEvaluate(BoneContainer))
		{
			continue;
		}
		const FCompactPoseBoneIndex TwistIndex = TwistBone.GetCompactPoseIndex(BoneContainer);
		if (BoneContainer.GetParentBoneIndex(TwistIndex) != LowerArmIndex)
		{
			continue;
		}

		// Its share is how far along the forearm it sits.
		const FTransform& TwistRef = BoneContainer.GetRefPoseTransform(TwistIndex);
		const double Share = FMath::Clamp(FVector::DotProduct(TwistRef.GetLocation(), Axis) / ForearmLength, 0.0, 1.0);

		FTransform Local = Output.Pose.GetComponentSpaceTransform(TwistIndex).GetRelativeTransform(LowerArmCS);
		Local.SetRotation(FQuat(Axis, Roll * Share) * TwistRef.GetRotation());
		OutBoneTransforms.Add(FBoneTransform(TwistIndex, Local * LowerArmCS));
	}

	// The base node applies them in bone order.
	OutBoneTransforms.Sort(FCompareBoneTransformIndex());
}

bool FAnimNode_ForearmTwist::IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones)
{
	return LowerArm.IsValidToEvaluate(RequiredBones) && Hand.IsValidToEvaluate(RequiredBones)
		&& RequiredBones.GetParentBoneIndex(Hand.GetCompactPoseIndex(RequiredBones)) == LowerArm.GetCompactPoseIndex(RequiredBones);
}

void FAnimNode_ForearmTwist::InitializeBoneReferences(const FBoneContainer& RequiredBones)
{
	LowerArm.Initialize(RequiredBones);
	Hand.Initialize(RequiredBones);
	for (FBoneReference& TwistBone : TwistBones)
	{
		TwistBone.Initialize(RequiredBones);
	}
}
