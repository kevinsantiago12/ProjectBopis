"""The flash's look, in one place: preview.py draws it with numpy and make_ue.py writes it into the material's
HLSL, so the two can't drift apart. Lengths are fractions of the card (see bl_mesh.py for the cards).

Age runs 0 -> 1 over the flash's life. The component grows the mesh over GROW_TIME of it; the material does
the rest: the flame's body is its shape times noise, and a threshold that rises with age burns it away from
the thin edges inward, while the colour cools from HOT through MID to COOL."""

# --- Mesh (bl_mesh.py) ---------------------------------------------------------------------------------------
FIN_PLANES = 3          # crossed side cards through the barrel axis, 180/FIN_PLANES degrees apart
STAR_X = 0.06           # the front card's distance out of the muzzle, of the length
STAR_HALF = 0.7         # the front card's half-size, of the width

# --- Growth (UMuzzleFlashComponent's defaults) ---------------------------------------------------------------
START_LENGTH = 0.45     # length at the first frame, of the full length
START_WIDTH = 0.6
GROW_TIME = 0.3         # of the life, eased out

# --- Shape -------------------------------------------------------------------------------------------------
# Side petal: the flame's half-width along the card is PETAL_WIDTH * u^PETAL_RISE * (1-u)^PETAL_FALL
# (u = 0 at the muzzle, 1 at the tip; 1 = the card's edge). Widest about a third of the way out. Each of the
# six petals (two per card) reaches its own length, PETAL_SHORTEST..1 of the card.
PETAL_WIDTH = 1.6
PETAL_RISE = 0.45
PETAL_FALL = 0.9
PETAL_SHORTEST = 0.7
# Front star: Petals spikes, cos^STAR_SHARP across each; reach STAR_REACH * (STAR_CORE + (1 - STAR_CORE) *
# spike * its length), each spike's length random in SPIKE_SHORTEST..1.
STAR_SHARP = 6.0
STAR_CORE = 0.4
STAR_REACH = 0.9
SPIKE_SHORTEST = 0.45
SPIKE_JITTER = 0.3      # each spike leans off its even spacing by up to this much of the gap
WARP = 0.35             # noise pushes the outline in and out by up to this, so no edge is smooth
# Round base (the default; the material's Spikes parameter, 0..1, blends back to the star and plain petals):
# a ball at the muzzle, BALL of the flash's width in radius. From the front it's a ragged disc; from the side,
# a round end to the flame. It's round when the flash is LENGTH_PER_WIDTH widths long; other ratios squash it.
BALL = 0.42
LENGTH_PER_WIDTH = 1.7
BALL_U = BALL / LENGTH_PER_WIDTH        # its radius along the side cards, of the length
DISC_REACH = BALL / STAR_HALF           # its radius on the front card, of the card's half-size

# --- Noise and burn ------------------------------------------------------------------------------------------
NOISE_MIP = 1.0         # sampled at a fixed mip: no seam at the star's angle wrap, and soft enough
NOISE_SCALE_2 = 2.3     # a second, finer sample
NOISE_MIX = 0.35        # of the finer one
NOISE_LOW = 0.15        # the texture (read back to its sRGB values) is stretched from LOW..HIGH to 0..1
NOISE_HIGH = 0.8
DENSITY_BASE = 0.5      # body = shape * (DENSITY_BASE + DENSITY_NOISE * noise)
DENSITY_NOISE = 0.7
BURN_START = 0.3        # the burn begins at this age (until then the flame grows and churns)...
BURN_CURVE = 1.5        # ...slowly at first (the remaining life to this power)...
BURN_FROM = 0.05        # ...from this threshold, rising to BURN_TO at the end of life
BURN_TO = 0.95
FADE_LAST = 0.2         # and the last part of life fades out whatever is left, so the end never pops

# --- Heat and colour ---------------------------------------------------------------------------------------
HEAT_DENSITY = 0.7      # heat = body * HEAT_DENSITY + nearness to the muzzle * HEAT_BIAS - age * HEAT_AGE
HEAT_BIAS = 0.3
HEAT_AGE = 0.8
POP = 1.0               # the bang: this much brighter (and hotter) on the first frame...
POP_TIME = 0.15         # ...easing back to normal by this age

# --- Material parameters (defaults; tune them on MI_MuzzleFlash) ---------------------------------------------
PARAMS = {
    "Intensity": 1.0,
    "Softness": 0.12,     # how soft the burning edge is
    "Flow": 0.6,          # how far the gas moves out along the flame over its life, in noise tiles
    "FacingMin": 0.12,    # a card fades out as it turns edge-on: gone below this |cos| of the view angle...
    "FacingMax": 0.55,    # ...whole above this
    "DepthFade": 6.0,     # cm: softens the flame where it meets a wall
    "Spikes": 0.0,        # 0: the round base; 1: the first version's spiky star and pointed petals
}
COLOURS = {               # linear, HDR (the pack's flash peaks at about 40 red)
    "HotColour": (40.0, 28.0, 14.0),
    "MidColour": (30.0, 8.0, 1.5),
    "CoolColour": (6.0, 0.8, 0.1),
}
