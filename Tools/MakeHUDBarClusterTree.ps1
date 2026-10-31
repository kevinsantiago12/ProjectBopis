# Writes the UMG clipboard text for the bottom-left HUD bar cluster to WBP_PlayerHUD_BarCluster.txt
# (next to this script); -Clipboard also copies it. In WBP_PlayerHUD: delete the old WBP_Health and
# WBP_Focus, select the root Canvas Panel in the Hierarchy, Ctrl+V, then anchor BarCluster bottom left.
#
# BarCluster is a Canvas Panel holding the accent (on top) and the health and Focus widgets at the
# layout measured off GPT's composite (spec *HUD: cinematic minimal*), in 1080p px from the accent's
# top-left. WBP_Health / WBP_Focus are just their "Bar" Image, so each fills the size given here and
# UHUDBarWidget feeds that size to M_HUDBar: change a width and the bar tiles, it doesn't stretch.
param([switch]$Clipboard)

$inv = [Globalization.CultureInfo]::InvariantCulture
function F([double]$v) { return $v.ToString("F6", $inv) }

$accentTexture = "/Script/Engine.Texture2D'/Game/UI/HUD/T_HUD_Accent.T_HUD_Accent'"
# Through M_HUDImage, for its Brightness and Opacity.
$backgroundTexture = "/Script/Engine.MaterialInstanceConstant'/Game/UI/HUD/MI_HUD_Background.MI_HUD_Background'"

$widgets = New-Object System.Collections.Generic.List[string]
$slots = New-Object System.Collections.Generic.List[hashtable]

function AddWidget([string]$block, [string]$name, [string]$classRef, $x, $y, $w, $h, [int]$z) {
  $widgets.Add($block)
  $slots.Add(@{ n = "Slot_$name"; c = "$classRef'$name'"; x = $x; y = $y; w = $w; h = $h; z = $z })
}

# GPT's ink background under everything: 130 tall at its own aspect (4.33), centred on the bars'
# height and running on to the right, where the weapon/ammo/items part of the strip will sit.
$block = "Begin Object Class=/Script/UMG.Image Name=`"Background`"`r`n" +
  "   Brush=(ResourceObject=`"$backgroundTexture`",ImageSize=(X=563.000000,Y=130.000000))`r`n" +
  "End Object"
AddWidget $block "Background" "/Script/UMG.Image" -30 -22 563 130 -1

# The bars next (under the accent), focus lowest.
foreach ($bar in @(
    @{ name = "FocusBar"; cls = "/Game/UI/WBP_Focus.WBP_Focus_C"; x = 45; y = 55; w = 328; h = 30; z = 0 },
    @{ name = "HealthBar"; cls = "/Game/UI/WBP_Health.WBP_Health_C"; x = 37; y = 16; w = 376; h = 29; z = 1 })) {
  $block = "Begin Object Class=$($bar.cls) Name=`"$($bar.name)`"`r`n" +
    "End Object"
  AddWidget $block $bar.name $bar.cls $bar.x $bar.y $bar.w $bar.h $bar.z
}

$block = "Begin Object Class=/Script/UMG.Image Name=`"Accent`"`r`n" +
  "   Brush=(ResourceObject=`"$accentTexture`",ImageSize=(X=76.000000,Y=86.000000))`r`n" +
  "End Object"
AddWidget $block "Accent" "/Script/UMG.Image" 0 0 76 86 2

# The cluster canvas, in the editor's own copy format: slots declared, then filled in.
$sb = New-Object System.Text.StringBuilder
function L([string]$s) { [void]$sb.Append($s + "`r`n") }
L "Begin Object Class=/Script/UMG.CanvasPanel Name=`"BarCluster`""
foreach ($s in $slots) { L "   Begin Object Class=/Script/UMG.CanvasPanelSlot Name=`"$($s.n)`""; L "   End Object" }
foreach ($s in $slots) {
  L "   Begin Object Name=`"$($s.n)`""
  L "      LayoutData=(Offsets=(Left=$(F $s.x),Top=$(F $s.y),Right=$(F $s.w),Bottom=$(F $s.h)),Anchors=(Minimum=(X=0.000000,Y=0.000000),Maximum=(X=0.000000,Y=0.000000)),Alignment=(X=0.000000,Y=0.000000))"
  L "      bAutoSize=False"
  L "      ZOrder=$($s.z)"
  L "      Parent=`"/Script/UMG.CanvasPanel'BarCluster'`""
  L "      Content=`"$($s.c)`""
  L "   End Object"
}
for ($k = 0; $k -lt $slots.Count; $k++) { L "   Slots($k)=`"/Script/UMG.CanvasPanelSlot'$($slots[$k].n)'`"" }
L "End Object"
foreach ($w in $widgets) { L $w }

$text = $sb.ToString()
$out = Join-Path $PSScriptRoot "WBP_PlayerHUD_BarCluster.txt"
[IO.File]::WriteAllText($out, $text, (New-Object System.Text.UTF8Encoding $false))
if ($Clipboard) { Set-Clipboard -Value $text }
"Wrote $out ($($slots.Count) widgets + BarCluster)$(if ($Clipboard) { '; copied to the clipboard' })"
