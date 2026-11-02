<#
.SYNOPSIS
    Runs one of the animation projects' Unreal scripts (export_ue.py, import_ue.py) in a headless editor.

.DESCRIPTION
    Starts UnrealEditor-Cmd on ProjectBopis with -run=pythonscript, waits, then prints the script's own log
    lines ([TAG] ...) and any Python errors. The full log goes next to the script as <script>_log.txt.

    -Render allows rendering, which exporting a skeletal mesh needs (and an anim with its preview mesh).
    Without it the run is -nullrhi -NoShaderCompile, which starts faster. (-NoShaderCompile together with
    rendering asserts on startup, so it's left out then.)

    The open editor can stay open for exports and for importing NEW assets. Re-importing over assets the
    open editor has loaded isn't safe (it keeps its own copies and can save them back): close it first,
    e.g. with ..\RebuildEditor.ps1 -NoLaunch, and reopen it afterwards.

    "HttpListener unable to bind to 127.0.0.1:8000" in the log is the open editor holding the bridge port;
    it's harmless, and it's why the exit code is often 1.

.EXAMPLE
    .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\AnimAuthoring\MP5Reload\export_ue.py -Render
#>
param(
    [Parameter(Mandatory = $true)][string]$Script,
    [switch]$Render
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$UProject    = Join-Path $ProjectRoot 'ProjectBopis.uproject'
$EditorCmd   = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$ScriptPath  = (Resolve-Path $Script).Path
$Log         = $ScriptPath -replace '\.py$', '_log.txt'

$CmdArgs = @("`"$UProject`"", '-run=pythonscript', "-script=`"$ScriptPath`"", '-unattended', '-nosplash', '-nop4',
             "-abslog=`"$Log`"")
if ($Render) { $CmdArgs += '-AllowCommandletRendering' } else { $CmdArgs += @('-nullrhi', '-NoShaderCompile') }

$p = Start-Process -FilePath $EditorCmd -ArgumentList $CmdArgs -PassThru -Wait -WindowStyle Hidden `
    -RedirectStandardOutput ($Log -replace '\.txt$', '_stdout.txt')

Select-String -Path $Log -Pattern 'LogPython: (Warning|Error): ' |
    Where-Object { $_.Line -notmatch 'LogInit: Display' } |
    ForEach-Object { $_.Line -replace '^\[[^\]]*\]\[[^\]]*\]', '' }
Write-Host "Exit code $($p.ExitCode). Full log: $Log"
