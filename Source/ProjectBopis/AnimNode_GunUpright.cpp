#include "AnimNode_GunUpright.h"

void FAnimNode_GunUpright::EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms)
{
	const FBoneContainer& BoneContainer = Output.Pose.GetPose().GetBoneContainer();
	const FCompactPoseBoneIndex HandIndex = Hand.GetCompactPoseIndex(BoneContainer);
	FTransform HandCS = Output.Pose.GetComponentSpaceTransform(HandIndex);

	// The gun's barrel, sideways axis and top, in component space (Z is up).
	const FVector Barrel = HandCS.TransformVectorNoScale(BarrelAxis).GetSafeNormal();
	const FVector Side = HandCS.TransformVectorNoScale(SideAxis).GetSafeNormal();
	const FVector Top = FVector::CrossProduct(Barrel, Side);

	// Turning Side about the barrel by Angle gives Side cos + Top sin (Top = Barrel x Side, the
	// gun's bottom); it's level when that has no Z. Of the two answers, the smaller turn (never past
	// 90 degrees), so the gun is never turned upside down.
	const double Angle = FMath::Atan2(-Side.Z * FMath::Sign(Top.Z), FMath::Abs(Top.Z));
	HandCS.SetRotation(FQuat(Barrel, Angle) * HandCS.GetRotation());
	OutBoneTransforms.Add(FBoneTransform(HandIndex, HandCS));
}

bool FAnimNode_GunUpright::IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones)
{
	return Hand.IsValidToEvaluate(RequiredBones);
}

void FAnimNode_GunUpright::InitializeBoneReferences(const FBoneContainer& RequiredBones)
{
	Hand.Initialize(RequiredBones);
}
