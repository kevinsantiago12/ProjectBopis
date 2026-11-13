#pragma once

#include "CoreMinimal.h"
#include "BoneControllers/AnimNode_SkeletalControlBase.h"
#include "AnimNode_TriggerFinger.generated.h"

/** Rests the trigger finger's middle segment on the trigger, wherever the gun puts it, the tip
    wrapping round it. The finger curls about its own flexion axis (CurlAxis): the middle joint until
    the spot ContactAlong of the way along the middle segment is as far from the knuckle as the
    trigger, the last joint by TipWrap. A trigger further out than that spot reaches with the finger
    straight rests further out along the finger instead (the M4's on the last segment). Then the
    whole finger swings at the knuckle to land on it. The target is in the hand bone's space: a gun
    held in the hand keeps the same target whatever the arm does. */
USTRUCT(BlueprintInternalUseOnly)
struct PROJECTBOPIS_API FAnimNode_TriggerFinger : public FAnimNode_SkeletalControlBase
{
	GENERATED_BODY()

	/** The hand; Target is in its space. */
	UPROPERTY(EditAnywhere, Category = "Finger")
	FBoneReference Hand;

	/** The finger's joints: knuckle (index_01), middle (index_02) and last (index_03). */
	UPROPERTY(EditAnywhere, Category = "Finger")
	FBoneReference Knuckle;

	UPROPERTY(EditAnywhere, Category = "Finger")
	FBoneReference Middle;

	UPROPERTY(EditAnywhere, Category = "Finger")
	FBoneReference Last;

	/** Where the pad goes, in the hand bone's space. */
	UPROPERTY(EditAnywhere, Category = "Finger", meta = (PinShownByDefault))
	FVector Target = FVector::ZeroVector;

	/** From the last joint to the middle of the pad, along the finger (cm): where the finger ends, for
	    a trigger out past the middle segment. */
	UPROPERTY(EditAnywhere, Category = "Finger", meta = (ClampMin = "0.0"))
	float PadLength = 2.0f;

	/** The axis the finger bends about, in the middle joint's own space: a finger only curls one
	    way. Manny's fingers curl about -Z on both hands. */
	UPROPERTY(EditAnywhere, Category = "Finger")
	FVector CurlAxis = FVector(0.0, 0.0, -1.0);

	/** Where the trigger rests on the middle segment (index_02 to index_03): 0 at the middle joint,
	    1 at the last. */
	UPROPERTY(EditAnywhere, Category = "Finger", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float ContactAlong = 0.5f;

	/** How far the last joint curls round the trigger (degrees). */
	UPROPERTY(EditAnywhere, Category = "Finger", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float TipWrap = 40.0f;

	/** Most the middle joint curls (degrees). */
	UPROPERTY(EditAnywhere, Category = "Finger", meta = (ClampMin = "0.0", ClampMax = "150.0"))
	float MaxCurl = 120.0f;

	/** Most the knuckle swings off the incoming pose (degrees). A trigger out of reach gets
	    pointed at, not reached by bending the finger somewhere it can't go. */
	UPROPERTY(EditAnywhere, Category = "Finger", meta = (ClampMin = "0.0", ClampMax = "90.0"))
	float MaxSwing = 40.0f;

	virtual void EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms) override;
	virtual bool IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones) override;

private:
	virtual void InitializeBoneReferences(const FBoneContainer& RequiredBones) override;
};
