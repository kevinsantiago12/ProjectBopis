// M_HUDBar Custom node: a slanted HUD bar of any length, texture tiled (never stretched).
// Paste into a Custom node. Output Type: CMOT Float 4 (rgb = colour, a = opacity).
// Same maths as shade() in CutHUDSheet.py, which renders the preview.
//
// Custom node inputs (name: what to wire in)
//   UV                 TexCoord[0]
//   Length             scalar param, bar length in Slate px (keep equal to the Image's width)
//   Height             scalar param, bar height in Slate px (keep equal to the Image's height)
//   Fill               scalar param, 0..1
//   Slope              scalar param, end slope in px across per px down (1 = 45 deg)
//   OutlineWidth       scalar param, px of outline on the slanted ends (~1)
//   OutlineColor       vector param, the fill tile's outline colour
//   TrackOutlineColor  vector param, the Empty tile's outline colour
//   TrackOpacity       scalar param, how solid the empty part is (0..1)
//   FillTex            TextureObjectParameter, T_HUD_BarTile_Health or _Focus
//   FillAspect         scalar param, FillTex width / height
//   TrackTex           TextureObjectParameter, T_HUD_BarTile_Empty
//   TrackAspect        scalar param, TrackTex width / height

float px = UV.x * Length;                 // along the bar, in px
float py = UV.y * Height;                 // down from the top edge, in px

float xl = py * Slope;                    // left end, leaning "\"
float xr = Length - py * Slope;           // right end, leaning "/"
float cover = saturate(px - xl + 0.5) * saturate(xr - px + 0.5);

// Outline along both slanted ends (the tiles carry the top and bottom outlines themselves).
float edge = min(px - xl, xr - px) / sqrt(1.0 + Slope * Slope);
float outline = saturate(OutlineWidth + 0.5 - edge);

// Fill front, parallel to the right end. Fill = 1 reaches the right end; 0 shows nothing.
float front = Fill * Length - py * Slope;
float filled = saturate(front - px + 0.5);

// Tiles are sampled in px scaled by height, so they keep their aspect at any bar length.
float4 f = Texture2DSample(FillTex, FillTexSampler, float2(px / (Height * FillAspect), UV.y));
float4 t = Texture2DSample(TrackTex, TrackTexSampler, float2(px / (Height * TrackAspect), UV.y));

float3 fillRgb = lerp(f.rgb, OutlineColor, outline);
float3 trackRgb = lerp(t.rgb, TrackOutlineColor, outline);

float3 rgb = lerp(trackRgb, fillRgb, filled);
float a = cover * lerp(t.a * TrackOpacity, f.a, filled);
return float4(rgb, a);
