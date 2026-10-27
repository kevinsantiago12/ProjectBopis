#include "UI/WeaponWheelWidget.h"
#include "ProjectBopisCharacter.h"
#include "Weapons/WeaponHolderComponent.h"
#include "Weapons/WeaponBase.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"
#include "HAL/PlatformTime.h"

namespace
{
	/** Width over height. */
	float IconAspect(const UTexture2D* Icon)
	{
		return FMath::Max(1, Icon->GetSizeX()) / static_cast<float>(FMath::Max(1, Icon->GetSizeY()));
	}
}

void UWeaponWheelWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// The designer's widgets, by name; a missing one just isn't driven.
	SegmentImages.SetNum(NumSegments);
	IconImages.SetNum(NumSegments);
	CountTexts.SetNum(NumSegments);
	IconDualImages.SetNum(NumSegments);
	for (int32 Index = 0; Index < NumSegments; ++Index)
	{
		SegmentImages[Index] = Cast<UImage>(GetWidgetFromName(*FString::Printf(TEXT("Segment_%d"), Index)));
		IconImages[Index] = Cast<UImage>(GetWidgetFromName(*FString::Printf(TEXT("Icon_%d"), Index)));
		IconDualImages[Index] = Cast<UImage>(GetWidgetFromName(*FString::Printf(TEXT("IconDual_%d"), Index)));
		CountTexts[Index] = Cast<UTextBlock>(GetWidgetFromName(*FString::Printf(TEXT("Count_%d"), Index)));
	}
	NameTextBlock = Cast<UTextBlock>(GetWidgetFromName(TEXT("NameText")));
	AmmoTextBlock = Cast<UTextBlock>(GetWidgetFromName(TEXT("AmmoText")));
}

void UWeaponWheelWidget::NativeConstruct()
{
	Super::NativeConstruct();
	SetVisibility(ESlateVisibility::Collapsed);
}

void UWeaponWheelWidget::Open(bool bInKeyMode)
{
	bOpen = true;
	bKeyMode = bInKeyMode;
	KeyHighlight = INDEX_NONE;
	LastHovered = INDEX_NONE;
	Pointer = FVector2D::ZeroVector;
	RebuildSegments();

	// The gun in hand is its type's current weapon.
	if (const AWeaponBase* Equipped = GetEquippedWeapon())
	{
		for (int32 Index = 0; Index < Segments.Num(); ++Index)
		{
			const int32 Found = Segments[Index].IndexOfByPredicate([Equipped](const TWeakObjectPtr<AWeaponBase>& W) { return W.Get() == Equipped; });
			if (Found != INDEX_NONE)
			{
				Selected[Index] = Found;
			}
		}
	}
	RefreshWidgets();
	SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UWeaponWheelWidget::Close()
{
	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
}

void UWeaponWheelWidget::AddPointerDelta(const FVector2D& Delta)
{
	if (!bOpen)
	{
		return;
	}
	Pointer += FVector2D(Delta.X, bFlipPointerY ? -Delta.Y : Delta.Y) * PointerScale;
	Pointer = Pointer.GetClampedToMaxSize(Radius);
}

void UWeaponWheelWidget::SelectType(int32 Index)
{
	if (!bOpen || !Segments.IsValidIndex(Index))
	{
		return;
	}

	// The same type again steps through its weapons; so does the first press on the type of
	// the gun in hand, since that one's already showing. Any other type is just highlighted.
	const bool bRepeat = KeyHighlight == Index;
	KeyHighlight = Index;
	const int32 Num = Segments[Index].Num();
	if (Num > 1 && (bRepeat || GetSegmentWeapon(Index) == GetEquippedWeapon()))
	{
		Selected[Index] = (Selected[Index] + 1) % Num;
	}
	RefreshWidgets();
}

void UWeaponWheelWidget::CycleHovered(int32 Direction)
{
	const int32 Index = GetHoveredIndex();
	const double Now = FPlatformTime::Seconds();
	if (Index == INDEX_NONE || Direction == 0 || Segments[Index].Num() < 2 || Now - LastCycleTime < CycleRepeatDelay)
	{
		return;
	}
	LastCycleTime = Now;
	const int32 Num = Segments[Index].Num();
	Selected[Index] = (Selected[Index] + (Direction > 0 ? 1 : Num - 1)) % Num;
	RefreshWidgets();
}

AWeaponBase* UWeaponWheelWidget::GetHoveredWeapon() const
{
	return GetSegmentWeapon(GetHoveredIndex());
}

AWeaponBase* UWeaponWheelWidget::GetSegmentWeapon(int32 Index) const
{
	if (!Segments.IsValidIndex(Index) || !Segments[Index].IsValidIndex(Selected[Index]))
	{
		return nullptr;
	}
	return Segments[Index][Selected[Index]].Get();
}

EWheelSegmentState UWeaponWheelWidget::GetSegmentState(int32 Index) const
{
	if (!Segments.IsValidIndex(Index))
	{
		return EWheelSegmentState::Empty;
	}
	if (Index == GetHoveredIndex())
	{
		return EWheelSegmentState::Hovered;
	}
	const AWeaponBase* Weapon = GetSegmentWeapon(Index);
	if (!Weapon)
	{
		return EWheelSegmentState::Empty;
	}
	return Weapon == GetEquippedWeapon() ? EWheelSegmentState::Equipped : EWheelSegmentState::Carried;
}

float UWeaponWheelWidget::GetSegmentAngleDegrees(int32 Index) const
{
	const float Arc = 360.0f / FMath::Max(1, NumSegments);
	const float Direction = bCounterClockwise ? -1.0f : 1.0f;
	return FirstSegmentAngleDegrees + Direction * Arc * Index;
}

void UWeaponWheelWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (bOpen)
	{
		RebuildSegments();
		RefreshWidgets();
	}
}

void UWeaponWheelWidget::RebuildSegments()
{
	Segments.SetNum(NumSegments);
	Selected.SetNum(NumSegments);
	for (TArray<TWeakObjectPtr<AWeaponBase>>& Segment : Segments)
	{
		Segment.Reset();
	}

	const AProjectBopisCharacter* Player = GetPlayerCharacter();
	const UWeaponHolderComponent* Holder = Player ? Player->GetWeaponHolder() : nullptr;
	if (Holder)
	{
		for (AWeaponBase* Weapon : Holder->GetCarriedWeapons())
		{
			const int32 Index = Weapon ? Weapon->GetWeaponSlot() - 1 : INDEX_NONE;
			if (Segments.IsValidIndex(Index))
			{
				Segments[Index].Add(Weapon);
			}
		}
	}

	for (int32 Index = 0; Index < NumSegments; ++Index)
	{
		Selected[Index] = FMath::Clamp(Selected[Index], 0, FMath::Max(0, Segments[Index].Num() - 1));
	}
}

int32 UWeaponWheelWidget::GetHoveredIndex() const
{
	if (!bOpen || NumSegments < 1)
	{
		return INDEX_NONE;
	}
	if (bKeyMode)
	{
		return Segments.IsValidIndex(KeyHighlight) ? KeyHighlight : INDEX_NONE;
	}
	if (Pointer.Size() < DeadZone * Radius)
	{
		return INDEX_NONE;
	}

	// How far round from the first segment, the way the segments run; half a segment added so
	// each one is centred on its angle.
	const float Arc = 2.0f * PI / NumSegments;
	const float Direction = bCounterClockwise ? -1.0f : 1.0f;
	const float PointerAngle = FMath::Atan2(Pointer.Y, Pointer.X);
	float FromFirst = Direction * (PointerAngle - FMath::DegreesToRadians(FirstSegmentAngleDegrees)) + Arc * 0.5f;
	FromFirst = FMath::Fmod(FromFirst + 4.0f * PI, 2.0f * PI);
	return FMath::Clamp(static_cast<int32>(FromFirst / Arc), 0, NumSegments - 1);
}

void UWeaponWheelWidget::RefreshWidgets()
{
	const int32 Hovered = GetHoveredIndex();
	const AWeaponBase* Equipped = GetEquippedWeapon();

	// One height for every icon, set by the handguns: the most that lets each carried handgun
	// fill HandgunFill of its wedge, so cycling them doesn't resize the wheel. Longer guns may
	// run past their wedge at this height. With no handgun carried, the last height holds.
	const int32 HandgunIndex = HandgunSlot - 1;
	if (Segments.IsValidIndex(HandgunIndex))
	{
		float Fitted = TNumericLimits<float>::Max();
		for (const TWeakObjectPtr<AWeaponBase>& Carried : Segments[HandgunIndex])
		{
			if (const UTexture2D* Icon = Carried.IsValid() ? Carried->GetIcon() : nullptr)
			{
				Fitted = FMath::Min(Fitted, FitIconHeight(HandgunIndex, IconAspect(Icon)));
			}
		}
		if (Fitted < TNumericLimits<float>::Max())
		{
			SharedIconHeight = Fitted * HandgunFill;
		}
	}

	for (int32 Index = 0; Index < NumSegments; ++Index)
	{
		const AWeaponBase* Weapon = GetSegmentWeapon(Index);

		if (UImage* Segment = SegmentImages.IsValidIndex(Index) ? SegmentImages[Index].Get() : nullptr)
		{
			switch (GetSegmentState(Index))
			{
			case EWheelSegmentState::Hovered:  Segment->SetColorAndOpacity(HoverColor); break;
			case EWheelSegmentState::Equipped: Segment->SetColorAndOpacity(EquippedColor); break;
			case EWheelSegmentState::Carried:  Segment->SetColorAndOpacity(SegmentColor); break;
			default:                           Segment->SetColorAndOpacity(EmptyColor); break;
			}
		}

		// A dual-wield weapon shows its icon twice, the pair either side of the single icon's spot.
		UTexture2D* Icon = Weapon ? Weapon->GetIcon() : nullptr;
		UImage* DualImage = IconDualImages.IsValidIndex(Index) ? IconDualImages[Index].Get() : nullptr;
		const bool bDual = Icon && DualImage && Weapon->IsDualWield();
		const FVector2D IconSize = Icon ? FVector2D(SharedIconHeight * IconAspect(Icon), SharedIconHeight) : FVector2D::ZeroVector;
		const FVector2D DualOffset = DualIconSpread * IconSize;
		if (UImage* IconImage = IconImages.IsValidIndex(Index) ? IconImages[Index].Get() : nullptr)
		{
			ShowIcon(IconImage, Icon, SharedIconHeight);
			IconImage->SetRenderTranslation(bDual ? -DualOffset * 0.5 : FVector2D::ZeroVector);
		}
		if (DualImage)
		{
			ShowIcon(DualImage, bDual ? Icon : nullptr, SharedIconHeight);
			DualImage->SetRenderTranslation(DualOffset * 0.5);
		}

		if (UTextBlock* Count = CountTexts.IsValidIndex(Index) ? CountTexts[Index].Get() : nullptr)
		{
			const int32 Num = Segments[Index].Num();
			Count->SetText(FText::Format(NSLOCTEXT("WeaponWheel", "Count", "{0}/{1}"), Selected[Index] + 1, Num));
			Count->SetVisibility(Num > 1 ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
		}
	}

	// The centre: the hovered type's weapon, else the one in hand.
	const AWeaponBase* Shown = Hovered != INDEX_NONE ? GetSegmentWeapon(Hovered) : Equipped;
	if (NameTextBlock)
	{
		NameTextBlock->SetText(Shown ? Shown->GetDisplayName() : FText::GetEmpty());
	}
	if (AmmoTextBlock)
	{
		AmmoTextBlock->SetText(Shown ? FText::Format(NSLOCTEXT("WeaponWheel", "Ammo", "{0} / {1}"), Shown->GetAmmoInMagazine(), Shown->GetReserveAmmo()) : FText::GetEmpty());
	}

	if (Hovered != LastHovered)
	{
		LastHovered = Hovered;
		OnHoverChanged(Hovered);
	}
}

void UWeaponWheelWidget::ShowIcon(UImage* Image, UTexture2D* Icon, float Height) const
{
	if (Icon)
	{
		FSlateBrush Brush = Image->GetBrush();
		Brush.SetResourceObject(Icon);
		Brush.ImageSize = FVector2D(Height * IconAspect(Icon), Height);
		Image->SetBrush(Brush);   // does nothing when the brush is unchanged
	}
	Image->SetVisibility(Icon ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
}

float UWeaponWheelWidget::FitIconHeight(int32 Index, float Aspect) const
{
	// The wedge in screen space (+Y down): the icon's spot at Radius on its centre line, and the
	// directions of its two edges.
	const float Angle = FMath::DegreesToRadians(GetSegmentAngleDegrees(Index));
	const float HalfArc = FMath::DegreesToRadians(SegmentArcDegrees * 0.5f);
	const FVector2D Centre = FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * Radius;
	const FVector2D EdgeA(FMath::Cos(Angle - HalfArc), FMath::Sin(Angle - HalfArc));
	const FVector2D EdgeB(FMath::Cos(Angle + HalfArc), FMath::Sin(Angle + HalfArc));

	// Whether an icon this tall fits: every corner inside the outer rim and between the two
	// edges (the wedge is convex there), and its point nearest the centre outside the inner rim.
	auto Fits = [&](float Height)
	{
		const FVector2D Half = FVector2D(Height * Aspect, Height) * 0.5;
		for (const FVector2D& Sign : { FVector2D(-1.0, -1.0), FVector2D(1.0, -1.0), FVector2D(-1.0, 1.0), FVector2D(1.0, 1.0) })
		{
			const FVector2D Corner = Centre + Half * Sign;
			if (Corner.Size() > RingOuterRadius - IconMargin
				|| FVector2D::CrossProduct(EdgeA, Corner) < IconMargin
				|| FVector2D::CrossProduct(Corner, EdgeB) < IconMargin)
			{
				return false;
			}
		}
		const FVector2D Nearest(FMath::Clamp(0.0, Centre.X - Half.X, Centre.X + Half.X),
			FMath::Clamp(0.0, Centre.Y - Half.Y, Centre.Y + Half.Y));
		return Nearest.Size() >= RingInnerRadius + IconMargin;
	};

	// A bigger icon on the same spot always covers a smaller one, so halve the gap between too
	// small and too big until it's under half a pixel.
	float Low = 0.0f;
	float High = RingOuterRadius * 2.0f;
	while (High - Low > 0.5f)
	{
		const float Mid = (Low + High) * 0.5f;
		if (Fits(Mid))
		{
			Low = Mid;
		}
		else
		{
			High = Mid;
		}
	}
	return Low;
}
