#include "AnimNode_TriggerFinger.h"

namespace
{
	/** Signed angle (radians) from A to B, turning about Axis (a unit vector). */
	double AngleAbout(const FVector& A, const FVector& B, const FVector& Axis)
	{
		return FMath::Atan2(FVector::DotProduct(FVector::CrossProduct(A, B), Axis), FVector::DotProduct(A, B));
	}
}

void FAnimNode_TriggerFinger::EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms)
{
	const FBoneContainer& Bones = Output.Pose.GetPose().GetBoneContainer();
	const FCompactPoseBoneIndex HandIndex = Hand.GetCompactPoseIndex(Bones);
	const FCompactPoseBoneIndex KnuckleIndex = Knuckle.GetCompactPoseIndex(Bones);
	const FCompactPoseBoneIndex MiddleIndex = Middle.GetCompactPoseIndex(Bones);
	const FCompactPoseBoneIndex LastIndex = Last.GetCompactPoseIndex(Bones);

	const FVector Goal = Output.Pose.GetComponentSpaceTransform(HandIndex).TransformPosition(Target);
	FTransform KnuckleCS = Output.Pose.GetComponentSpaceTransform(KnuckleIndex);
	FTransform MiddleCS = Output.Pose.GetComponentSpaceTransform(MiddleIndex);
	FTransform LastCS = Output.Pose.GetComponentSpaceTransform(LastIndex);

	const FVector P1 = KnuckleCS.GetLocation();
	const FVector P2 = MiddleCS.GetLocation();
	const FVector P3 = LastCS.GetLocation();

	// The pad lies on past the last joint, along its bone. Which way a bone's X runs depends on the
	// side of the body, so it's turned to point away from the middle joint.
	FVector LastAxis = LastCS.GetUnitAxis(EAxis::X);
	if (FVector::DotProduct(LastAxis, P3 - P2) < 0.0)
	{
		LastAxis = -LastAxis;
	}
	const FVector D1 = P2 - P1;
	const FVector D2 = P3 - P2;
	const FVector D3 = LastAxis * PadLength;
	if (D1.SizeSquared() < KINDA_SMALL_NUMBER || D2.SizeSquared() < KINDA_SMALL_NUMBER)
	{
		return;
	}

	// The axis the finger curls about: its own flexion axis, from the middle joint. (Taking the bend
	// it came in with failed on a straight finger: it curled any which way, up over the slide.)
	FVector Axis = MiddleCS.TransformVectorNoScale(CurlAxis);
	if (!Axis.Normalize())
	{
		return;
	}

	// Each joint is set to a curl about Axis; these turns take it there from the curl it came in with.
	const double MiddleIn = AngleAbout(D1, D2, Axis);
	const double LastIn = AngleAbout(D2, D3, Axis);
	const auto MiddleTurnTo = [Axis, MiddleIn](double Curl) { return FQuat(Axis, Curl - MiddleIn); };

	// The trigger rests on the middle segment, ContactAlong of the way along it. The middle joint
	// curls until that spot is as far from the knuckle as the trigger (curling brings it closer):
	// halve the range until it's found. The last joint wraps round the trigger.
	const double Wanted = (Goal - P1).Size();
	const FVector Spot = D2 * ContactAlong;
	const auto SpotReach = [D1, Spot, MiddleTurnTo](double Curl) { return (D1 + MiddleTurnTo(Curl).RotateVector(Spot)).Size(); };
	double MiddleCurl = 0.0;
	double LastCurl = FMath::DegreesToRadians(TipWrap);
	const bool bSlideOut = Wanted >= SpotReach(0.0);
	if (!bSlideOut)
	{
		double Low = 0.0;
		double High = FMath::DegreesToRadians(MaxCurl);
		for (int32 Step = 0; Step < 24 && High - Low > 1.0e-4; ++Step)
		{
			const double Mid = 0.5 * (Low + High);
			if (SpotReach(Mid) > Wanted)
			{
				Low = Mid;      // still too far: curl more
			}
			else
			{
				High = Mid;
			}
		}
		MiddleCurl = 0.5 * (Low + High);
	}
	else if (Wanted > (D1 + MiddleTurnTo(0.0).RotateVector(D2)).Size())
	{
		// Out past the middle segment (the M4): the last joint straightens too.
		LastCurl = 0.0;
	}

	const FQuat MiddleTurn = MiddleTurnTo(MiddleCurl);
	const FQuat LastTurn(Axis, LastCurl - LastIn);
	const FVector NewD2 = MiddleTurn.RotateVector(D2);
	const FVector NewP3 = P2 + NewD2;
	const FVector NewPad = NewP3 + (LastTurn * MiddleTurn).RotateVector(D3);
	MiddleCS.SetRotation(MiddleTurn * MiddleCS.GetRotation());
	LastCS.SetRotation(LastTurn * MiddleTurn * LastCS.GetRotation());

	// Where the trigger touches. Further than the spot reaches with the finger straight, the finger
	// stays straight at the middle joint and the trigger rests further out along it: the point as far
	// from the knuckle as the trigger, on the middle segment or past it (the pad, if further still).
	FVector Contact = P2 + NewD2 * ContactAlong;
	if (bSlideOut)
	{
		Contact = NewPad;
		const FVector Joints[] = { P2, NewP3, NewPad };
		for (int32 Segment = 0; Segment < 2; ++Segment)
		{
			const FVector From = Joints[Segment] - P1;
			const FVector Along = Joints[Segment + 1] - Joints[Segment];
			const double AlongSquared = Along.SizeSquared();
			if (AlongSquared > KINDA_SMALL_NUMBER && Wanted <= (Joints[Segment + 1] - P1).Size())
			{
				// Where on this segment the distance from the knuckle is Wanted: |From + Along * T| = Wanted.
				const double B = FVector::DotProduct(From, Along);
				const double Root = FMath::Sqrt(FMath::Max(B * B - AlongSquared * (From.SizeSquared() - Wanted * Wanted), 0.0));
				Contact = Joints[Segment] + Along * FMath::Clamp((Root - B) / AlongSquared, 0.0, 1.0);
				break;
			}
		}
	}

	// Swing the whole finger at the knuckle so the contact lands on the trigger (capped at MaxSwing).
	FQuat Swing = FQuat::FindBetweenVectors(Contact - P1, Goal - P1);
	FVector SwingAxis;
	double SwingAngle = 0.0;
	Swing.ToAxisAndAngle(SwingAxis, SwingAngle);
	const double MaxSwingRadians = FMath::DegreesToRadians(MaxSwing);
	if (SwingAngle > MaxSwingRadians)
	{
		Swing = FQuat(SwingAxis, MaxSwingRadians);
	}

	KnuckleCS.SetRotation(Swing * KnuckleCS.GetRotation());
	MiddleCS.SetLocation(P1 + Swing.RotateVector(D1));
	MiddleCS.SetRotation(Swing * MiddleCS.GetRotation());
	LastCS.SetLocation(P1 + Swing.RotateVector(NewP3 - P1));
	LastCS.SetRotation(Swing * LastCS.GetRotation());

	// Parents before children, as the base node requires.
	OutBoneTransforms.Add(FBoneTransform(KnuckleIndex, KnuckleCS));
	OutBoneTransforms.Add(FBoneTransform(MiddleIndex, MiddleCS));
	OutBoneTransforms.Add(FBoneTransform(LastIndex, LastCS));
}

bool FAnimNode_TriggerFinger::IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones)
{
	return Hand.IsValidToEvaluate(RequiredBones) && Knuckle.IsValidToEvaluate(RequiredBones)
		&& Middle.IsValidToEvaluate(RequiredBones) && Last.IsValidToEvaluate(RequiredBones);
}

void FAnimNode_TriggerFinger::InitializeBoneReferences(const FBoneContainer& RequiredBones)
{
	Hand.Initialize(RequiredBones);
	Knuckle.Initialize(RequiredBones);
	Middle.Initialize(RequiredBones);
	Last.Initialize(RequiredBones);
}
