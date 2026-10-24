#pragma once

#include "CoreMinimal.h"
#include "UI/PlayerHUDElementWidget.h"
#include "WeaponWheelWidget.generated.h"

class AWeaponBase;
class UImage;
class UTextBlock;

/** How a segment reads: nothing carried, carried, the gun in hand, or under the highlight. */
UENUM(BlueprintType)
enum class EWheelSegmentState : uint8
{
	Empty,
	Carried,
	Equipped,
	Hovered
};

/**
 * The weapon wheel, GTA V style: a fixed ring of segments, one per weapon type (WeaponSlot 1..N,
 * counter-clockwise from the top), each showing the type's current weapon. Key mode (the number
 * keys): a key highlights its type, the same key again steps through that type's weapons, a
 * click equips. Pointer mode (a held key, a pad): pointing hovers, cycling steps, releasing
 * equips. The look lives in the designer (WBP_WeaponWheel): this class finds its widgets by
 * name and drives them while open —
 *   Segment_0..5        (Image)      tinted by state with the colours below
 *   Icon_0..5           (Image)      the weapon's icon; all icons share one height (IconMaxWidth)
 *   IconDual_0..5       (Image)      the second icon of a dual-wield pair; hidden otherwise
 *   Count_0..5          (TextBlock)  "2/3" when a type holds several; hidden otherwise
 *   NameText, AmmoText  (TextBlock)  the highlighted weapon (else the one in hand) and its ammo
 * Any of them may be left out. Segment i belongs at GetSegmentAngleDegrees(i) round the ring.
 */
UCLASS()
class PROJECTBOPIS_API UWeaponWheelWidget : public UPlayerHUDElementWidget
{
	GENERATED_BODY()

public:
	/** Shows the wheel, built from what's carried; the equipped weapon becomes its type's
	    current one. Key mode (the number keys): the highlight is set by SelectType and the
	    pointer is ignored. Pointer mode (a held key, a pad): the pointer rests in the middle. */
	void Open(bool bInKeyMode = false);

	void Close();

	bool IsOpen() const { return bOpen; }
	bool IsKeyMode() const { return bKeyMode; }

	/** Key mode: a number key. Highlights that type; the already highlighted type — or the type
	    of the gun in hand, on the first press — steps to its next weapon instead. */
	void SelectType(int32 Index);

	/** Moves the pointer: a mouse's movement, or a stick's value each frame (held over, it
	    saturates at the rim). Inside DeadZone nothing is hovered. */
	void AddPointerDelta(const FVector2D& Delta);

	/** Steps the hovered type's current weapon forward (+1) or back (−1), wrapping. */
	void CycleHovered(int32 Direction);

	/** The hovered type's current weapon, or null (nothing hovered, or an empty type). */
	AWeaponBase* GetHoveredWeapon() const;

	/** The highlighted segment, or −1 for none. */
	UFUNCTION(BlueprintPure, Category = "Weapon Wheel")
	int32 GetHoveredIndex() const;

	UFUNCTION(BlueprintPure, Category = "Weapon Wheel")
	EWheelSegmentState GetSegmentState(int32 Index) const;

	/** The segment's current weapon, or null for an empty type. */
	UFUNCTION(BlueprintPure, Category = "Weapon Wheel")
	AWeaponBase* GetSegmentWeapon(int32 Index) const;

	/** The segment's middle, in screen degrees (0 = right, clockwise positive, −90 = top). */
	UFUNCTION(BlueprintPure, Category = "Weapon Wheel")
	float GetSegmentAngleDegrees(int32 Index) const;

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** The highlight moved to Index (−1 for none). The tints are already set; this is for
	    animation on top. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Weapon Wheel")
	void OnHoverChanged(int32 Index);

	/** Sorts the carried weapons into their type's segment (pickup order within a type);
	    redone every frame while open. */
	void RebuildSegments();

	/** Pushes the current state into the designer's widgets. */
	void RefreshWidgets();

	/** Sets Image to Icon at Height and the texture's own proportions; hides it for null. */
	void ShowIcon(UImage* Image, UTexture2D* Icon, float Height) const;

	/** Segments round the ring, one per WeaponSlot from 1: six for pistols, shotguns, SMGs and
	    rifles, sniper, launcher and the free slot 1. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout", meta = (ClampMin = "1", ClampMax = "9"))
	int32 NumSegments = 6;

	/** Where segment 1 sits: screen degrees, −90 is the top. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout")
	float FirstSegmentAngleDegrees = -90.0f;

	/** Segments 1, 2, 3… run counter-clockwise from the first; off for clockwise. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout")
	bool bCounterClockwise = true;

	/** Distance from the centre to the middle of the ring as laid out in the designer, in
	    pixels: the pointer saturates here, and DeadZone is a fraction of it. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout", meta = (ClampMin = "40.0"))
	float Radius = 230.0f;

	/** Every icon on the wheel shares one height, each at its own proportions: the most that
	    lets every carried icon (a dual pair counting its spread) fit this width… */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout", meta = (ClampMin = "8.0"))
	float IconMaxWidth = 110.0f;

	/** …and never more than this, for when nothing long is carried. Set it to the long guns'
	    height to keep the icons one size whatever is carried. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout", meta = (ClampMin = "8.0"))
	float IconMaxHeight = 50.0f;

	/** A dual-wield weapon shows its icon twice, the second copy behind the first like a shadow,
	    this far from it (pixels; +X right, +Y down); the pair is centred where Icon_N sits.
	    IconDual_N draws the copy. Both are placed by render translation, so one set on them in
	    the designer is overridden. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout")
	FVector2D DualIconOffset = FVector2D(10.0, 8.0);

	/** How far from the centre, as a fraction of Radius, the pointer must be to hover anything. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float DeadZone = 0.3f;

	/** Pointer pixels per unit of input: a mouse delta is already pixels, a stick gives −1..1 a
	    frame, and both reach the rim in a flick at this. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout", meta = (ClampMin = "0.1"))
	float PointerScale = 10.0f;

	/** Look input counts up as positive; the screen counts down. Off if it points the wrong way. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout")
	bool bFlipPointerY = true;

	/** Seconds between cycle steps, so a held D-pad steps rather than spins. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Layout", meta = (ClampMin = "0.0"))
	float CycleRepeatDelay = 0.15f;

	/** Segment_N tints, by state. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Style")
	FLinearColor SegmentColor = FLinearColor(0.07f, 0.07f, 0.07f, 0.8f);

	/** A type with nothing carried. */
	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Style")
	FLinearColor EmptyColor = FLinearColor(0.04f, 0.04f, 0.04f, 0.5f);

	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Style")
	FLinearColor EquippedColor = FLinearColor(0.3f, 0.3f, 0.3f, 0.9f);

	UPROPERTY(EditAnywhere, Category = "Weapon Wheel|Style")
	FLinearColor HoverColor = FLinearColor(0.95f, 0.72f, 0.18f, 0.95f);

private:
	bool bOpen = false;
	bool bKeyMode = false;

	/** Key mode's highlighted type. */
	int32 KeyHighlight = INDEX_NONE;

	/** Where the pointer is, in pixels from the centre (pointer mode). */
	FVector2D Pointer = FVector2D::ZeroVector;

	/** Carried weapons per segment (type), pickup order. */
	TArray<TArray<TWeakObjectPtr<AWeaponBase>>> Segments;

	/** Each type's current weapon (index into its segment); kept between openings. */
	TArray<int32> Selected;

	double LastCycleTime = 0.0;

	/** What OnHoverChanged last reported. */
	int32 LastHovered = INDEX_NONE;

	// The designer's widgets, found by name on initialise; null where the layout has none.
	UPROPERTY(Transient)
	TArray<TObjectPtr<UImage>> SegmentImages;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UImage>> IconImages;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UImage>> IconDualImages;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UTextBlock>> CountTexts;

	// Named for the widget plus "Block": a C++ property with a designer widget's own name
	// clashes with the variable the Blueprint generates for that widget.
	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> NameTextBlock;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> AmmoTextBlock;
};
