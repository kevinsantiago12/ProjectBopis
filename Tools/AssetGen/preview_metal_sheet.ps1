<#
.SYNOPSIS
    Offline preview of M_BackAlleys_MetalSheet's paint layer (create_metal_sheet_ue.py), so the instance colours can be
    tuned without the editor. Applies the shader's colour formula to the pack's T_MetalPlate_A_001_D.png (unlit) and
    writes one strip per instance to Saved/AssetGen/export/metal_sheet_preview.png.

    Keep FORMULA in step with the "Color" custom node in create_metal_sheet_ue.py. Colours are linear, like the shader.
#>
param([int]$Size = 512)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging;
public static class SheetPreview {
    static double Lin(double c) { return c <= 0.04045 ? c / 12.92 : Math.Pow((c + 0.055) / 1.055, 2.4); }
    static int Srgb(double c) { c = Math.Max(0, Math.Min(1, c)); c = c <= 0.0031308 ? c * 12.92 : 1.055 * Math.Pow(c, 1 / 2.4) - 0.055; return (int)Math.Round(c * 255); }
    static double Smooth(double a, double b, double x) { double t = Math.Max(0, Math.Min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); }
    // FORMULA: same as the shader's Color node.
    public static void Paint(Bitmap src, Bitmap dst, int ox, double pr, double pg, double pb, double cover, double wear, double tr, double tg, double tb) {
        for (int y = 0; y < src.Height; y++) for (int x = 0; x < src.Width; x++) {
            Color c = src.GetPixel(x, y);
            double r = Lin(c.R / 255.0) * tr, g = Lin(c.G / 255.0) * tg, b = Lin(c.B / 255.0) * tb;
            double dr = Lin(c.R / 255.0), db = Lin(c.B / 255.0);
            double lum = 0.3 * dr + 0.59 * Lin(c.G / 255.0) + 0.11 * db;
            double rust = Math.Max(0, Math.Min(1, (dr - db) * 6));
            double m = cover * (1 - Smooth(wear - 0.15, wear + 0.15, rust));
            double k = 0.55 + 0.9 * lum;
            dst.SetPixel(ox + x, y, Color.FromArgb(Srgb(r + (pr * k - r) * m), Srgb(g + (pg * k - g) * m), Srgb(b + (pb * k - b) * m)));
        }
    }
}
"@
$img = [System.Drawing.Image]::FromFile((Join-Path $Root 'Content\AsiaSlum\Textures\T_MetalPlate_A_001_D.png'))
$src = New-Object System.Drawing.Bitmap $Size, $Size
$g = [System.Drawing.Graphics]::FromImage($src); $g.DrawImage($img, 0, 0, $Size, $Size); $g.Dispose(); $img.Dispose()
# Name, PaintColor (linear), Coverage, Wear, BaseTint: keep in step with the instances in create_metal_sheet_ue.py
$Looks = @(
    @('Galv',     0, 0, 0,             0.0, 0.5,  1, 1, 1),
    @('RedOxide', 0.30, 0.075, 0.035,  0.9, 0.3,  1, 1, 1),
    @('Rust',     0.16, 0.06, 0.025,   0.75, 0.3, 0.6, 0.42, 0.3)
)
$dst = New-Object System.Drawing.Bitmap ($Size * $Looks.Count), $Size
for ($i = 0; $i -lt $Looks.Count; $i++) {
    $l = $Looks[$i]
    [SheetPreview]::Paint($src, $dst, $i * $Size, $l[1], $l[2], $l[3], $l[4], $l[5], $l[6], $l[7], $l[8])
}
$out = Join-Path $Root 'Saved\AssetGen\export\metal_sheet_preview.png'
New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
$dst.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$src.Dispose(); $dst.Dispose()
"Wrote $out ($($Looks | ForEach-Object { $_[0] }))"
