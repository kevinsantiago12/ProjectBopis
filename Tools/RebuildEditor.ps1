<#
.SYNOPSIS
    Closes the ProjectBopis editor, builds the editor target, then reopens the editor.

.DESCRIPTION
    Replaces the manual "close editor -> Build in Visual Studio -> reopen" loop needed
    after any change Live Coding can't handle (new/changed UPROPERTY, UFUNCTION, UENUM,
    class layout, new files).

    1. Asks the running ProjectBopis editor to close (same as clicking X, so it still
       prompts to save unsaved assets) and waits until it has actually exited.
    2. Builds ProjectBopisEditor Win64 Development through Unreal Build Tool - the same
       build Visual Studio runs. -Clean does a full rebuild (Rebuild.bat) instead.
    3. Reopens the editor on the project, only if the build succeeded.

.PARAMETER Clean
    Full rebuild (clean + build) instead of an incremental build. Rarely needed: an
    incremental build already regenerates reflection code for header changes.

.PARAMETER NoLaunch
    Build only; don't reopen the editor.

.PARAMETER Force
    If the editor hasn't closed by the timeout (e.g. a save dialog was left open),
    kill it instead of aborting. Unsaved changes are lost.

.PARAMETER TimeoutSeconds
    How long to wait for the editor to close. Default 300.

.EXAMPLE
    .\Tools\RebuildEditor.ps1
    .\Tools\RebuildEditor.ps1 -Clean
#>
param(
    [switch]$Clean,
    [switch]$NoLaunch,
    [switch]$Force,
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$UProject    = Join-Path $ProjectRoot 'ProjectBopis.uproject'
$EngineRoot  = 'C:\Program Files\Epic Games\UE_5.8'
$EditorExe   = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$BatchDir    = Join-Path $EngineRoot 'Engine\Build\BatchFiles'
$Target      = 'ProjectBopisEditor'

function Write-Step([string]$Message) {
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}

if (-not (Test-Path $UProject))  { throw "Project not found: $UProject" }
if (-not (Test-Path $EditorExe)) { throw "Editor not found: $EditorExe (check `$EngineRoot)" }

# ---- 1. Close the editor ----------------------------------------------------------

# Only editors that have this project open - other projects are left alone.
function Get-ProjectEditors {
    Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe'" |
        Where-Object { $_.CommandLine -like '*ProjectBopis.uproject*' }
}

$editors = @(Get-ProjectEditors)
if ($editors.Count -eq 0) {
    Write-Step 'Editor is not running.'
}
else {
    Write-Step "Closing the editor (PID $($editors.ProcessId -join ', ')) - answer any save prompt in the editor."
    foreach ($e in $editors) {
        $proc = Get-Process -Id $e.ProcessId -ErrorAction SilentlyContinue
        if ($proc) { [void]$proc.CloseMainWindow() }
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-ProjectEditors) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 1
    }

    $still = @(Get-ProjectEditors)
    if ($still.Count -gt 0) {
        if ($Force) {
            Write-Host 'Editor did not close in time - killing it (-Force).' -ForegroundColor Yellow
            $still | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
            Start-Sleep -Seconds 2
        }
        else {
            throw "Editor still open after $TimeoutSeconds s (a save dialog waiting?). Close it and re-run, or use -Force."
        }
    }

    # Live Coding's console can outlive the editor briefly and hold the DLL.
    Get-Process -Name 'LiveCodingConsole' -ErrorAction SilentlyContinue |
        ForEach-Object { $_ | Stop-Process -Force }

    Write-Host 'Editor closed.' -ForegroundColor Green
}

# ---- 2. Build -------------------------------------------------------------------------

$batch = if ($Clean) { 'Rebuild.bat' } else { 'Build.bat' }
Write-Step "Building $Target Win64 Development ($batch)..."

$started = Get-Date
& (Join-Path $BatchDir $batch) $Target Win64 Development "-Project=$UProject" -WaitMutex
$exitCode = $LASTEXITCODE
$elapsed = [int]((Get-Date) - $started).TotalSeconds

if ($exitCode -ne 0) {
    Write-Host ''
    Write-Host "BUILD FAILED (exit code $exitCode, ${elapsed}s). Editor not reopened - fix the errors above." -ForegroundColor Red
    exit $exitCode
}
Write-Host "Build succeeded (${elapsed}s)." -ForegroundColor Green

# ---- 3. Reopen the editor ---------------------------------------------------------------

if ($NoLaunch) {
    Write-Step 'Done (-NoLaunch: editor not reopened).'
    exit 0
}

Write-Step 'Opening the editor...'
Start-Process -FilePath $EditorExe -ArgumentList "`"$UProject`""
Write-Host 'Editor launched. Done.' -ForegroundColor Green
