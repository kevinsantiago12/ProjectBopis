// M_HUDIcon's Custom node (Output Type CMOT Float 4): a HUD icon with a stroke (outline) round
// its alpha, StrokeWidth screen pixels wide at any Image size, Scale Box or not.
// Inputs: UV (TexCoord 0), Tex (the Texture Object parameter "Texture"), StrokeWidth (px),
// StrokeColor (vector parameter: rgb, and a for the stroke's opacity).
// Returns float4(rgb, alpha), straight alpha; the graph multiplies rgb by Brightness and alpha by
// Opacity.

// One screen pixel in UV, per axis.
float2 px = float2(length(float2(ddx(UV.x), ddy(UV.x))), length(float2(ddx(UV.y), ddy(UV.y))));

// Draw the icon StrokeWidth px inside its quad, so an icon touching its texture's edge still has
// room for the stroke there.
float2 inset = StrokeWidth * px;
float2 uv = (UV - inset) / max(1.0 - 2.0 * inset, 1e-4);

// Outside 0..1 counts as empty, whatever the texture's address mode.
float4 icon = Texture2DSample(Tex, TexSampler, uv);
icon *= (all(uv >= 0.0) && all(uv <= 1.0)) ? 1.0 : 0.0;

// The stroke: the most alpha within StrokeWidth px, from two rings of 12 taps.
float ring = 0.0;
[unroll]
for (int i = 0; i < 12; i++)
{
	float angle = i * (6.2831853 / 12.0);
	float2 offset = float2(cos(angle), sin(angle)) * px * StrokeWidth;
	[unroll]
	for (int r = 1; r <= 2; r++)
	{
		float2 s = uv + offset * (r * 0.5);
		float inside = (all(s >= 0.0) && all(s <= 1.0)) ? 1.0 : 0.0;
		ring = max(ring, Texture2DSample(Tex, TexSampler, s).a * inside);
	}
}

// The icon over its stroke. Faint alpha (specks in the source's empty area) grows no stroke; the
// texture needs mipmaps for the ring's edge, and the icon's, to come out anti-aliased.
float stroke = smoothstep(0.05, 0.55, ring) * StrokeColor.a * (1.0 - icon.a);
float alpha = icon.a + stroke;
float3 rgb = (icon.rgb * icon.a + StrokeColor.rgb * stroke) / max(alpha, 1e-4);
return float4(rgb, alpha);
