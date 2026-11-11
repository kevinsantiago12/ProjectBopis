<#
.SYNOPSIS
    Closes the ProjectBopis editor, makes a Deck test build, then reopens the editor.

.DESCRIPTION
    The build procedure from TechnicalDesignSpec.md, "Deck test builds":
    BuildCookRun Win64 Development, cooked, staged, pak + IoStore, compressed, archived to
    ProjectBopis_Builds/DeckTest beside the project.

    The editor must be closed first: with it open, Live Coding blocks the -build step and
    the cooker can't bind the MCP bridge's port 8000, which fails the whole cook.

    1. Asks the editor to close (same as clicking X, so it still prompts to save) and waits.
       Never kills it: if it hasn't closed by the timeout, the script stops.
    2. Runs BuildCookRun. The full log goes to Saved/Logs/Build<ArchiveName>.log
       (BuildDeckTest.log, BuildShowcase.log).
    3. Reopens the editor, whether the build passed or failed.

.PARAMETER NoLaunch
    Don't reopen the editor afterwards.

.PARAMETER TimeoutSeconds
    How long to wait for the editor to close. Default 300.

.PARAMETER Configuration
    Development (default: the Deck test build, with logs, the console and on-screen debug text)
    or Shipping (a build to show people: no console, no on-screen debug messages or map
    warnings, no Print String output).

.PARAMETER ArchiveName
    The folder under ProjectBopis_Builds it goes to. Default DeckTest for Development, Showcase
    for Shipping, so one never overwrites the other.

.EXAMPLE
    .\Tools\BuildDeck.ps1

.EXAMPLE
    .\Tools\BuildDeck.ps1 -Configuration Shipping
#>
param(
    [switch]$NoLaunch,
    [int]$TimeoutSeconds = 300,
    [ValidateSet('Development', 'Shipping')][string]$Configuration = 'Development',
    [string]$ArchiveName
)
if (-not $ArchiveName) { $ArchiveName = if ($Configuration -eq 'Shipping') { 'Showcase' } else { 'DeckTest' } }

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$UProject    = Join-Path $ProjectRoot 'ProjectBopis.uproject'
$EngineRoot  = 'C:\Program Files\Epic Games\UE_5.8'
$EditorExe   = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$RunUAT      = Join-Path $EngineRoot 'Engine\Build\BatchFiles\RunUAT.bat'
$ArchiveDir  = Join-Path (Split-Path -Parent $ProjectRoot) "ProjectBopis_Builds\$ArchiveName"
$LogFile     = Join-Path $ProjectRoot "Saved\Logs\Build$ArchiveName.log"

function Write-Step([string]$Message) {
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}

if (-not (Test-Path $UProject)) { throw "Project not found: $UProject" }
if (-not (Test-Path $RunUAT))   { throw "RunUAT not found: $RunUAT (check `$EngineRoot)" }

# ---- 1. Close the editor ----------------------------------------------------------

function Get-ProjectEditors {
    Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe'" |
        Where-Object { $_.CommandLine -like '*ProjectBopis.uproject*' }
}

$editors = @(Get-ProjectEditors)
$wasOpen = $editors.Count -gt 0
if (-not $wasOpen) {
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
    if (@(Get-ProjectEditors).Count -gt 0) {
        throw "Editor still open after $TimeoutSeconds s (a save dialog waiting?). Close it and re-run."
    }

    Get-Process -Name 'LiveCodingConsole' -ErrorAction SilentlyContinue |
        ForEach-Object { $_ | Stop-Process -Force }
    Write-Host 'Editor closed.' -ForegroundColor Green
}

# ---- 2. Build ------------------------------------------------------------------------

Write-Step "Building Win64 $Configuration into $ArchiveDir (log: $LogFile)..."
$started = Get-Date
& $RunUAT BuildCookRun "-project=$UProject" -platform=Win64 "-clientconfig=$Configuration" `
    -build -cook -stage -pak -iostore -compressed -archive "-archivedirectory=$ArchiveDir" `
    -unattended -utf8output 2>&1 | Tee-Object -FilePath $LogFile
$exitCode = $LASTEXITCODE
$elapsed = [int]((Get-Date) - $started).TotalMinutes

if ($exitCode -ne 0) {
    Write-Host "BUILD FAILED (exit code $exitCode, $elapsed min). See $LogFile." -ForegroundColor Red
}
else {
    Write-Host "Build succeeded ($elapsed min): $ArchiveDir\Windows" -ForegroundColor Green
}

# ---- 3. Reopen the editor ---------------------------------------------------------------

if ($wasOpen -and -not $NoLaunch) {
    # Someone may have reopened it during the build; a second editor on the project risks
    # overwriting each other's saves.
    if (@(Get-ProjectEditors).Count -gt 0) {
        Write-Step 'Editor already open again - not opening a second one.'
    }
    else {
        Write-Step 'Opening the editor...'
        Start-Process -FilePath $EditorExe -ArgumentList "`"$UProject`""
    }
}
exit $exitCode
