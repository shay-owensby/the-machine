"""Colour science for the Analytics & Insights design system.

Pure standard library. Everything the design system claims about contrast and
colour-vision separation is *computed here*, not asserted in prose, so a change
to a token is checked rather than trusted.

Conventions
-----------
* Colours travel as ``#rrggbb`` strings at the boundaries and as ``(r, g, b)``
  float triples in ``0..1`` internally.
* Contrast is WCAG 2.1 relative luminance.
* Perceptual distance is CIEDE2000 against D65.
* Colour-vision deficiency uses Viénot-Brettel-Mollon (1999) for protan and
  deutan and Brettel (1997) for tritan, which is what the accessibility
  literature uses to check chart palettes.
"""

import math

__all__ = [
    "hex_to_rgb", "rgb_to_hex", "relative_luminance", "contrast_ratio",
    "rgb_to_lab", "lab_to_rgb", "delta_e_2000", "simulate_cvd",
    "set_lightness", "adjust_to_contrast", "mix", "is_valid_hex", "normalise_hex",
    "worst_pair_separation", "CVD_KINDS",
]

CVD_KINDS = ("normal", "protan", "deutan", "tritan")

# D65, 2 degree observer.
_WHITE = (0.95047, 1.00000, 1.08883)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def is_valid_hex(value):
    """True for ``#rgb`` / ``#rrggbb``, with or without the leading hash."""
    if not isinstance(value, str):
        return False
    s = value.strip().lstrip("#")
    if len(s) not in (3, 6):
        return False
    try:
        int(s, 16)
    except ValueError:
        return False
    return True


def normalise_hex(value):
    """``#AbC`` -> ``#aabbcc``. Raises ValueError on anything else."""
    if not is_valid_hex(value):
        raise ValueError("not a hex colour: %r" % (value,))
    s = value.strip().lstrip("#").lower()
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return "#" + s


def hex_to_rgb(value):
    s = normalise_hex(value).lstrip("#")
    return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def rgb_to_hex(rgb):
    def clamp(v):
        return max(0, min(255, int(round(v * 255))))
    return "#%02x%02x%02x" % tuple(clamp(c) for c in rgb)


# --------------------------------------------------------------------------
# sRGB transfer function
# --------------------------------------------------------------------------

def _to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _to_srgb(c):
    c = max(0.0, min(1.0, c))
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


# --------------------------------------------------------------------------
# WCAG contrast
# --------------------------------------------------------------------------

def relative_luminance(color):
    r, g, b = hex_to_rgb(color) if isinstance(color, str) else color
    r, g, b = _to_linear(r), _to_linear(g), _to_linear(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    """WCAG 2.1 contrast ratio, 1.0 (identical) to 21.0 (black on white)."""
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# --------------------------------------------------------------------------
# CIELAB
# --------------------------------------------------------------------------

def _rgb_to_xyz(rgb):
    r, g, b = (_to_linear(c) for c in rgb)
    return (
        0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
        0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
        0.0193339 * r + 0.1191920 * g + 0.9503041 * b,
    )


def _xyz_to_rgb(xyz):
    x, y, z = xyz
    r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z
    return tuple(_to_srgb(c) for c in (r, g, b))


def _f(t):
    return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29


def _f_inv(t):
    return t ** 3 if t ** 3 > 216 / 24389 else (t - 4 / 29) * 108 / 841


def rgb_to_lab(color):
    rgb = hex_to_rgb(color) if isinstance(color, str) else color
    x, y, z = _rgb_to_xyz(rgb)
    fx, fy, fz = _f(x / _WHITE[0]), _f(y / _WHITE[1]), _f(z / _WHITE[2])
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def lab_to_rgb(lab):
    L, a, b = lab
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    xyz = (_f_inv(fx) * _WHITE[0], _f_inv(fy) * _WHITE[1], _f_inv(fz) * _WHITE[2])
    return _xyz_to_rgb(xyz)


# --------------------------------------------------------------------------
# CIEDE2000
# --------------------------------------------------------------------------

def delta_e_2000(c1, c2):
    """Perceptual distance. Roughly: <1 invisible, ~2.3 a just-noticeable
    difference, >10 unmistakably different colours."""
    L1, a1, b1 = rgb_to_lab(c1)
    L2, a2, b2 = rgb_to_lab(c2)

    kL = kC = kH = 1.0
    C1 = math.hypot(a1, b1)
    C2 = math.hypot(a2, b2)
    Cbar = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cbar ** 7 / (Cbar ** 7 + 25 ** 7))) if Cbar > 0 else 0.0

    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0.0

    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)

    Lbar = (L1 + L2) / 2
    Cbarp = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbarp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbarp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbarp = (h1p + h2p + 360) / 2
    else:
        hbarp = (h1p + h2p - 360) / 2

    T = (1
         - 0.17 * math.cos(math.radians(hbarp - 30))
         + 0.24 * math.cos(math.radians(2 * hbarp))
         + 0.32 * math.cos(math.radians(3 * hbarp + 6))
         - 0.20 * math.cos(math.radians(4 * hbarp - 63)))
    dtheta = 30 * math.exp(-(((hbarp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbarp ** 7 / (Cbarp ** 7 + 25 ** 7)) if Cbarp > 0 else 0.0
    Sl = 1 + (0.015 * (Lbar - 50) ** 2) / math.sqrt(20 + (Lbar - 50) ** 2)
    Sc = 1 + 0.045 * Cbarp
    Sh = 1 + 0.015 * Cbarp * T
    Rt = -math.sin(math.radians(2 * dtheta)) * Rc

    return math.sqrt(
        (dLp / (kL * Sl)) ** 2
        + (dCp / (kC * Sc)) ** 2
        + (dHp / (kH * Sh)) ** 2
        + Rt * (dCp / (kC * Sc)) * (dHp / (kH * Sh))
    )


# --------------------------------------------------------------------------
# Colour-vision deficiency simulation
# --------------------------------------------------------------------------

# LMS transform (Hunt-Pointer-Estevez, normalised to D65) applied to linear RGB.
_RGB_TO_LMS = (
    (0.31399022, 0.63951294, 0.04649755),
    (0.15537241, 0.75789446, 0.08670142),
    (0.01775239, 0.10944209, 0.87256922),
)
_LMS_TO_RGB = (
    (5.47221206, -4.64196010, 0.16963708),
    (-1.12524190, 2.29317094, -0.16789520),
    (0.02980165, -0.19318073, 1.16364789),
)

# Viénot-Brettel-Mollon dichromat projections, in LMS.
_CVD_MATRIX = {
    "protan": ((0.0, 1.05118294, -0.05116099), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "deutan": ((1.0, 0.0, 0.0), (0.9513092, 0.0, 0.04866992), (0.0, 0.0, 1.0)),
    "tritan": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-0.86744736, 1.86727089, 0.0)),
}


def _matmul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def simulate_cvd(color, kind):
    """Return the colour as seen with ``kind`` dichromacy.

    ``kind`` is one of ``normal``, ``protan``, ``deutan``, ``tritan``.
    """
    if kind == "normal":
        return normalise_hex(color) if isinstance(color, str) else rgb_to_hex(color)
    if kind not in _CVD_MATRIX:
        raise ValueError("unknown CVD kind: %r" % (kind,))
    rgb = hex_to_rgb(color) if isinstance(color, str) else color
    lin = tuple(_to_linear(c) for c in rgb)
    lms = _matmul(_RGB_TO_LMS, lin)
    lms = _matmul(_CVD_MATRIX[kind], lms)
    out = _matmul(_LMS_TO_RGB, lms)
    return rgb_to_hex(tuple(_to_srgb(c) for c in out))


def worst_pair_separation(colors, kinds=CVD_KINDS):
    """Smallest CIEDE2000 between any two colours, under each vision type.

    Returns ``{kind: (delta_e, colour_a, colour_b)}``. This is the check that
    decides whether a categorical palette is safe to use.
    """
    result = {}
    for kind in kinds:
        worst = None
        seen = [(c, simulate_cvd(c, kind)) for c in colors]
        for i in range(len(seen)):
            for j in range(i + 1, len(seen)):
                d = delta_e_2000(seen[i][1], seen[j][1])
                if worst is None or d < worst[0]:
                    worst = (d, seen[i][0], seen[j][0])
        result[kind] = worst
    return result


# --------------------------------------------------------------------------
# Manipulation
# --------------------------------------------------------------------------

def set_lightness(color, L):
    """Return ``color`` with CIELAB lightness forced to ``L`` (0..100).

    Hue and chroma are preserved, so a brand colour keeps its identity while
    moving to a lightness that meets a contrast requirement.
    """
    _, a, b = rgb_to_lab(color)
    return rgb_to_hex(lab_to_rgb((max(0.0, min(100.0, L)), a, b)))


def mix(a, b, t):
    """Blend two colours in linear-light sRGB. ``t=0`` -> ``a``, ``t=1`` -> ``b``."""
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    lin = tuple(_to_linear(ra[i]) * (1 - t) + _to_linear(rb[i]) * t for i in range(3))
    return rgb_to_hex(tuple(_to_srgb(c) for c in lin))


def adjust_to_contrast(color, background, target, direction="darker"):
    """Move ``color`` along CIELAB L* until it meets ``target`` contrast.

    Used to turn an arbitrary client brand colour into one that is legible as
    text on the report surface without discarding the brand's hue. Returns the
    original colour unchanged when it already passes. Binary search on L*, so
    it lands on the *closest* passing colour rather than an arbitrary darker one.
    """
    if contrast_ratio(color, background) >= target:
        return normalise_hex(color)

    L0 = rgb_to_lab(color)[0]
    lo, hi = (0.0, L0) if direction == "darker" else (L0, 100.0)
    best = set_lightness(color, lo if direction == "darker" else hi)
    if contrast_ratio(best, background) < target:
        # Even the extreme fails; fall back to pure black or white.
        return "#000000" if direction == "darker" else "#ffffff"

    for _ in range(40):
        mid = (lo + hi) / 2
        candidate = set_lightness(color, mid)
        if contrast_ratio(candidate, background) >= target:
            best = candidate
            if direction == "darker":
                lo = mid
            else:
                hi = mid
        else:
            if direction == "darker":
                hi = mid
            else:
                lo = mid
    return best
