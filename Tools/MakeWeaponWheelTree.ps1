# Writes the UMG clipboard text for WBP_WeaponWheel's widget tree to WBP_WeaponWheel_Tree.txt
# (next to this script); -Clipboard also copies it. In the Widget Blueprint: delete the old root
# (if any), click the empty Hierarchy, Ctrl+V, compile, save.
#
# The widget names are the contract with UWeaponWheelWidget (Segment_N, Icon_N, IconDual_N,
# Count_N, NameText, AmmoText); positions, sizes, fonts and colours are only a starting layout.
# Everything is anchored at the centre. Radius must match the class's Radius (Class Defaults).
param([switch]$Clipboard)

$inv = [Globalization.CultureInfo]::InvariantCulture
function F([double]$v) { return $v.ToString("F6", $inv) }

$segmentTexture = "/Script/Engine.Texture2D'/Game/UI/T_WheelSegment.T_WheelSegment'"
# Designer preview only; the class sets each icon at runtime.
$previewIcon = "/Script/Engine.Texture2D'/Game/Handcrafted_Weapon_Icons/White_Icon_Set/Modern/Pistols/modern_pistol__1_.modern_pistol__1_'"
$font = "/Script/Engine.Font'/Engine/EngineFonts/Roboto.Roboto'"

$Segments = 6
$Radius = 230.0        # middle of the ring: icons sit here
$KeyRadius = 149.0     # slot numbers, just inside the ring
$CountRadius = 314.0   # "2/3", just outside
$SegmentSize = 592.0   # T_WheelSegment drawn at this size gives a 165-295 px ring

$dir = @{}
for ($i = 0; $i -lt $Segments; $i++) {
  $a = (-90 - 360 / $Segments * $i) * [math]::PI / 180   # counter-clockwise from the top
  $dir[$i] = @([math]::Cos($a), [math]::Sin($a))
}

$widgets = New-Object System.Collections.Generic.List[string]
$slots = New-Object System.Collections.Generic.List[hashtable]

function AddWidget([string]$block, [string]$name, [string]$class, $x, $y, $w, $h, [bool]$auto, [int]$z) {
  $widgets.Add($block)
  $slots.Add(@{ n = "Slot_$name"; c = "/Script/UMG.$class'$name'"; x = $x; y = $y; w = $w; h = $h; auto = $auto; z = $z })
}

function AddText([string]$name, [string]$text, [string]$face, $size, $x, $y) {
  $block = "Begin Object Class=/Script/UMG.TextBlock Name=`"$name`"`r`n" +
    "   Text=INVTEXT(`"$text`")`r`n" +
    "   Font=(FontObject=`"$font`",TypefaceFontName=`"$face`",Size=$(F $size))`r`n" +
    "   Justification=Center`r`n" +
    "   bIsVariable=True`r`n" +
    "End Object"
  AddWidget $block $name "TextBlock" $x $y 0 0 $true 3
}

function AddIcon([string]$name, $x, $y, [int]$z, [bool]$hidden) {
  $block = "Begin Object Class=/Script/UMG.Image Name=`"$name`"`r`n" +
    "   Brush=(ResourceObject=`"$previewIcon`",ImageSize=(X=110.000000,Y=45.000000))`r`n" +
    $(if ($hidden) { "   Visibility=Hidden`r`n" } else { "" }) +
    "   bIsVariable=True`r`n" +
    "End Object"
  AddWidget $block $name "Image" $x $y 0 0 $true $z
}

for ($i = 0; $i -lt $Segments; $i++) {
  $block = "Begin Object Class=/Script/UMG.Image Name=`"Segment_$i`"`r`n" +
    "   Brush=(ResourceObject=`"$segmentTexture`",ImageSize=(X=$(F $SegmentSize),Y=$(F $SegmentSize)))`r`n" +
    "   ColorAndOpacity=(R=0.070000,G=0.070000,B=0.070000,A=0.800000)`r`n" +
    "   RenderTransform=(Translation=(X=0.000000,Y=0.000000),Scale=(X=1.000000,Y=1.000000),Shear=(X=0.000000,Y=0.000000),Angle=$(F (-360 / $Segments * $i)))`r`n" +
    "   bIsVariable=True`r`n" +
    "End Object"
  AddWidget $block "Segment_$i" "Image" 0 0 $SegmentSize $SegmentSize $false 0
}
for ($i = 0; $i -lt $Segments; $i++) {
  # A dual weapon's second copy sits on the same spot, behind, like a shadow; the class offsets the two by DualIconOffset.
  AddIcon "Icon_$i" ($dir[$i][0] * $Radius) ($dir[$i][1] * $Radius) 2 $false
  AddIcon "IconDual_$i" ($dir[$i][0] * $Radius) ($dir[$i][1] * $Radius) 1 $true
}
for ($i = 0; $i -lt $Segments; $i++) { AddText "Key_$i" "$($i + 1)" "Bold" 14 ($dir[$i][0] * $KeyRadius) ($dir[$i][1] * $KeyRadius) }
for ($i = 0; $i -lt $Segments; $i++) { AddText "Count_$i" "1/2" "Bold" 14 ($dir[$i][0] * $CountRadius) ($dir[$i][1] * $CountRadius) }
AddText "NameText" "Weapon" "Bold" 22 0 -12
AddText "AmmoText" "12 / 36" "Regular" 16 0 14

# The root canvas, in the editor's own copy format: slots declared, then filled in.
$sb = New-Object System.Text.StringBuilder
function L([string]$s) { [void]$sb.Append($s + "`r`n") }
L "Begin Object Class=/Script/UMG.CanvasPanel Name=`"WheelCanvas`""
foreach ($s in $slots) { L "   Begin Object Class=/Script/UMG.CanvasPanelSlot Name=`"$($s.n)`""; L "   End Object" }
foreach ($s in $slots) {
  L "   Begin Object Name=`"$($s.n)`""
  L "      LayoutData=(Offsets=(Left=$(F $s.x),Top=$(F $s.y),Right=$(F $s.w),Bottom=$(F $s.h)),Anchors=(Minimum=(X=0.500000,Y=0.500000),Maximum=(X=0.500000,Y=0.500000)),Alignment=(X=0.500000,Y=0.500000))"
  L "      bAutoSize=$(if ($s.auto) { 'True' } else { 'False' })"
  L "      ZOrder=$($s.z)"
  L "      Parent=`"/Script/UMG.CanvasPanel'WheelCanvas'`""
  L "      Content=`"$($s.c)`""
  L "   End Object"
}
for ($k = 0; $k -lt $slots.Count; $k++) { L "   Slots($k)=`"/Script/UMG.CanvasPanelSlot'$($slots[$k].n)'`"" }
L "End Object"
foreach ($w in $widgets) { L $w }

$text = $sb.ToString()
$out = Join-Path $PSScriptRoot "WBP_WeaponWheel_Tree.txt"
[IO.File]::WriteAllText($out, $text, (New-Object System.Text.UTF8Encoding $false))
if ($Clipboard) { Set-Clipboard -Value $text }
"Wrote $out ($($slots.Count) widgets + WheelCanvas)$(if ($Clipboard) { '; copied to the clipboard' })"
