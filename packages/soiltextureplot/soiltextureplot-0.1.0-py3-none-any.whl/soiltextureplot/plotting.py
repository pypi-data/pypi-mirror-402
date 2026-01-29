import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from typing import Optional, Union, List, Tuple
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.colors import Colormap
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from matplotlib import colormaps

from .systems import TextureSystem
from .utils import calculate_centroid


def plot_triangle_with_points(
    df: pd.DataFrame,
    system: TextureSystem,
    size_by: Optional[str] = None,
    size_min: Optional[float] = None,
    size_max: Optional[float] = None,
    show_labels: Optional[bool] = None,
    cmap: Optional[Union[str, List[str], Colormap]] = None,
    color_points: Optional[Union[str, List[str]]] = None,
) -> Tuple[Figure, Axes]:
    """
    Plot soil texture data on a ternary diagram.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'clay', 'sand', 'silt' columns.
    system : TextureSystem
        The soil texture classification system to use.
    size_by : str, optional
        Column name to use for sizing points.
    size_min : float, optional
        Minimum point size.
    size_max : float, optional
        Maximum point size.
    show_labels : bool, optional
        If True, show sample labels on points.
    cmap : str, list, or Colormap, optional
        Colormap for filling texture classes. Can be a matplotlib colormap name
        or a list of colors. Defaults to 'Set3_r'.
    color_points : str or list, optional
        Color for the scattered points.

    Returns
    -------
    fig : Figure
        The matplotlib Figure object.
    ax : Axes
        The matplotlib Axes object (ternary projection).
    """
    import mpltern  # imported here so core doesn’t hard‑depend for non‑plot use

    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(projection="ternary", ternary_sum=100.0)

    _plot_background_classes(ax, system, cmap=cmap)

    # coordinates in ternary order (clay, sand, silt)
    t = df["clay"].to_numpy()
    l = df["sand"].to_numpy()
    r = df["silt"].to_numpy()

    sizes = _compute_sizes(df, size_by, size_min, size_max)

    ax.scatter(
        t,
        l,
        r,
        c=color_points,
        alpha=0.7,
        edgecolors="none",
        s=sizes,
    )

    if show_labels and "sample_id" in df.columns:
        for (_, row), tt, ll, rr in zip(df.iterrows(), t, l, r):
            ax.text(
                tt,
                ll,
                rr,
                row["sample_id"],
                fontsize=7,
                ha="center",
                va="center",
                color="white",
            )

    ax.set_title(f"{system.name} Soil Texture Triangle", weight="bold", pad=20)
    fig.tight_layout()
    return fig, ax


def _plot_background_classes(
    ax: Axes,
    system: TextureSystem,
    cmap: Optional[Union[str, List[str], Colormap]] = None
) -> None:
    """
    Plots the texture class polygons in the background.

    Parameters
    ----------
    ax : Axes
        The ternary axes to plot on.
    system : TextureSystem
        The system containing polygons to plot.
    cmap : str, list, or Colormap, optional
        Colormap to use for filling polygons.
    """
    from itertools import cycle

    num_polygons = len(system.polygons)

    colors = None
    if isinstance(cmap, list):
        colors = cmap
    else:
        if cmap is None:
            cmap = "Set3_r"  # default
        try:
            colormap = colormaps.get_cmap(cmap)
            # Resample the colormap to have exactly the number of colors we need.
            # Then, get the list of colors by calling the resampled map.
            # This is a robust way that works for both continuous and discrete colormaps.
            resampled_cmap = colormap.resampled(num_polygons)
            colors = [resampled_cmap(i) for i in range(resampled_cmap.N)]
        except (ValueError, KeyError):
            print(
                f"Warning: Colormap '{cmap}' not found. Falling back to default 'Set3_r'."
            )
            colormap = colormaps.get_cmap("Set3_r")
            resampled_cmap = colormap.resampled(num_polygons)
            colors = [resampled_cmap(i) for i in range(resampled_cmap.N)]

    # Cycle through colors if not enough are provided for the polygons.
    # This is a safeguard, though resampled() should give the correct number.
    if len(colors) < num_polygons:
        color_cycle = cycle(colors)
    else:
        color_cycle = colors  # type: ignore

    for (name, vertices), color in zip(system.polygons.items(), color_cycle):
        tn0, tn1, tn2 = np.array(vertices).T  # clay, sand, silt
        patch = ax.fill(
            tn0,
            tn1,
            tn2,
            ec="k",
            fc=color,
            alpha=0.5,
        )
        centroid = calculate_centroid(patch[0].get_xy())

        label = name.capitalize()

        ax.text(
            centroid[0],
            centroid[1],
            label,
            ha="center",
            va="center",
            transform=ax.transData,
        )

    # ticks, grid, etc. (same as you already have)
    ax.taxis.set_major_locator(MultipleLocator(10.0))
    ax.laxis.set_major_locator(MultipleLocator(10.0))
    ax.raxis.set_major_locator(MultipleLocator(10.0))
    ax.taxis.set_minor_locator(AutoMinorLocator(2))
    ax.laxis.set_minor_locator(AutoMinorLocator(2))
    ax.raxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(which="both", linewidth=0.4, color="gray", alpha=0.6)

    # Add custom axis labels along edges

    # Sand (%) – bottom edge, centered, below triangle
    ax.text(
        -5,
        33,
        33,  # roughly mid bottom edge in (t,l,r) = (clay,sand,silt)
        "Sand [%]",
        ha="center",
        va="top",
        fontsize=12,
        rotation=0,
        transform=ax.transTernaryAxes,  # use ternary coordinate classification_system
    )

    # Clay (%) – left edge, centered, rotated up
    ax.text(
        40,
        40,
        -8,  # somewhere along left edge
        "Clay [%]",
        ha="center",
        va="center",
        fontsize=12,
        rotation=60,  # rotate along left edge
        transform=ax.transTernaryAxes,
    )

    # Silt (%) – right edge, centered, rotated down
    ax.text(
        40,
        -8,
        40,  # somewhere along right edge
        "Silt [%]",
        ha="center",
        va="center",
        fontsize=12,
        rotation=-60,  # rotate along right edge
        transform=ax.transTernaryAxes,
    )
    ax.taxis.set_ticks_position("tick2")
    ax.laxis.set_ticks_position("tick2")
    ax.raxis.set_ticks_position("tick2")


def _compute_sizes(
    df: pd.DataFrame,
    size_by: Optional[str],
    size_min: Optional[float],
    size_max: Optional[float]
) -> Union[float, np.ndarray]:
    """Helper to compute point sizes based on a column."""
    if size_min is None:
        size_min = 20.0  # default fallback
    if size_by is None or size_by not in df.columns:
        return size_min

    if size_max is None:
        size_max = 100.0  # default fallback

    vals = df[size_by].to_numpy().astype(float)
    valid = np.isfinite(vals)
    if not valid.any() or np.allclose(vals[valid], vals[valid][0]):
        return np.full_like(vals, (size_min + size_max) / 2.0)

    vmin = vals[valid].min()
    vmax = vals[valid].max()
    norm = (vals - vmin) / (vmax - vmin)
    return size_min + norm * (size_max - size_min)
