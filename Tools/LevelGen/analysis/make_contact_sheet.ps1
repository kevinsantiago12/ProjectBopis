<#
.SYNOPSIS
    Tiles the PNGs in a folder into one labelled contact sheet (System.Drawing; no Python imaging needed).
.EXAMPLE
    .\Tools\LevelGen\analysis\make_contact_sheet.ps1 -Folder Saved\LevelGen\tex -Out Saved\LevelGen\tex_sheet.png
#>
param(
    [Parameter(Mandatory = $true)][string]$Folder,
    [Parameter(Mandatory = $true)][string]$Out,
    [int]$Cell = 220,
    [int]$Columns = 8
)
Add-Type -AssemblyName System.Drawing
$files = Get-ChildItem -Path $Folder -Filter *.png | Sort-Object Name
$rows = [math]::Ceiling($files.Count / $Columns)
$label = 18
$sheet = New-Object System.Drawing.Bitmap ($Columns * $Cell), ($rows * ($Cell + $label))
$g = [System.Drawing.Graphics]::FromImage($sheet)
$g.Clear([System.Drawing.Color]::Black)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBilinear
$font = New-Object System.Drawing.Font 'Arial', 8
for ($i = 0; $i -lt $files.Count; $i++) {
    $x = ($i % $Columns) * $Cell
    $y = [math]::Floor($i / $Columns) * ($Cell + $label)
    $img = [System.Drawing.Image]::FromFile($files[$i].FullName)
    $g.DrawImage($img, $x + 2, $y + 2, $Cell - 4, $Cell - 4)
    $img.Dispose()
    $g.DrawString($files[$i].BaseName, $font, [System.Drawing.Brushes]::White, $x + 2, $y + $Cell)
}
$sheet.Save((Join-Path (Get-Location) $Out), [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $sheet.Dispose()
Write-Host "Wrote $Out ($($files.Count) images)"
