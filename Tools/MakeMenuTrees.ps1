# Writes the UMG clipboard text for the menu widgets (spec *Main menu*), one file each next to this
# script: WBP_MenuButton_Tree.txt and WBP_MainMenu_Tree.txt; -Clipboard <name> also copies that one.
# The bridge can't build widget trees, so these are pasted: in the Widget Blueprint, click the empty
# Hierarchy, Ctrl+V, compile, save. Do WBP_MenuButton first: WBP_MainMenu is made of its copies.
#
# The widget names are the contract with the C++: UMenuButtonWidget needs a Button named "Button"
# and takes an optional Text Block "Label"; UMenuWidget takes an optional Widget Switcher "Pages"
# whose first child is the first page. Everything else (the look, layout, sizes) is a starting
# point for the user to restyle in the designer.
#
# The main menu's layout is the user's (2026-11-07): Main: Story, Arena, Options, Quit Game.
# Story: New Game, Load Game, Back. Arena: Back Alley, Back. Each button's Text and Action are
# set on its copy, so they show in the Details panel; Options and Load Game have no Action yet
# and New Game no level yet, so they're greyed out.
#
# WBP_PauseMenu (2026-11-07): a blurred, lightly dimmed backdrop over the paused game, then the same bottom-left Pages
# with one page: Resume (Back: back from the first page resumes), Restart (RestartLevel), Options,
# Main Menu (OpenLevel Lvl_MainMenu), Quit Game.
#
# Options (2026-11-09, spec *Player settings*): WBP_SettingSlider is one setting on a slider
# (USettingSliderWidget needs a Slider "Slider"; Label, ValueText, a Border "Background" and FocusFrame
# are optional). WBP_OptionsPage is the one Options page both menus share (user: "shared options page"):
# Mouse Sensitivity, Controller Sensitivity, Back. Each menu holds a copy of it as the last child of
# Pages, named "OptionsPage", which its Options button opens. Paste WBP_SettingSlider before
# WBP_OptionsPage, which is made of its copies. In menus already pasted and restyled, add the page and
# set the Options button by hand rather than re-pasting the menu.
param([ValidateSet("MenuButton", "MainMenu", "PauseMenu", "SettingSlider", "OptionsPage")][string]$Clipboard)

$inv = [Globalization.CultureInfo]::InvariantCulture
function F([double]$v) { return $v.ToString("F6", $inv) }

$bold = "/Script/Engine.Font'/Game/antonio/Antonio-Bold_Font.Antonio-Bold_Font'"
$buttonClass = "/Game/UI/Menu/WBP_MenuButton.WBP_MenuButton_C"
$sliderClass = "/Game/UI/Menu/WBP_SettingSlider.WBP_SettingSlider_C"
$optionsClass = "/Game/UI/Menu/WBP_OptionsPage.WBP_OptionsPage_C"
$backAlley = "/Game/ThirdPerson/Lvl_BackAlleys_Arena.Lvl_BackAlleys_Arena"

function Pad($l, $t, $r, $b) { return "Padding=(Left=$(F $l),Top=$(F $t),Right=$(F $r),Bottom=$(F $b))" }

# A panel $name (UMG class $cls, slots of class $slotCls) holding $items (@{ name; cls (full class
# path); block; slot (slot property lines) }), in the editor's own copy format: the slots declared,
# then filled in, then each child's own block.
function Panel([string]$cls, [string]$name, [string]$slotCls, $items, $props = @()) {
  $sb = New-Object System.Text.StringBuilder
  function L([string]$s) { [void]$sb.Append($s + "`r`n") }
  L "Begin Object Class=/Script/UMG.$cls Name=`"$name`""
  foreach ($i in $items) { L "   Begin Object Class=/Script/UMG.$slotCls Name=`"$($slotCls)_$($i.name)`""; L "   End Object" }
  foreach ($i in $items) {
    L "   Begin Object Name=`"$($slotCls)_$($i.name)`""
    foreach ($p in $i.slot) { L "      $p" }
    L "      Parent=`"/Script/UMG.$cls'$name'`""
    L "      Content=`"$($i.cls)'$($i.name)'`""
    L "   End Object"
  }
  foreach ($p in $props) { L "   $p" }
  for ($k = 0; $k -lt $items.Count; $k++) { L "   Slots($k)=`"/Script/UMG.$slotCls'$($slotCls)_$($items[$k].name)'`"" }
  L "End Object"
  foreach ($i in $items) { [void]$sb.Append($i.block) }
  return $sb.ToString()
}

# --- WBP_MenuButton: an Overlay of the Button "Button" (holding the Text Block "Label") and the
# selection frame "FocusFrame" on top ------------------------------------------------------------------
# Dark, half-see-through boxes over the scene; Antonio Bold like the HUD. The label shows the copy's
# Text (UMenuButtonWidget::NativePreConstruct), so it's blank here and filled in each menu. The colours
# come from the C++ (NormalColor / HighlightColor ...), set on WBP_MenuButton's defaults.
# FocusFrame replaces Slate's blue focus ring (RenderFocusRule=Never, 2026-11-07): a blue 3 px rounded
# outline with a see-through fill, never hit-testable, shown by the C++ on the selected button while a
# controller drives the menu. It's left visible here so it can be styled in the designer.
$button = Panel "Button" "Button" "ButtonSlot" @(
  @{ name = "Label"; cls = "/Script/UMG.TextBlock"
     slot = @((Pad 28 6 28 6), "HorizontalAlignment=HAlign_Left", "VerticalAlignment=VAlign_Center")
     block = "Begin Object Class=/Script/UMG.TextBlock Name=`"Label`"`r`n" +
             "   Font=(FontObject=`"$bold`",TypefaceFontName=`"Default`",Size=$(F 30))`r`n" +
             "End Object`r`n" }
) @("BackgroundColor=(R=0.020000,G=0.020000,B=0.020000,A=0.650000)")

$focusFrame = "Begin Object Class=/Script/UMG.Image Name=`"FocusFrame`"`r`n" +
  "   Brush=(TintColor=(SpecifiedColor=(R=1.000000,G=1.000000,B=1.000000,A=0.000000)),DrawAs=RoundedBox," +
  "OutlineSettings=(CornerRadii=(X=4.000000,Y=4.000000,Z=4.000000,W=4.000000)," +
  "Color=(SpecifiedColor=(R=0.050000,G=0.400000,B=1.000000,A=1.000000)),Width=3.000000,RoundingType=FixedRadius,bUseBrushTransparency=False))`r`n" +
  "   Visibility=HitTestInvisible`r`n" +
  "End Object`r`n"

$fill = @("HorizontalAlignment=HAlign_Fill", "VerticalAlignment=VAlign_Fill")
$menuButton = Panel "Overlay" "Root" "OverlaySlot" @(
  @{ name = "Button"; cls = "/Script/UMG.Button"; slot = $fill; block = $button },
  @{ name = "FocusFrame"; cls = "/Script/UMG.Image"; slot = $fill; block = $focusFrame })

# --- WBP_MainMenu ------------------------------------------------------------------------------------
# One copy of WBP_MenuButton: its Text, its Action (none = greyed out), and the Action's target.
function MenuButton([string]$name, [string]$text, [string]$action = "", [string]$page = "", [string]$level = "") {
  $s = "Begin Object Class=$buttonClass Name=`"$name`"`r`n   Text=INVTEXT(`"$text`")`r`n"
  if ($action) { $s += "   Action=$action`r`n" }
  if ($page) { $s += "   Page=`"$page`"`r`n" }
  if ($level) { $s += "   Level=`"$level`"`r`n" }
  return $s + "End Object`r`n"
}

# A page: a Vertical Box of buttons, all as wide as the widest, 10 px apart.
function Page([string]$name, $buttons) {
  $items = @($buttons | ForEach-Object {
    @{ name = $_.name; cls = $buttonClass; block = $_.block
       slot = @((Pad 0 0 0 10), "HorizontalAlignment=HAlign_Fill") } })
  return Panel "VerticalBox" $name "VerticalBoxSlot" $items
}
function B([string]$name, [string]$text, [string]$action = "", [string]$page = "", [string]$level = "") {
  return @{ name = $name; block = (MenuButton $name $text $action $page $level) }
}

# Pages in a Widget Switcher; MainPage first (UMenuWidget shows the first child at start). Each page
# keeps to the bottom, so the shorter ones line up with the main page's bottom edge.
$pageSlot = @("HorizontalAlignment=HAlign_Fill", "VerticalAlignment=VAlign_Bottom")

# The shared Options page, as each menu's last page (its contents are WBP_OptionsPage's own).
$optionsPageItem = @{ name = "OptionsPage"; cls = $optionsClass; slot = $pageSlot
  block = "Begin Object Class=$optionsClass Name=`"OptionsPage`"`r`nEnd Object`r`n" }
$pages = Panel "WidgetSwitcher" "Pages" "WidgetSwitcherSlot" @(
  @{ name = "MainPage"; cls = "/Script/UMG.VerticalBox"; slot = $pageSlot; block = (Page "MainPage" @(
    (B "StoryButton" "Story" "OpenPage" "StoryPage"),
    (B "ArenaButton" "Arena" "OpenPage" "ArenaPage"),
    (B "OptionsButton" "Options" "OpenPage" "OptionsPage"),
    (B "QuitButton" "Quit Game" "QuitGame"))) },
  @{ name = "StoryPage"; cls = "/Script/UMG.VerticalBox"; slot = $pageSlot; block = (Page "StoryPage" @(
    (B "NewGameButton" "New Game" "OpenLevel"),
    (B "LoadGameButton" "Load Game"),
    (B "StoryBackButton" "Back" "Back"))) },
  @{ name = "ArenaPage"; cls = "/Script/UMG.VerticalBox"; slot = $pageSlot; block = (Page "ArenaPage" @(
    (B "BackAlleyButton" "Back Alley" "OpenLevel" "" $backAlley),
    (B "ArenaBackButton" "Back" "Back"))) },
  $optionsPageItem)

# The root fills the screen; the menu sits bottom-left, clear of the scene's middle (1080p px).
$mainMenu = Panel "Overlay" "Root" "OverlaySlot" @(
  @{ name = "Pages"; cls = "/Script/UMG.WidgetSwitcher"; block = $pages
     slot = @((Pad 140 0 0 160), "HorizontalAlignment=HAlign_Left", "VerticalAlignment=VAlign_Bottom") })

# --- WBP_PauseMenu -----------------------------------------------------------------------------------
$mainMenuLevel = "/Game/ThirdPerson/Lvl_MainMenu.Lvl_MainMenu"
$pausePages = Panel "WidgetSwitcher" "Pages" "WidgetSwitcherSlot" @(
  @{ name = "MainPage"; cls = "/Script/UMG.VerticalBox"; slot = $pageSlot; block = (Page "MainPage" @(
    (B "ResumeButton" "Resume" "Back"),
    (B "RestartButton" "Restart" "RestartLevel"),
    (B "OptionsButton" "Options" "OpenPage" "OptionsPage"),
    (B "MainMenuButton" "Main Menu" "OpenLevel" "" $mainMenuLevel),
    (B "QuitButton" "Quit Game" "QuitGame"))) },
  $optionsPageItem)

# The game blurs behind the menu (user, 2026-11-07: "Use a blur, not just a dim"), with a light dim on
# top so the buttons read. BlurStrength is the look's main knob; the blur only runs while paused.
$blur = "Begin Object Class=/Script/UMG.BackgroundBlur Name=`"Blur`"`r`n" +
  "   BlurStrength=$(F 10)`r`n" +
  "End Object`r`n"
$dim = "Begin Object Class=/Script/UMG.Image Name=`"Dim`"`r`n" +
  "   ColorAndOpacity=(R=0.000000,G=0.000000,B=0.000000,A=0.250000)`r`n" +
  "End Object`r`n"

$fullScreen = @("HorizontalAlignment=HAlign_Fill", "VerticalAlignment=VAlign_Fill")
$pauseMenu = Panel "Overlay" "Root" "OverlaySlot" @(
  @{ name = "Blur"; cls = "/Script/UMG.BackgroundBlur"; block = $blur; slot = $fullScreen },
  @{ name = "Dim"; cls = "/Script/UMG.Image"; block = $dim; slot = $fullScreen },
  @{ name = "Pages"; cls = "/Script/UMG.WidgetSwitcher"; block = $pausePages
     slot = @((Pad 140 0 0 160), "HorizontalAlignment=HAlign_Left", "VerticalAlignment=VAlign_Bottom") })

# --- WBP_SettingSlider: an Overlay of the Border "Background" (the label, the slider and the number in
# a row) and the same selection frame as the buttons --------------------------------------------------
# The Border's colour comes from the C++ (NormalColor / HighlightColor, as the button's background), so
# the row reads like a button. The slider's handle is amber so it shows on both the dark resting
# background and the light highlight. Range, step and value are set by the C++ from the settings; the
# ones here only show in the designer. Left/right without grabbing it first (RequiresControllerLock off).
$text30 = "Font=(FontObject=`"$bold`",TypefaceFontName=`"Default`",Size=$(F 30))"
$slider = "Begin Object Class=/Script/UMG.Slider Name=`"Slider`"`r`n" +
  "   Value=$(F 1)`r`n   MinValue=$(F 0.2)`r`n   MaxValue=$(F 3)`r`n   StepSize=$(F 0.05)`r`n" +
  "   MouseUsesStep=True`r`n   RequiresControllerLock=False`r`n" +
  "   SliderBarColor=(R=0.400000,G=0.400000,B=0.400000,A=1.000000)`r`n" +
  "   SliderHandleColor=(R=0.950000,G=0.600000,B=0.150000,A=1.000000)`r`n" +
  "End Object`r`n"
function SizeBox([string]$name, [double]$width, $child) {
  return Panel "SizeBox" $name "SizeBoxSlot" @($child) @("WidthOverride=$(F $width)", "bOverride_WidthOverride=True")
}
$row = Panel "HorizontalBox" "Row" "HorizontalBoxSlot" @(
  @{ name = "Label"; cls = "/Script/UMG.TextBlock"
     slot = @("Size=(SizeRule=Fill)", (Pad 0 0 32 0), "VerticalAlignment=VAlign_Center")
     block = "Begin Object Class=/Script/UMG.TextBlock Name=`"Label`"`r`n   $text30`r`nEnd Object`r`n" },
  @{ name = "SliderBox"; cls = "/Script/UMG.SizeBox"; slot = @("VerticalAlignment=VAlign_Center")
     block = (SizeBox "SliderBox" 360 @{ name = "Slider"; cls = "/Script/UMG.Slider"; block = $slider
       slot = @("HorizontalAlignment=HAlign_Fill", "VerticalAlignment=VAlign_Center") }) },
  @{ name = "ValueBox"; cls = "/Script/UMG.SizeBox"; slot = @((Pad 20 0 0 0), "VerticalAlignment=VAlign_Center")
     block = (SizeBox "ValueBox" 90 @{ name = "ValueText"; cls = "/Script/UMG.TextBlock"
       slot = @("HorizontalAlignment=HAlign_Right", "VerticalAlignment=VAlign_Center")
       block = "Begin Object Class=/Script/UMG.TextBlock Name=`"ValueText`"`r`n   Text=INVTEXT(`"1.00`")`r`n   $text30`r`n   Justification=Right`r`nEnd Object`r`n" }) })
$background = Panel "Border" "Background" "BorderSlot" @(
  @{ name = "Row"; cls = "/Script/UMG.HorizontalBox"; block = $row
     slot = @((Pad 28 6 28 6), "HorizontalAlignment=HAlign_Fill", "VerticalAlignment=VAlign_Center") }
) @("BrushColor=(R=0.020000,G=0.020000,B=0.020000,A=0.650000)")
$settingSlider = Panel "Overlay" "Root" "OverlaySlot" @(
  @{ name = "Background"; cls = "/Script/UMG.Border"; slot = $fill; block = $background },
  @{ name = "FocusFrame"; cls = "/Script/UMG.Image"; slot = $fill; block = $focusFrame })

# --- WBP_OptionsPage: the settings, then Back, as wide as the widest, 10 px apart -----------------------
function SettingSlider([string]$name, [string]$text, [string]$setting) {
  return "Begin Object Class=$sliderClass Name=`"$name`"`r`n   Text=INVTEXT(`"$text`")`r`n   Setting=$setting`r`nEnd Object`r`n"
}
$rowSlot = @((Pad 0 0 0 10), "HorizontalAlignment=HAlign_Fill")
$optionsPage = Panel "VerticalBox" "OptionsList" "VerticalBoxSlot" @(
  @{ name = "MouseSensitivity"; cls = $sliderClass; slot = $rowSlot
     block = (SettingSlider "MouseSensitivity" "Mouse Sensitivity" "MouseSensitivity") },
  @{ name = "ControllerSensitivity"; cls = $sliderClass; slot = $rowSlot
     block = (SettingSlider "ControllerSensitivity" "Controller Sensitivity" "ControllerSensitivity") },
  @{ name = "OptionsBackButton"; cls = $buttonClass; slot = $rowSlot
     block = (MenuButton "OptionsBackButton" "Back" "Back") })

$trees = [ordered]@{ MenuButton = $menuButton; MainMenu = $mainMenu; PauseMenu = $pauseMenu
                     SettingSlider = $settingSlider; OptionsPage = $optionsPage }
foreach ($key in $trees.Keys) {
  $out = Join-Path $PSScriptRoot "WBP_$($key)_Tree.txt"
  [IO.File]::WriteAllText($out, $trees[$key], (New-Object System.Text.UTF8Encoding $false))
  "Wrote $out"
}
if ($Clipboard) {
  Set-Clipboard -Value $trees[$Clipboard]
  "Copied WBP_$($Clipboard)_Tree to the clipboard"
}
