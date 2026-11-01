# Writes the UMG clipboard text for the bottom-left HUD's item pieces (spec *HUD: cinematic
# minimal -> Item strip*), one file each next to this script: WBP_WeaponIcon_Tree.txt,
# WBP_Ammo_Tree.txt, WBP_FirstAid_Tree.txt, WBP_Grenades_Tree.txt; -Clipboard <piece> also copies
# that one. In the Widget Blueprint: delete the old root (if any), click the empty Hierarchy,
# Ctrl+V, compile, save.
#
# Each piece's root is a Scale Box. The weapon icon's doesn't scale (Stretch None): every gun is
# drawn UAmmoWidget's IconHeight tall at its own proportions, one standard scale, so a long gun is
# long; it's right-aligned (towards the numbers) and centred in the widget's box, and overflows
# the box to the left. The others scale to their box's height (left-aligned, so a longer number
# grows to the right). Sizes are GPT's mockup x 0.40 in 1080p px; the whole HUD is scaled as one.
# The widget names are the contract with the C++ (UAmmoWidget: WeaponIcon, MagazineText,
# ReserveText; UHUDCountWidget: Count). WBP_WeaponIcon and WBP_Ammo both derive from UAmmoWidget,
# each holding the part it shows.
#
# WBP_ItemStrip_Tree.txt groups the pieces into one widget (user: "I need to scale that entire
# section uniformly"): a Scale Box holding a Canvas with WBP_WeaponIcon, WBP_Ammo, two divider
# Images, WBP_FirstAid and WBP_Grenades at the places the user gave them in WBP_PlayerHUD (read
# 2026-10-31, made relative to the group's top-left). Resizing its box scales them all together.
param([ValidateSet("WeaponIcon", "Ammo", "FirstAid", "Grenades", "ItemStrip")][string]$Clipboard)

$inv = [Globalization.CultureInfo]::InvariantCulture
function F([double]$v) { return $v.ToString("F6", $inv) }

$bold = "/Script/Engine.Font'/Game/antonio/Antonio-Bold_Font.Antonio-Bold_Font'"
# M_HUDIcon (the stroke); its default Texture, the 9mm icon, is the Designer preview.
# UAmmoWidget puts the equipped weapon's icon into its "Texture" parameter at runtime.
$weaponIcon = "/Script/Engine.MaterialInstanceConstant'/Game/UI/HUD/MI_HUD_WeaponIcon.MI_HUD_WeaponIcon'"
$firstAidIcon = "/Script/Engine.Texture2D'/Game/UI/HUD/T_HUD_Icon_FirstAid.T_HUD_Icon_FirstAid'"
$grenadeIcon = "/Script/Engine.Texture2D'/Game/UI/HUD/T_HUD_Icon_Grenade.T_HUD_Icon_Grenade'"

# $grey is linear: the mockup's reserve grey is sRGB 0.65, linear 0.38.
function Text([string]$name, [string]$text, $size, [double]$grey = 1.0) {
  return "Begin Object Class=/Script/UMG.TextBlock Name=`"$name`"`r`n" +
    "   Text=INVTEXT(`"$text`")`r`n" +
    "   ColorAndOpacity=(SpecifiedColor=(R=$(F $grey),G=$(F $grey),B=$(F $grey),A=1.000000))`r`n" +
    "   Font=(FontObject=`"$bold`",TypefaceFontName=`"Default`",Size=$(F $size))`r`n" +
    "End Object"
}

function Image([string]$name, [string]$texture, $w, $h, [bool]$collapsed = $false) {
  return "Begin Object Class=/Script/UMG.Image Name=`"$name`"`r`n" +
    "   Brush=(ResourceObject=`"$texture`",ImageSize=(X=$(F $w),Y=$(F $h)))`r`n" +
    $(if ($collapsed) { "   Visibility=Collapsed`r`n" } else { "" }) +
    "End Object"
}

# An Overlay "Icons" holding $items (@{ name; block }) stacked in order (later on top), each at
# the top-left; UAmmoWidget sets their padding to spread a dual-wield pair.
function Overlay($items) {
  $sb = New-Object System.Text.StringBuilder
  function L([string]$s) { [void]$sb.Append($s + "`r`n") }
  L "Begin Object Class=/Script/UMG.Overlay Name=`"Icons`""
  foreach ($i in $items) { L "   Begin Object Class=/Script/UMG.OverlaySlot Name=`"Slot_$($i.name)`""; L "   End Object" }
  foreach ($i in $items) {
    L "   Begin Object Name=`"Slot_$($i.name)`""
    L "      HorizontalAlignment=HAlign_Left"
    L "      VerticalAlignment=VAlign_Top"
    L "      Parent=`"/Script/UMG.Overlay'Icons'`""
    L "      Content=`"/Script/UMG.Image'$($i.name)'`""
    L "   End Object"
  }
  for ($k = 0; $k -lt $items.Count; $k++) { L "   Slots($k)=`"/Script/UMG.OverlaySlot'Slot_$($items[$k].name)'`"" }
  L "End Object"
  foreach ($i in $items) { L $i.block }
  return $sb.ToString()
}

# A Horizontal Box "Row" holding $items (@{ name; cls; block; left }) left to right, each
# vertically centred with $left px before it, in the editor's own copy format.
function Row($items) {
  $sb = New-Object System.Text.StringBuilder
  function L([string]$s) { [void]$sb.Append($s + "`r`n") }
  L "Begin Object Class=/Script/UMG.HorizontalBox Name=`"Row`""
  foreach ($i in $items) { L "   Begin Object Class=/Script/UMG.HorizontalBoxSlot Name=`"Slot_$($i.name)`""; L "   End Object" }
  foreach ($i in $items) {
    L "   Begin Object Name=`"Slot_$($i.name)`""
    L "      Padding=(Left=$(F $i.left),Top=0.000000,Right=0.000000,Bottom=0.000000)"
    L "      VerticalAlignment=VAlign_Center"
    L "      Parent=`"/Script/UMG.HorizontalBox'Row'`""
    L "      Content=`"/Script/UMG.$($i.cls)'$($i.name)'`""
    L "   End Object"
  }
  for ($k = 0; $k -lt $items.Count; $k++) { L "   Slots($k)=`"/Script/UMG.HorizontalBoxSlot'Slot_$($items[$k].name)'`"" }
  L "End Object"
  foreach ($i in $items) { L $i.block }
  return $sb.ToString()
}

# A Canvas Panel $root holding $items (@{ name; cls (full class path); block; x; y; w; h }), each in
# a fixed-size slot anchored top-left, in the editor's own copy format.
function Canvas([string]$root, $items) {
  $sb = New-Object System.Text.StringBuilder
  function L([string]$s) { [void]$sb.Append($s + "`r`n") }
  L "Begin Object Class=/Script/UMG.CanvasPanel Name=`"$root`""
  foreach ($i in $items) { L "   Begin Object Class=/Script/UMG.CanvasPanelSlot Name=`"Slot_$($i.name)`""; L "   End Object" }
  foreach ($i in $items) {
    L "   Begin Object Name=`"Slot_$($i.name)`""
    L "      LayoutData=(Offsets=(Left=$(F $i.x),Top=$(F $i.y),Right=$(F $i.w),Bottom=$(F $i.h)),Anchors=(Minimum=(X=0.000000,Y=0.000000),Maximum=(X=0.000000,Y=0.000000)),Alignment=(X=0.000000,Y=0.000000))"
    L "      bAutoSize=False"
    L "      Parent=`"/Script/UMG.CanvasPanel'$root'`""
    L "      Content=`"$($i.cls)'$($i.name)'`""
    L "   End Object"
  }
  for ($k = 0; $k -lt $items.Count; $k++) { L "   Slots($k)=`"/Script/UMG.CanvasPanelSlot'Slot_$($items[$k].name)'`"" }
  L "End Object"
  foreach ($i in $items) { L $i.block }
  return $sb.ToString()
}

function UserWidget([string]$name, [string]$cls) {
  return "Begin Object Class=$cls Name=`"$name`"`r`nEnd Object"
}

# A plain white Image (no texture), for the dividers.
function Divider([string]$name, $w, $h) {
  return "Begin Object Class=/Script/UMG.Image Name=`"$name`"`r`n" +
    "   Brush=(ImageSize=(X=$(F $w),Y=$(F $h)))`r`n" +
    "End Object"
}

# The root: a Scale Box "Fit" ($stretch) holding $content (@{ name; cls; block }) at $halign.
function Fit([string]$stretch, [string]$halign, $content) {
  return "Begin Object Class=/Script/UMG.ScaleBox Name=`"Fit`"`r`n" +
    "   Begin Object Class=/Script/UMG.ScaleBoxSlot Name=`"Slot_$($content.name)`"`r`n" +
    "   End Object`r`n" +
    "   Begin Object Name=`"Slot_$($content.name)`"`r`n" +
    "      HorizontalAlignment=$halign`r`n" +
    "      VerticalAlignment=VAlign_Center`r`n" +
    "      Parent=`"/Script/UMG.ScaleBox'Fit'`"`r`n" +
    "      Content=`"/Script/UMG.$($content.cls)'$($content.name)'`"`r`n" +
    "   End Object`r`n" +
    "   Stretch=$stretch`r`n" +
    "   Slots(0)=`"/Script/UMG.ScaleBoxSlot'Slot_$($content.name)'`"`r`n" +
    "End Object`r`n" +
    $content.block
}

# Natural heights (scale 1): the icon 62; Antonio's line is 1.442 em and Slate draws 96 DPI, so a
# size-39 line is 75 tall and a size-43 line 83.
$trees = [ordered]@{
  # The dual-wield copy first, so it draws behind; collapsed until UAmmoWidget shows a pair.
  WeaponIcon = Fit "None" "HAlign_Right" @{ name = "Icons"; cls = "Overlay"; block = (Overlay @(
    @{ name = "WeaponIconDual"; block = (Image "WeaponIconDual" $weaponIcon 90 62 $true) },
    @{ name = "WeaponIcon"; block = (Image "WeaponIcon" $weaponIcon 90 62) })) }
  # "15" Antonio Bold 39 white; "/ 90" Bold 36 grey.
  Ammo = Fit "ScaleToFitY" "HAlign_Left" @{ name = "Row"; cls = "HorizontalBox"; block = (Row @(
    @{ name = "MagazineText"; cls = "TextBlock"; left = 0; block = (Text "MagazineText" "15" 39) },
    @{ name = "ReserveText"; cls = "TextBlock"; left = 12; block = (Text "ReserveText" "/ 90" 36 0.38) })) }
  # Icons at 0.40 of their texture (which includes 4 px of padding); counts Bold 43.
  FirstAid = Fit "ScaleToFitY" "HAlign_Left" @{ name = "Row"; cls = "HorizontalBox"; block = (Row @(
    @{ name = "Icon"; cls = "Image"; left = 0; block = (Image "Icon" $firstAidIcon 70 66) },
    @{ name = "Count"; cls = "TextBlock"; left = 20; block = (Text "Count" "3" 43) })) }
  Grenades = Fit "ScaleToFitY" "HAlign_Left" @{ name = "Row"; cls = "HorizontalBox"; block = (Row @(
    @{ name = "Icon"; cls = "Image"; left = 0; block = (Image "Icon" $grenadeIcon 59 78) },
    @{ name = "Count"; cls = "TextBlock"; left = 18; block = (Text "Count" "2" 43) })) }
  # The user's layout from WBP_PlayerHUD's BottomLeft canvas, less (1176, 852): 618 x 87 in all.
  # Long guns still run left of the weapon icon's box (its Scale Box doesn't scale).
  ItemStrip = Fit "ScaleToFit" "HAlign_Left" @{ name = "Strip"; cls = "CanvasPanel"; block = (Canvas "Strip" @(
    @{ name = "WeaponIcon"; cls = "/Game/UI/WBP_WeaponIcon.WBP_WeaponIcon_C"; block = (UserWidget "WeaponIcon" "/Game/UI/WBP_WeaponIcon.WBP_WeaponIcon_C"); x = 0; y = 12; w = 110; h = 62 },
    @{ name = "Ammo"; cls = "/Game/UI/WBP_Ammo.WBP_Ammo_C"; block = (UserWidget "Ammo" "/Game/UI/WBP_Ammo.WBP_Ammo_C"); x = 128; y = 8; w = 170; h = 75 },
    @{ name = "Divider_0"; cls = "/Script/UMG.Image"; block = (Divider "Divider_0" 3 87); x = 300; y = 0; w = 3; h = 87 },
    @{ name = "FirstAid"; cls = "/Game/UI/WBP_FirstAid.WBP_FirstAid_C"; block = (UserWidget "FirstAid" "/Game/UI/WBP_FirstAid.WBP_FirstAid_C"); x = 332; y = 4; w = 125; h = 83 },
    @{ name = "Divider_1"; cls = "/Script/UMG.Image"; block = (Divider "Divider_1" 3 87); x = 480; y = 0; w = 3; h = 87 },
    @{ name = "Grenades"; cls = "/Game/UI/WBP_Grenades.WBP_Grenades_C"; block = (UserWidget "Grenades" "/Game/UI/WBP_Grenades.WBP_Grenades_C"); x = 508; y = 4; w = 110; h = 83 })) }
}

foreach ($key in $trees.Keys) {
  $out = Join-Path $PSScriptRoot "WBP_$($key)_Tree.txt"
  [IO.File]::WriteAllText($out, $trees[$key], (New-Object System.Text.UTF8Encoding $false))
  "Wrote $out"
}
if ($Clipboard) {
  Set-Clipboard -Value $trees[$Clipboard]
  "Copied WBP_$($Clipboard)_Tree to the clipboard"
}
