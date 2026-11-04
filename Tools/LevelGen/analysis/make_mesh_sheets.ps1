<#
.SYNOPSIS
    Tiles the mesh renders and thumbnails into labelled sheets, one group at a time, for reviewing a pack's models.
.DESCRIPTION
    Each mesh is a 2 x 2 block: the editor thumbnail (textured, as Unreal shows it), then render_meshes_blender.py's
    views a (from UE -X -Y), b (from UE +X +Y) and t (top, UE +X up). Under it: the name, size in metres
    (UE X x Y x Z) and triangle count. Reads Saved/LevelGen/visual/meshes.json; writes visual/sheets/<group>_<n>.png.
.EXAMPLE
    .\Tools\LevelGen\analysis\make_mesh_sheets.ps1
#>
param([int]$Cell = 150, [int]$Columns = 5, [int]$Rows = 4)
Add-Type -AssemblyName System.Drawing
$vis = Join-Path $PSScriptRoot '..\..\..\Saved\LevelGen\visual' | Resolve-Path
$index = Get-Content (Join-Path $vis 'meshes.json') -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force (Join-Path $vis 'sheets') | Out-Null
$font = New-Object System.Drawing.Font 'Arial', 8
$label = 28
$block = 2 * $Cell
$per = $Columns * $Rows
foreach ($grp in ($index | Group-Object group)) {
    $items = @($grp.Group | Sort-Object name)
    for ($s = 0; $s * $per -lt $items.Count; $s++) {
        $page = $items[($s * $per)..([math]::Min(($s + 1) * $per, $items.Count) - 1)]
        $rowsHere = [math]::Ceiling($page.Count / $Columns)
        $sheet = New-Object System.Drawing.Bitmap ($Columns * $block), ($rowsHere * ($block + $label))
        $g = [System.Drawing.Graphics]::FromImage($sheet)
        $g.Clear([System.Drawing.Color]::Black)
        $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBilinear
        for ($i = 0; $i -lt $page.Count; $i++) {
            $e = $page[$i]
            $x = ($i % $Columns) * $block
            $y = [math]::Floor($i / $Columns) * ($block + $label)
            $tiles = @((Join-Path $vis "thumbs\$($e.group)\$($e.name).jpg"),
                       (Join-Path $vis "renders\$($e.group)\$($e.name)_a.png"),
                       (Join-Path $vis "renders\$($e.group)\$($e.name)_b.png"),
                       (Join-Path $vis "renders\$($e.group)\$($e.name)_t.png"))
            for ($k = 0; $k -lt 4; $k++) {
                if (Test-Path $tiles[$k]) {
                    $img = [System.Drawing.Image]::FromFile($tiles[$k])
                    $g.DrawImage($img, $x + ($k % 2) * $Cell + 1, $y + [math]::Floor($k / 2) * $Cell + 1, $Cell - 2, $Cell - 2)
                    $img.Dispose()
                }
            }
            $size = for ($a = 0; $a -lt 3; $a++) { '{0:0.00}' -f (($e.bounds_max[$a] - $e.bounds_min[$a]) / 100) }
            $g.DrawString("$($e.name)`n$($size -join ' x ') m  $($e.tris) tris", $font, [System.Drawing.Brushes]::White, $x + 2, $y + $block)
        }
        $out = Join-Path $vis ("sheets\{0}_{1:00}.png" -f $grp.Name, $s)
        $sheet.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
        $g.Dispose(); $sheet.Dispose()
    }
    Write-Host "$($grp.Name): $($items.Count) meshes"
}
