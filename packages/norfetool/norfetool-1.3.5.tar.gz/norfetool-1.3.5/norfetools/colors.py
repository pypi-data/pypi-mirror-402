# colors.py
# -*- coding: utf-8 -*-
import colorsys, numpy as np, matplotlib.pyplot as plt
from matplotlib.colors import to_rgb

from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from typing import Optional

ALL_CARDS = {
    'Deep Blue':    ['#313772', '#2c4ca0', '#326db6', '#478ecc', '#75b5dc', "#b2e0fd"], 
    'Deep Red':     ['#b7282e', '#c44438', '#d16d5b', '#dc917b', '#eabaa1', '#fee3ce'], 
    'Orange':       ['#f7842d', '#fa9b48', '#fcac65', '#ffc187', '#ffd7a8', '#ffebcc'],
    'Deep Green':   ['#376439', '#4d7e54', '#669877', '#81b095', '#a4cbb7', '#cfeadf'], 
    'Purple':       ['#704085', '#865a96', '#9d78ad', '#b291c2', '#c8b4d6', '#e7daf2'], 
    'Teal':         ['#00646e', '#008c8c', '#4db6ac', '#80cbc4', '#b2e1db', '#e0f2f1'], 
    'Yellow':       ['#ffa600', '#ffb30a', '#ffca28', '#ffd478', '#f8ecb8', '#fcfae4'], 
    'Grayscale':   ['#000000', '#333333', '#666666', '#999999', '#CCCCCC', '#FFFFFF'],  # black → white (6 stops)
    # 'Deep Purple': ['#832440', '#9b3f5c', '#b25f79', '#c87d98', '#dda1be', '#ebcce2'],
    # 'Blue':        ['#164da6', '#1976d2', '#2196f3', '#64b5f6', '#90caf9', '#e3f2fb'], 
    # 'Green':       ['#3c7a46', '#538c5e', '#74a680', '#97c4a4', '#badec7', '#dcf5e9'], 
    # 'Red':         ['#a63121', '#ba4e3d', '#cf705f', '#e09284', '#f2b7b1', '#ffe0e0'], 
}

# Also store as a 2D list (rows = families, cols = lightness levels from dark → light)
CLL = [ALL_CARDS[k] for k in ALL_CARDS.keys()]


def lightness(hx):
    r,g,b = to_rgb(hx)
    return colorsys.rgb_to_hls(r,g,b)[1]


def plot_palette_heatmap(cards_dict):
    by_light = {name: sorted(seq, key=lightness) for name, seq in cards_dict.items()}
    rep_hue = {}
    for name, seq in by_light.items():
        mid = len(seq)//2
        r,g,b = to_rgb(seq[mid])
        h,l,s = colorsys.rgb_to_hls(r,g,b)
        rep_hue[name] = h
    col_order = sorted(rep_hue, key=lambda k: rep_hue[k])
    cols = [by_light[k] for k in col_order]
    max_levels = max(len(c) for c in cols)
    ncols = len(cols)
    img = np.ones((max_levels, ncols, 3), dtype=float)
    for j, seq in enumerate(cols):
        for i, hx in enumerate(seq):
            img[i, j, :] = to_rgb(hx)
    plt.figure(figsize=(max(8, ncols*0.7), max(4, max_levels*0.6)))
    plt.imshow(img, aspect='auto', origin='lower')
    plt.xticks(range(ncols), col_order, rotation=45, ha='right')
    plt.yticks(range(max_levels), [f"L{i+1}" for i in range(max_levels)])
    plt.xlabel("Hue-sorted color families")
    plt.ylabel("Lightness levels (dark → light)")
    plt.tight_layout()
    plt.show()

# --- helpers ---------------------------------------------------------
def _deep_to_light(hex_seq):
    """Sort a hex list by lightness (HLS.l), from dark -> light."""
    return sorted(hex_seq, key=lightness)


def _light_to_deep(hex_seq):
    """Sort a hex list by lightness (HLS.l), from light -> dark."""
    return sorted(hex_seq, key=lightness, reverse=True)

# --- API 1: pick one palette by index --------------------------------
def get_cmap_by_index(
    idx: int, 
    reverse: bool = False, 
    name: Optional[str] = None, 
    discrete: Optional[int] = None
):
    """
    Select a color card from CLL by index and convert to a Matplotlib colormap.

    Parameters
    ----------
    idx : int
        Row index in CLL (0-based).
    reverse : bool, optional
        If True, reverse the lightness order (light->dark). Default False.
    name : str | None
        Optional name for the colormap.
    discrete : int | None
        If None, return a smooth LinearSegmentedColormap (256 levels).
        If int, return a ListedColormap with that many discrete bins.

    Returns
    -------
    cmap : Colormap
        Matplotlib colormap object.
    hex_list : list[str]
        The underlying hex colors in the order used.
    """
    if not (0 <= idx < len(CLL)):
        raise IndexError(f"idx out of range: 0..{len(CLL)-1}")

    hex_seq = _deep_to_light(CLL[idx][:])
    if reverse:
        hex_seq = list(reversed(hex_seq))

    if discrete is None:
        cmap = LinearSegmentedColormap.from_list(name or f"card_{idx}", hex_seq, N=256)
    else:
        cmap = ListedColormap(hex_seq, name=name or f"card_{idx}", N=discrete)

    return cmap, hex_seq

# --- API 2: build dark->light->dark between two palettes --------------
def make_dark_light_dark(
    id1: int, 
    id2: int, 
    name: Optional[str] = None, 
    drop_duplicate: bool = True, 
    discrete: Optional[int] = None
):
    """
    Build a dark->light->dark colormap by concatenating:
        card[id1] (dark->light) + card[id2] (light->dark)

    Parameters
    ----------
    id1, id2 : int
        Row indices in CLL.
    name : str | None
        Optional name for the colormap.
    drop_duplicate : bool
        If True, drop the peak light color once to avoid a flat plateau.
    discrete : int | None
        If None, return a smooth LinearSegmentedColormap (256 levels).
        If int, return a ListedColormap with that many discrete bins.

    Returns
    -------
    cmap : Colormap
        The concatenated colormap.
    hex_list : list[str]
        The concatenated hex sequence.
    """
    if not (0 <= id1 < len(CLL)) or not (0 <= id2 < len(CLL)):
        raise IndexError(f"id out of range: 0..{len(CLL)-1}")

    a = _deep_to_light(CLL[id1][:])              # dark -> light
    b = _light_to_deep(CLL[id2][:])              # light -> dark

    if drop_duplicate and b and a and b[0].lower() == a[-1].lower():
        b = b[1:]

    concat_hex = a + b

    if discrete is None:
        cmap = LinearSegmentedColormap.from_list(name or f"dld_{id1}_{id2}", concat_hex, N=256)
    else:
        cmap = ListedColormap(concat_hex, name=name or f"dld_{id1}_{id2}", N=discrete)

    return cmap, concat_hex

# --- quick test -------------------------------------------------------
def test_colormap_generators(idx_single: int = 0, id1: int = 0, id2: int = 1):
    """
    Visual check for both generators. Draw two horizontal colorbars.
    """
    cmap1, seq1 = get_cmap_by_index(idx_single)          # continuous
    cmap2, seq2 = make_dark_light_dark(id1, id2)         # continuous
    cmap3, seq3 = get_cmap_by_index(idx_single, discrete=6)  # discrete
    cmap4, seq4 = make_dark_light_dark(id1, id2, discrete=12) # discrete

    grad = np.linspace(0, 1, 256).reshape(1, -1)

    fig, axes = plt.subplots(4, 1, figsize=(6, 4.8))
    for ax, cmap, label in zip(
        axes,
        [cmap1, cmap2, cmap3, cmap4],
        ["single continuous", "dark-light-dark continuous", "single discrete", "dark-light-dark discrete"]
    ):
        ax.imshow(grad, aspect='auto', cmap=cmap)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.set_xlabel(label)

    plt.tight_layout()
    plt.show()

# --- keep the original demo if run directly ---------------------------
if __name__ == "__main__":
    # Existing heatmap of all palettes
    plot_palette_heatmap(ALL_CARDS)
    # New tests: pick the first card, and build a dark-light-dark using 0 & 1
    test_colormap_generators(idx_single=0, id1=0, id2=1)