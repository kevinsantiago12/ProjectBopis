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

	// One height for every icon: the most that lets each carried icon fit IconMaxWidth (a dual
	// pair counting its spread), capped at IconMaxHeight. All carried weapons count, not just
	// the ones showing, so cycling a type doesn't resize the wheel.
	float IconHeight = IconMaxHeight;
	for (const TArray<TWeakObjectPtr<AWeaponBase>>& Segment : Segments)
	{
		for (const TWeakObjectPtr<AWeaponBase>& Carried : Segment)
		{
			const AWeaponBase* Weapon = Carried.Get();
			if (const UTexture2D* Icon = Weapon ? Weapon->GetIcon() : nullptr)
			{
				const float Width = IconMaxWidth - (Weapon->IsDualWield() ? FMath::Abs(DualIconOffset.X) : 0.0f);
				IconHeight = FMath::Min(IconHeight, FMath::Max(1.0f, Width) / IconAspect(Icon));
			}
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
		if (UImage* IconImage = IconImages.IsValidIndex(Index) ? IconImages[Index].Get() : nullptr)
		{
			ShowIcon(IconImage, Icon, IconHeight);
			IconImage->SetRenderTranslation(bDual ? -DualIconOffset * 0.5 : FVector2D::ZeroVector);
		}
		if (DualImage)
		{
			ShowIcon(DualImage, bDual ? Icon : nullptr, IconHeight);
			DualImage->SetRenderTranslation(DualIconOffset * 0.5);
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
