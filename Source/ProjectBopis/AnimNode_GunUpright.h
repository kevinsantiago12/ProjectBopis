#pragma once

#include "CoreMinimal.h"
#include "BoneControllers/AnimNode_SkeletalControlBase.h"
#include "AnimNode_GunUpright.generated.h"

/** Keeps the held gun from rolling as the aim moves up and down. The aim poses roll the gun about
    its barrel (up to ~15 degrees aiming high); this rolls the hand back about the barrel until the
    gun's sideways axis is level again. Works at any pitch, straight up included. Run it before the
    left hand is fitted to the gun, so a two-handed hold follows. */
USTRUCT(BlueprintInternalUseOnly)
struct PROJECTBOPIS_API FAnimNode_GunUpright : public FAnimNode_SkeletalControlBase
{
	GENERATED_BODY()

	/** The hand holding the gun. */
	UPROPERTY(EditAnywhere, Category = "Upright")
	FBoneReference Hand;

	/** The gun's barrel and its sideways axis, in the hand bone's space. The defaults follow the
	    HandGrip_R socket (yaw 90): barrel -X, sideways +Y. */
	UPROPERTY(EditAnywhere, Category = "Upright")
	FVector BarrelAxis = FVector(-1.0, 0.0, 0.0);

	UPROPERTY(EditAnywhere, Category = "Upright")
	FVector SideAxis = FVector(0.0, 1.0, 0.0);

	virtual void EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms) override;
	virtual bool IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones) override;

private:
	virtual void InitializeBoneReferences(const FBoneContainer& RequiredBones) override;
};
