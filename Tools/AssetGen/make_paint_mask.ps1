<#
.SYNOPSIS
    Makes T_BackAlleys_PaintChips.png: a seamless tiling paint-wear mask, cut from the inside of Favela's T_decal_02 (the
    mask every Favela paint decal uses). Offline, no editor. The wall material M_BackAlleys_PaintedWall tiles it, so its
    paint chips like the decals do, without the decal's rough outer edge repeating as a grid.

.DESCRIPTION
    Crops $Margin px off T_decal_02 (the rough border), then folds the last $Overlap px of each axis over the first. In
    the fold, both sides' dark marks are kept at full strength instead of being averaged, so specks don't fade along the
    seam. Resampled to $Size with wrapping, so the edges still meet.

    Values stay as they are in the source (sRGB-encoded grey): the material samples this exactly as the decal samples
    T_decal_02, so the same value gives the same paint coverage.

    Writes Saved/AssetGen/import/paint_mask/T_BackAlleys_PaintChips.png, and _tiled2x2.jpg to check for seams.
#>
param(
    [string]$Source = 'Saved\LevelGen\decals\T_decal_02.png',   # exported by Tools/LevelGen/analysis/inspect_decals_ue.py
    [string]$Out = 'Saved\AssetGen\import\paint_mask',
    [int]$MarginLow = 130,
    [int]$MarginHigh = 144,
    [int]$Overlap = 64,
    [int]$Size = 1024
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class PaintMask {
    static double Sm(double t) { t = Math.Max(0, Math.Min(1, t)); return t * t * (3 - 2 * t); }
    // One fold along an axis: g is w x h; returns (w - overlap) x h. Dark marks from both sides survive at full strength.
    static float[] FoldX(float[] g, int w, int h, int b, out int nw) {
        int n = w - b; nw = n; var o = new float[n * h];
        for (int y = 0; y < h; y++) for (int x = 0; x < n; x++) {
            float a = g[y * w + x];
            if (x >= b) { o[y * n + x] = a; continue; }
            float c = g[y * w + x + n];
            double t = (x + 0.5) / b;
            double da = (1 - a) * Sm(t * 2), dc = (1 - c) * Sm((1 - t) * 2);
            o[y * n + x] = (float)(1 - Math.Max(da, dc));
        }
        return o; }
    static float[] Swap(float[] g, int w, int h) { var o = new float[w * h]; for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) o[x * h + y] = g[y * w + x]; return o; }
    public static byte[] Make(Bitmap src, int lo, int hi, int b, int size, out string info) {
        var d = src.LockBits(new Rectangle(0, 0, src.Width, src.Height), ImageLockMode.ReadOnly, PixelFormat.Format24bppRgb);
        var a = new byte[d.Stride * src.Height]; Marshal.Copy(d.Scan0, a, 0, a.Length); int stride = d.Stride; src.UnlockBits(d);
        int cw = src.Width - lo - hi, ch = src.Height - lo - hi;
        var g = new float[cw * ch]; double sum = 0;
        for (int y = 0; y < ch; y++) for (int x = 0; x < cw; x++) { g[y * cw + x] = a[(y + lo) * stride + (x + lo) * 3 + 1] / 255f; sum += g[y * cw + x]; }
        int nw, nh;
        var f = FoldX(g, cw, ch, b, out nw);
        f = Swap(f, nw, ch);
        f = FoldX(f, ch, nw, b, out nh);
        f = Swap(f, nh, nw);   // now nw x nh
        var o = new byte[size * size]; double sum2 = 0;
        for (int y = 0; y < size; y++) for (int x = 0; x < size; x++) {   // bilinear, wrapping
            double u = (x + 0.5) * nw / size - 0.5, v = (y + 0.5) * nh / size - 0.5;
            int x0 = (int)Math.Floor(u), y0 = (int)Math.Floor(v); double fu = u - x0, fv = v - y0;
            int xa = (x0 + nw) % nw, xb = (x0 + 1 + nw) % nw, ya = (y0 + nh) % nh, yb = (y0 + 1 + nh) % nh;
            double val = (f[ya * nw + xa] * (1 - fu) + f[ya * nw + xb] * fu) * (1 - fv) + (f[yb * nw + xa] * (1 - fu) + f[yb * nw + xb] * fu) * fv;
            o[y * size + x] = (byte)Math.Round(Math.Max(0, Math.Min(1, val)) * 255); sum2 += val;
        }
        info = string.Format("crop {0}x{1} mean {2:0.000}; tile {3}x{4} resampled to {5}, mean {6:0.000}", cw, ch, sum / (cw * ch), nw, nh, size, sum2 / (size * size));
        return o; }
    public static Bitmap Grey(byte[] g, int size, int repeat) {
        int s = size * repeat; var b = new Bitmap(s, s, PixelFormat.Format24bppRgb);
        var d = b.LockBits(new Rectangle(0, 0, s, s), ImageLockMode.WriteOnly, PixelFormat.Format24bppRgb);
        var a = new byte[d.Stride * s];
        for (int y = 0; y < s; y++) for (int x = 0; x < s; x++) { byte v = g[(y % size) * size + x % size]; int i = y * d.Stride + x * 3; a[i] = a[i + 1] = a[i + 2] = v; }
        Marshal.Copy(a, 0, d.Scan0, a.Length); b.UnlockBits(d); return b; }
}
"@
$img = [System.Drawing.Image]::FromFile((Join-Path $Root $Source))
$src = New-Object System.Drawing.Bitmap $img; $img.Dispose()
$info = ''
$grey = [PaintMask]::Make($src, $MarginLow, $MarginHigh, $Overlap, $Size, [ref]$info)
$src.Dispose()
$dir = Join-Path $Root $Out; New-Item -ItemType Directory -Force $dir | Out-Null
$b = [PaintMask]::Grey($grey, $Size, 1); $b.Save((Join-Path $dir 'T_BackAlleys_PaintChips.png'), [System.Drawing.Imaging.ImageFormat]::Png); $b.Dispose()
$t = [PaintMask]::Grey($grey, $Size, 2); $small = New-Object System.Drawing.Bitmap 1024, 1024
$g = [System.Drawing.Graphics]::FromImage($small); $g.InterpolationMode = 'HighQualityBicubic'; $g.DrawImage($t, 0, 0, 1024, 1024); $g.Dispose()
$small.Save((Join-Path $dir 'T_BackAlleys_PaintChips_tiled2x2.jpg'), [System.Drawing.Imaging.ImageFormat]::Jpeg); $small.Dispose(); $t.Dispose()
$info
"Wrote $dir"
