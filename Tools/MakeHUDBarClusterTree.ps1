# Writes the UMG clipboard text for the inside of WBP_BarCluster (a plain UserWidget) to
# WBP_BarCluster_Tree.txt (next to this script); -Clipboard also copies it. In the Widget
# Blueprint: delete the old root (if any), click the empty Hierarchy, Ctrl+V, compile, save.
#
# A Scale Box holding a Canvas Panel with GPT's background, the health and Focus bars and the
# accent, so resizing the widget's box in WBP_PlayerHUD scales the whole section uniformly (it
# keeps to the box's bottom-left corner). Its natural size is 563 x 130 (1080p px); the bars'
# layout was measured off GPT's composite (spec *HUD: cinematic minimal*). WBP_Health / WBP_Focus
# are just their "Bar" Image, so each fills the size given here and UHUDBarWidget feeds that size
# to M_HUDBar: change a width and the bar tiles, it doesn't stretch.
param([switch]$Clipboard)

$inv = [Globalization.CultureInfo]::InvariantCulture
function F([double]$v) { return $v.ToString("F6", $inv) }

$accentTexture = "/Script/Engine.Texture2D'/Game/UI/HUD/T_HUD_Accent.T_HUD_Accent'"
# Through M_HUDImage, for its Brightness and Opacity.
$backgroundTexture = "/Script/Engine.MaterialInstanceConstant'/Game/UI/HUD/MI_HUD_Background.MI_HUD_Background'"

function Image([string]$name, [string]$texture, $w, $h) {
  return "Begin Object Class=/Script/UMG.Image Name=`"$name`"`r`n" +
    "   Brush=(ResourceObject=`"$texture`",ImageSize=(X=$(F $w),Y=$(F $h)))`r`n" +
    "End Object"
}

function UserWidget([string]$name, [string]$cls) {
  return "Begin Object Class=$cls Name=`"$name`"`r`nEnd Object"
}

# A Canvas Panel $root holding $items (@{ name; cls; block; x; y; w; h; z }), each in a fixed-size
# slot anchored top-left, in the editor's own copy format: slots declared, then filled in.
function Canvas([string]$root, $items) {
  $sb = New-Object System.Text.StringBuilder
  function L([string]$s) { [void]$sb.Append($s + "`r`n") }
  L "Begin Object Class=/Script/UMG.CanvasPanel Name=`"$root`""
  foreach ($i in $items) { L "   Begin Object Class=/Script/UMG.CanvasPanelSlot Name=`"Slot_$($i.name)`""; L "   End Object" }
  foreach ($i in $items) {
    L "   Begin Object Name=`"Slot_$($i.name)`""
    L "      LayoutData=(Offsets=(Left=$(F $i.x),Top=$(F $i.y),Right=$(F $i.w),Bottom=$(F $i.h)),Anchors=(Minimum=(X=0.000000,Y=0.000000),Maximum=(X=0.000000,Y=0.000000)),Alignment=(X=0.000000,Y=0.000000))"
    L "      bAutoSize=False"
    L "      ZOrder=$($i.z)"
    L "      Parent=`"/Script/UMG.CanvasPanel'$root'`""
    L "      Content=`"$($i.cls)'$($i.name)'`""
    L "   End Object"
  }
  for ($k = 0; $k -lt $items.Count; $k++) { L "   Slots($k)=`"/Script/UMG.CanvasPanelSlot'Slot_$($items[$k].name)'`"" }
  L "End Object"
  foreach ($i in $items) { L $i.block }
  return $sb.ToString()
}

# WBP_BarCluster, from the background's top-left (the accent sits at (30, 22)). The canvas sizes
# itself to its children, 563 x 130, which is what the Scale Box fits to the widget's box.
$cluster = Canvas "Cluster" @(
  # GPT's ink background under everything: 130 tall at its own aspect (4.33).
  @{ name = "Background"; cls = "/Script/UMG.Image"; block = (Image "Background" $backgroundTexture 563 130); x = 0; y = 0; w = 563; h = 130; z = -1 },
  # The bars next (under the accent), focus lowest.
  @{ name = "FocusBar"; cls = "/Game/UI/WBP_Focus.WBP_Focus_C"; block = (UserWidget "FocusBar" "/Game/UI/WBP_Focus.WBP_Focus_C"); x = 75; y = 77; w = 328; h = 30; z = 0 },
  @{ name = "HealthBar"; cls = "/Game/UI/WBP_Health.WBP_Health_C"; block = (UserWidget "HealthBar" "/Game/UI/WBP_Health.WBP_Health_C"); x = 67; y = 38; w = 376; h = 29; z = 1 },
  @{ name = "Accent"; cls = "/Script/UMG.Image"; block = (Image "Accent" $accentTexture 76 86); x = 30; y = 22; w = 76; h = 86; z = 2 })
$clusterText = "Begin Object Class=/Script/UMG.ScaleBox Name=`"Fit`"`r`n" +
  "   Begin Object Class=/Script/UMG.ScaleBoxSlot Name=`"Slot_Cluster`"`r`n" +
  "   End Object`r`n" +
  "   Begin Object Name=`"Slot_Cluster`"`r`n" +
  "      HorizontalAlignment=HAlign_Left`r`n" +
  "      VerticalAlignment=VAlign_Bottom`r`n" +
  "      Parent=`"/Script/UMG.ScaleBox'Fit'`"`r`n" +
  "      Content=`"/Script/UMG.CanvasPanel'Cluster'`"`r`n" +
  "   End Object`r`n" +
  "   Stretch=ScaleToFit`r`n" +
  "   Slots(0)=`"/Script/UMG.ScaleBoxSlot'Slot_Cluster'`"`r`n" +
  "End Object`r`n" +
  $cluster

$out = Join-Path $PSScriptRoot "WBP_BarCluster_Tree.txt"
[IO.File]::WriteAllText($out, $clusterText, (New-Object System.Text.UTF8Encoding $false))
if ($Clipboard) { Set-Clipboard -Value $clusterText }
"Wrote $out$(if ($Clipboard) { '; copied to the clipboard' })"
