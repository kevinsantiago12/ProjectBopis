<#
.SYNOPSIS
    Repairs the GPT hollow-block texture (2026-11-03): restores the mortar joints its face mask lost, and rebuilds the
    normal map from the corrected joint layout. Offline, no editor. The inputs stay untouched.

.DESCRIPTION
    GPT's T_HollowBlocks_01_BC.png kept the layout of the Favela brick (T_Bricks_01_BC) but its face mask merged
    neighbouring blocks wherever a joint was faint, leaving slabs of 2-4 blocks with no joints.
    In the source brick, mortar is low-saturation (bricks ~0.5, mortar 0.1-0.2); so are the clay grooves (2-3 px
    lines inside the bricks). The joints follow the running-bond grid, so the grid is found ($RowFrac, $ColFrac) and
    only grey pixels within $Reach px of it count as mortar. So:
      - BC: where the source pixel's saturation is under $MortarSat it's mortar, and the source pixel is used;
        everywhere else GPT's concrete is kept.
      - Normal (DirectX, Unreal's convention): from a height map = block faces (1) vs mortar (0), softened by two box
        blurs (a rounded edge about $Bevel px), plus fine detail from the concrete's luminance. The green sign is
        checked against GPT's own DirectX map where both agree, and flipped if needed.
    Writes T_HollowBlocks_01_BC.png, T_HollowBlocks_01_N.png and mask_diff.png (red = joints restored) to $Out.
#>
param(
    [string]$Gpt = 'Saved\AssetGen\import\hollow_blocks_zip\philippine-hollow-blocks',
    [string]$Source = 'Saved\AssetGen\export\T_Bricks_01_BC.png',
    [string]$Out = 'Saved\AssetGen\import\hollow_blocks_fixed',
    [double]$MortarSat = 0.28,
    [double]$RowFrac = 0.35,
    [double]$ColFrac = 0.4,
    [int]$MinCourse = 40,
    [int]$Reach = 4,
    [int]$Bevel = 3,
    [double]$Strength = 6.0,
    [double]$Detail = 0.6
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class ChbRepair {
    public static byte[] Read(Bitmap b) {
        var d = b.LockBits(new Rectangle(0, 0, b.Width, b.Height), ImageLockMode.ReadOnly, PixelFormat.Format24bppRgb);
        var a = new byte[d.Stride * b.Height]; Marshal.Copy(d.Scan0, a, 0, a.Length); b.UnlockBits(d); return a; }
    public static Bitmap Write(byte[] a, int w, int h) {
        var b = new Bitmap(w, h, PixelFormat.Format24bppRgb);
        var d = b.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format24bppRgb);
        Marshal.Copy(a, 0, d.Scan0, a.Length); b.UnlockBits(d); return b; }
    static float[] Blur(float[] s, int w, int h, int r) {   // box blur, wrapping (the texture tiles)
        var t = new float[s.Length]; var o = new float[s.Length]; float n = 2 * r + 1;
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { float acc = 0; for (int k = -r; k <= r; k++) acc += s[y * w + ((x + k + w) % w)]; t[y * w + x] = acc / n; }
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { float acc = 0; for (int k = -r; k <= r; k++) acc += t[((y + k + h) % h) * w + x]; o[y * w + x] = acc / n; }
        return o; }
    static bool[] MinMax(bool[] s, int w, int h, int r, bool all) {   // square erode (all) / dilate (any), wrapping
        var t = new bool[s.Length]; var o = new bool[s.Length];
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { bool v = all; for (int k = -r; k <= r; k++) { bool q = s[y * w + ((x + k + w) % w)]; v = all ? v && q : v || q; } t[y * w + x] = v; }
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { bool v = all; for (int k = -r; k <= r; k++) { bool q = t[((y + k + h) % h) * w + x]; v = all ? v && q : v || q; } o[y * w + x] = v; }
        return o; }
    static bool[] Grow(bool[] s, int w, int h, int r) { return MinMax(s, w, h, r, false); }
    // Returns: [0] new BC bytes, [1] normal bytes, [2] diff bytes; stats in info.
    public static byte[][] Run(byte[] src, byte[] gpt, byte[] gptN, int w, int h, int stride, double sat, double rowT, double colT, int minCourse, int reach, int bevel, double strength, double detail, out string info) {
        var bc = (byte[])gpt.Clone(); var diff = new byte[gpt.Length]; var height = new float[w * h];
        // Grey pixels in the source: the joints, but also the clay brick's grooves (thin lines inside the bricks). The
        // joints follow the running-bond grid, so find the grid: bed joints are rows that are mostly grey across the
        // whole width; head joints are columns that are mostly grey over one course. The grid is the joint core (always
        // mortar, so faint joints stay continuous); grey source pixels within reach px of it keep the source's
        // irregular edges; grey pixels further away (the grooves) are dropped. Wrapping: the texture tiles.
        var grey = new bool[w * h];
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
            int i = y * stride + x * 3; byte b = src[i], g = src[i + 1], r = src[i + 2];
            int mx = Math.Max(r, Math.Max(g, b)), mn = Math.Min(r, Math.Min(g, b));
            grey[y * w + x] = mx == 0 || (mx - mn) / (double)mx < sat; }
        var bed = new bool[h];
        for (int y = 0; y < h; y++) { int cnt = 0; for (int x = 0; x < w; x++) if (grey[y * w + x]) cnt++; bed[y] = cnt > rowT * w; }
        int y0 = Array.IndexOf(bed, true); if (y0 < 0) throw new Exception("no bed joints found");
        var core = new bool[w * h]; int beds = 0, heads = 0, courses = 0;
        for (int y = 0; y < h; y++) if (bed[y]) for (int x = 0; x < w; x++) core[y * w + x] = true;
        for (int k = 0; k < h; ) {   // walk the courses from the first bed joint, wrapping
            int y = (y0 + k) % h;
            if (bed[y]) { if (k == 0 || !bed[(y - 1 + h) % h]) beds++; k++; continue; }
            int len = 0; while (k + len < h && !bed[(y0 + k + len) % h]) len++;
            if (len < minCourse) {   // a sliver between two joint rows: part of the joint
                for (int j = 0; j < len; j++) for (int x = 0; x < w; x++) core[((y0 + k + j) % h) * w + x] = true;
            } else {
                courses++;
                bool prev = false;
                for (int x = 0; x < w; x++) {
                    int cnt = 0; for (int j = 0; j < len; j++) if (grey[((y0 + k + j) % h) * w + x]) cnt++;
                    bool head = cnt > colT * len;
                    if (head && !prev) heads++; prev = head;
                    if (head) for (int j = 0; j < len; j++) core[((y0 + k + j) % h) * w + x] = true;
                }
            }
            k += len;
        }
        var near = Grow(core, w, h, reach);
        var keep = new bool[w * h]; int dropped = 0;
        double mr = 0, mg = 0, mb = 0, gl = 0; int mn2 = 0, gn = 0;
        for (int p = 0; p < w * h; p++) {
            keep[p] = core[p] || (grey[p] && near[p]);
            if (grey[p] && !keep[p]) dropped++;
            int i = (p / w) * stride + (p % w) * 3;
            if (core[p] && grey[p]) { mb += src[i]; mg += src[i + 1]; mr += src[i + 2]; mn2++; }
            if (!keep[p]) { gl += 0.3 * gpt[i + 2] + 0.59 * gpt[i + 1] + 0.11 * gpt[i]; gn++; }
        }
        mr /= Math.Max(1, mn2); mg /= Math.Max(1, mn2); mb /= Math.Max(1, mn2); gl /= Math.Max(1, gn);
        int mortar = 0, restored = 0, filled = 0;
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
            int i = y * stride + x * 3; byte b = src[i], g = src[i + 1], r = src[i + 2];
            bool isMortar = keep[y * w + x];
            bool gptKept = gpt[i] == b && gpt[i + 1] == g && gpt[i + 2] == r;   // GPT left this pixel as source
            if (isMortar) {
                mortar++; if (!gptKept) { restored++; diff[i + 2] = 255; }
                if (grey[y * w + x]) { bc[i] = b; bc[i + 1] = g; bc[i + 2] = r; }
                else {   // a faint joint: mean mortar colour, shaded by GPT's concrete there
                    filled++; diff[i + 1] = 255;
                    double s = Math.Min(1.4, Math.Max(0.6, (0.3 * gpt[i + 2] + 0.59 * gpt[i + 1] + 0.11 * gpt[i]) / gl));
                    bc[i] = (byte)Math.Min(255, mb * s); bc[i + 1] = (byte)Math.Min(255, mg * s); bc[i + 2] = (byte)Math.Min(255, mr * s); }
            }
            else { diff[i] = diff[i + 1] = diff[i + 2] = 60; }
            double lum = (0.3 * bc[i + 2] + 0.59 * bc[i + 1] + 0.11 * bc[i]) / 255.0;
            height[y * w + x] = isMortar ? 0f : 1f;
            height[y * w + x] += (float)(detail * 0.05 * (lum - 0.5));
        }
        var hb = Blur(Blur(height, w, h, bevel), w, h, Math.Max(1, bevel / 2));
        var n = new byte[gpt.Length]; double agree = 0;
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
            double dx = hb[y * w + (x + 1) % w] - hb[y * w + (x - 1 + w) % w];
            double dy = hb[((y + 1) % h) * w + x] - hb[((y - 1 + h) % h) * w + x];   // + = downward in the image
            double nx = -dx * strength, ny = dy * strength, nz = 1;   // green: candidate DirectX sign, checked below
            double l = Math.Sqrt(nx * nx + ny * ny + nz * nz); nx /= l; ny /= l; nz /= l;
            int i = y * stride + x * 3;
            n[i + 2] = (byte)Math.Round((nx * 0.5 + 0.5) * 255); n[i + 1] = (byte)Math.Round((ny * 0.5 + 0.5) * 255); n[i] = (byte)Math.Round((nz * 0.5 + 0.5) * 255);
            agree += (n[i + 1] - 127.5) * (gptN[i + 1] - 127.5);
        }
        bool flipped = agree < 0;
        if (flipped) for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { int i = y * stride + x * 3; n[i + 1] = (byte)(255 - n[i + 1]); }
        info = string.Format("grid: {6} bed joints, {7} courses, {8} head joints; mortar {0} px ({1:P1}), restored {2} ({3:P1}), faint joints filled {9}, grooves dropped {5}, green {4}", mortar, mortar / (double)(w * h), restored, restored / (double)(w * h), flipped ? "flipped to match GPT's DirectX map" : "matches GPT's DirectX map", dropped, beds, courses, heads, filled);
        return new byte[][] { bc, n, diff };
    }
}
"@
function Load($p) { $i = [System.Drawing.Image]::FromFile((Resolve-Path (Join-Path $Root $p))); $b = New-Object System.Drawing.Bitmap $i; $i.Dispose(); $b }
$src = Load $Source; $gbc = Load (Join-Path $Gpt 'T_HollowBlocks_01_BC.png'); $gn = Load (Join-Path $Gpt 'T_HollowBlocks_01_N_DirectX.png')
$w = $src.Width; $h = $src.Height
if ($gbc.Width -ne $w -or $gn.Width -ne $w) { throw "size mismatch" }
$stride = [int]([Math]::Ceiling($w * 3 / 4.0) * 4)
$info = ''
$res = [ChbRepair]::Run([ChbRepair]::Read($src), [ChbRepair]::Read($gbc),[ChbRepair]::Read($gn), $w, $h, $stride, $MortarSat, $RowFrac, $ColFrac, $MinCourse, $Reach, $Bevel, $Strength, $Detail, [ref]$info)
$dir = Join-Path $Root $Out; New-Item -ItemType Directory -Force $dir | Out-Null
$names = 'T_HollowBlocks_01_BC.png', 'T_HollowBlocks_01_N.png', 'mask_diff.png'
for ($k = 0; $k -lt 3; $k++) { $b = [ChbRepair]::Write($res[$k], $w, $h); $b.Save((Join-Path $dir $names[$k]), [System.Drawing.Imaging.ImageFormat]::Png); $b.Dispose() }
$src.Dispose(); $gbc.Dispose(); $gn.Dispose()
"$info"
"Wrote $dir"
