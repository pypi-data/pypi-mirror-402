"""
oxford_palette.py
A minimal library that stores Oxford University theme colours and small helpers
for plotting.

Usage examples
--------------
from oxford_palette import OXFORD_COLORS, hex, rgb, mpl_palette, mpl_cycler

# get hex:
hex("oxford_blue")          # -> '#002147'

# get integer RGB tuple:
rgb("oxford_blue")          # -> (0, 33, 71)

# get matplotlib-ready normalized RGB list:
mpl_palette(["oxford_blue", "oxford_peach", "oxford_mauve"])

# create a matplotlib cycler:
from matplotlib import pyplot as plt
from matplotlib import cycler
plt.rcParams['axes.prop_cycle'] = mpl_cycler(["oxford_blue","oxford_peach"])
"""

from __future__ import annotations
from typing import Tuple, Dict, List, Optional, Iterable, Any, ContextManager
from dataclasses import dataclass
from contextlib import contextmanager
import matplotlib as mpl
from matplotlib import pyplot as plt

__all__ = [
    "OXFORD_COLORS",
    "COLORS_BY_GROUP",
    "hex",
    "rgb",
    "cmyk",
    "pantone",
    "as_rgb_norm",
    "get_names",
    "mpl_palette",
    "mpl_cycler",
    "oxford_style",
]

@dataclass(frozen=True)
class Color:
    name: str
    hex: str
    rgb: Tuple[int, int, int]
    cmyk: Optional[Tuple[int, int, int, int]] = None
    pantone: Optional[str] = None

    def rgb_norm(self) -> Tuple[float, float, float]:
        r, g, b = self.rgb
        return (r / 255.0, g / 255.0, b / 255.0)


# Master colour dictionary
OXFORD_COLORS: Dict[str, Color] = {
    # Key colour
    "oxford_blue": Color("Oxford blue", "#002147", (0, 33, 71), (100, 87, 42, 51), "Pantone 282"),

    # Secondary / supporting palette
    "oxford_mauve": Color("Oxford mauve", "#776885", (119, 104, 133), (58, 60, 27, 10), "Pantone 667C"),
    "oxford_peach": Color("Oxford peach", "#E08D79", (224, 141, 121), (2, 58, 51, 0), "Pantone 4051C"),
    "oxford_potters_pink": Color("Oxford potters pink", "#ED9390", (237, 147, 144), (0, 57, 34, 0), "Pantone 2339C"),
    "oxford_dusk": Color("Oxford dusk", "#C4A29E", (196, 162, 158), (20, 40, 31, 5), "Pantone 6030C"),
    "oxford_lilac": Color("Oxford lilac", "#D1BDD5", (209, 189, 213), (18, 30, 4, 0), "Pantone 524C"),
    "oxford_sienna": Color("Oxford sienna", "#994636", (153, 70, 54), (25, 82, 80, 19), "Pantone 4036C"),
    "oxford_ccb_red": Color("Oxford Red", "#AA1A2D", (190, 15, 52), (18, 100, 74, 8), "Pantone 187C"),
    "oxford_plum": Color("Oxford plum", "#7F055F", (127, 5, 95), (48, 100, 19, 15), "Pantone 2425C"),
    "oxford_coral": Color("Oxford coral", "#FE615A", (254, 97, 90), (0, 79, 56, 0), "Pantone 178C"),
    "oxford_lavender": Color("Oxford lavender", "#D4CDF4", (212, 205, 244), (19, 22, 0, 0), "Pantone 2635C"),
    "oxford_orange": Color("Oxford orange", "#FB5607", (251, 86, 7), (0, 76, 95, 0), "Pantone 1655C"),
    "oxford_pink": Color("Oxford pink", "#E6007E", (230, 0, 126), (0, 100, 0, 0), "Pantone 2385C"),
    "oxford_green": Color("Oxford green", "#426A5A", (66, 106, 90), (79, 35, 64, 26), "Pantone 5545C"),
    "oxford_ocean_grey": Color("Oxford ocean grey", "#789E9E", (120, 158, 158), (61, 22, 37, 4), "Pantone 2211C"),
    "oxford_yellow_ochre": Color("Oxford yellow ochre", "#E2C044", (226, 192, 68), (10, 23, 93, 1), "Pantone 4016C"),
    "oxford_cool_grey": Color("Oxford cool grey", "#E4F0EF", (228, 240, 239), (15, 0, 8, 0), "Pantone 7541C"),
    "oxford_sky_blue": Color("Oxford sky blue", "#B9D6F2", (185, 214, 242), (34, 6, 0, 0), "Pantone 277C"),
    "oxford_sage_green": Color("Oxford sage green", "#A0AF84", (160, 175, 132), (45, 19, 58, 3), "Pantone 7494C"),
    "oxford_viridian": Color("Oxford viridian", "#15616D", (21, 97, 109), (92, 36, 43, 27), "Pantone 5473C"),
    "oxford_royal_blue": Color("Oxford royal blue", "#1D42A6", (29, 66, 166), (96, 75, 0, 0), "Pantone 2126C"),
    "oxford_aqua": Color("Oxford aqua", "#00AAB4", (0, 170, 180), (84, 0, 33, 0), "Pantone 7710C"),
    "oxford_vivid_green": Color("Oxford vivid green", "#65E5AE", (101, 229, 174), (56, 0, 46, 0), "Pantone 3385C"),
    "oxford_lime_green": Color("Oxford lime green", "#95C11F", (149, 193, 31), (54, 0, 100, 0), "Pantone 2292C"),
    "oxford_cerulean_blue": Color("Oxford cerulean blue", "#49B6FF", (73, 182, 255), (68, 11, 0, 0), "Pantone 292C"),
    "oxford_yellow": Color("Oxford lemon yellow", "#F7EF66", (247, 239, 102), (8, 0, 69, 0), "Pantone 3935C"),

    # Neutrals
    "oxford_charcoal": Color("Oxford charcoal", "#211D1C", (33, 29, 28), (70, 67, 61, 81), "Pantone 419 C"),
    "oxford_ash_grey": Color("Oxford ash grey", "#61615F", (97, 97, 95), (57, 46, 48, 36), "Pantone 6215 C"),
    "oxford_umber": Color("Oxford umber", "#89827A", (137, 130, 122), (43, 39, 43, 22), "Pantone 403 C"),
    "oxford_stone_grey": Color("Oxford stone grey", "#D9D8D6", (217, 216, 214), (17, 13, 15, 0), "Pantone Cool Gray 1 C"),
    "oxford_shell_grey": Color("Oxford shell grey", "#F1EEE9", (241, 238, 233), (6, 6, 9, 0), "Pantone Warm Gray 1 C"),
    "oxford_off_white": Color("Oxford off white", "#F2F0F0", (242, 240, 240), (6, 6, 6, 0), "Pantone 663 C"),

    # Metallic (no exact hex provided; leaving None for hex)
    "oxford_gold": Color("Oxford gold", "#C9A14B", (201, 161, 75), None, "Pantone 10122C"),
    "oxford_silver": Color("Oxford silver", "#BFC0C0", (191, 192, 192), None, "Pantone 10103C"),
}

# Grouping convenience (primary, secondary, neutrals, metallic)
COLORS_BY_GROUP: Dict[str, List[str]] = {
    "primary": ["oxford_blue"],
    "secondary": [
        "oxford_mauve", "oxford_peach", "oxford_potters_pink", "oxford_dusk", "oxford_lilac",
        "oxford_sienna", "oxford_ccb_red", "oxford_plum", "oxford_coral", "oxford_lavender",
        "oxford_orange", "oxford_pink", "oxford_green", "oxford_ocean_grey", "oxford_yellow_ochre",
        "oxford_cool_grey", "oxford_sky_blue", "oxford_sage_green", "oxford_viridian", "oxford_royal_blue",
        "oxford_aqua", "oxford_vivid_green", "oxford_lime_green", "oxford_cerulean_blue", "oxford_yellow"
    ],
    "neutrals": [
        "oxford_charcoal", "oxford_ash_grey", "oxford_umber", "oxford_stone_grey",
        "oxford_shell_grey", "oxford_off_white"
    ],
    "metallic": ["oxford_gold", "oxford_silver"],
}

# -- Helper accessors -------------------------------------------------------
def _get_color_obj(name: str) -> Color:
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    if key not in OXFORD_COLORS:
        raise KeyError(f"Color '{name}' not found. Available: {', '.join(sorted(OXFORD_COLORS.keys()))}")
    return OXFORD_COLORS[key]

def hex(name: str) -> str:
    """Return hex string for a color name (e.g. '#002147')."""
    return _get_color_obj(name).hex

def rgb(name: str) -> Tuple[int, int, int]:
    """Return integer RGB tuple (0-255)."""
    return _get_color_obj(name).rgb

def cmyk(name: str) -> Optional[Tuple[int, int, int, int]]:
    """Return CMYK tuple if present (integers)."""
    return _get_color_obj(name).cmyk

def pantone(name: str) -> Optional[str]:
    """Return Pantone string if present."""
    return _get_color_obj(name).pantone

def as_rgb_norm(name: str) -> Tuple[float, float, float]:
    """Return RGB normalized to 0..1 (for matplotlib)."""
    return _get_color_obj(name).rgb_norm()

def get_names(group: Optional[str] = None) -> List[str]:
    """
    Return a list of colour keys.
    If group is given (primary|secondary|neutrals|metallic) returns that group.
    """
    if group is None:
        return sorted(list(OXFORD_COLORS.keys()))
    g = group.strip().lower()
    if g not in COLORS_BY_GROUP:
        raise KeyError(f"Group '{group}' not found. Available groups: {', '.join(COLORS_BY_GROUP.keys())}")
    return COLORS_BY_GROUP[g].copy()

# -- Matplotlib helpers ----------------------------------------------------
def mpl_palette(names: Optional[Iterable[str]] = None) -> List[str]:
    """
    Return a list of hex colour codes suitable for use with matplotlib/seaborn.
    If `names` is None, returns the primary + secondary palette in order.
    `names` may be an iterable of colour keys or friendly names.
    """
    if names is None:
        names = COLORS_BY_GROUP["primary"] + COLORS_BY_GROUP["secondary"]
    hexes = []
    for n in names:
        try:
            hexes.append(hex(n))
        except KeyError:
            # allow raw hex strings passed through
            s = str(n)
            if s.startswith("#") and (len(s) in (4, 7)):
                hexes.append(s)
            else:
                raise
    return hexes

def set_plt_colors(plt, names:Optional[Iterable[str]]=["oxford_blue", "oxford_pink", "oxford_green","oxford_yellow_ochre", "oxford_vivid_green"]):
    plt.rcParams['axes.prop_cycle'] = mpl_cycler(names)


def mpl_cycler(names: Optional[Iterable[str]] = None):
    """
    Return a matplotlib cycler object to set rcParams['axes.prop_cycle'].
    """
    try:
        from matplotlib import cycler
    except Exception as e:
        raise RuntimeError("matplotlib is required for mpl_cycler but import failed") from e

    pal = mpl_palette(names)
    return cycler(color=pal)


# module-level convenience: common palette
DEFAULT_PALETTE = mpl_palette()  # primary + secondary order


@contextmanager
def oxford_style(
    colors: Optional[Iterable[str]] = None
) -> ContextManager[None]:
    """
    Context manager for temporarily setting Oxford color styles in matplotlib.
    
    Args:
        colors: Iterable of color names to use for the color cycle.
                If None, uses the default Oxford palette.
    
    Example:
        with oxford_style(colors=["oxford_blue", "oxford_pink", "oxford_green"]):
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 4, 9])  # Uses Oxford colors
        # Outside the context, colors return to previous settings
    """
    # Store current rcParams
    old_rc = mpl.rcParams.copy()
    
    try:
        # Set the color cycle
        if colors is not None:
            plt.rc('axes', prop_cycle=mpl_cycler(colors))
        else:
            plt.rc('axes', prop_cycle=mpl_cycler())
            
        yield
        
    finally:
        # Restore original settings
        mpl.rcParams.clear()
        mpl.rcParams.update(old_rc)


# End of file


