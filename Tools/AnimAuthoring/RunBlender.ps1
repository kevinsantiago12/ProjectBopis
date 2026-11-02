<#
.SYNOPSIS
    Runs one of the animation projects' Blender scripts (bl_inspect.py, bl_author.py, bl_export.py) in
    background Blender 4.0, with factory settings.

.DESCRIPTION
    Anything after the script path is passed to the script (after Blender's "--"), e.g. "render" for
    bl_author.py's contact sheets. The scripts print their own progress lines; Blender's are left in.

.EXAMPLE
    .\Tools\AnimAuthoring\RunBlender.ps1 .\Tools\AnimAuthoring\MP5Reload\bl_author.py render
#>
param(
    [Parameter(Mandatory = $true)][string]$Script,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ScriptArgs
)

$ErrorActionPreference = 'Stop'

$Blender = 'C:\Program Files\Blender Foundation\Blender 4.0\blender.exe'
$CmdArgs = @('--background', '--factory-startup', '--python', (Resolve-Path $Script).Path)
if ($ScriptArgs) { $CmdArgs += '--'; $CmdArgs += $ScriptArgs }
& $Blender @CmdArgs
