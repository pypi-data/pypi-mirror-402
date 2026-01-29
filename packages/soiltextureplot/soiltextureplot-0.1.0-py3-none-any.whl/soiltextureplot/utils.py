import numpy as np


def calculate_centroid(vertices: np.ndarray) -> np.ndarray:
    """
    Compute centroid of a 2D polygon given an (N, 2) array of vertices.
    Uses the standard shoelace formula (no np.cross).

    Parameters
    ----------
    vertices : np.ndarray
        Array of shape (N, 2) containing polygon vertices.

    Returns
    -------
    np.ndarray
        Array of shape (2,) containing the (x, y) centroid coordinates.
    """
    x = vertices[:, 0]
    y = vertices[:, 1]

    # Close the polygon
    x_next = np.roll(x, -1)
    y_next = np.roll(y, -1)

    cross = x * y_next - x_next * y
    area = cross.sum() / 2.0

    if np.isclose(area, 0.0):
        # Fallback: simple mean if area is ~0 (degenerate polygon)
        return np.array([x.mean(), y.mean()])

    cx = ((x + x_next) * cross).sum() / (6.0 * area)
    cy = ((y + y_next) * cross).sum() / (6.0 * area)

    return np.array([cx, cy])


def ternary_to_cartesian(
    clay: np.ndarray,
    sand: np.ndarray,
    silt: np.ndarray,
    ternary_sum: float = 100.0
) -> np.ndarray:
    """
    Convert ternary coordinates (clay, sand, silt) to 2D Cartesian (x, y).

    Uses an equilateral triangle with side length = ternary_sum.

    Parameters
    ----------
    clay : np.ndarray
        Clay percentages.
    sand : np.ndarray
        Sand percentages.
    silt : np.ndarray
        Silt percentages.
    ternary_sum : float, optional
        The sum of the ternary components (default 100.0).

    Returns
    -------
    np.ndarray
        Array of shape (N, 2) containing Cartesian (x, y) coordinates.
    """
    clay = np.asarray(clay, dtype=float)
    sand = np.asarray(sand, dtype=float)
    silt = np.asarray(silt, dtype=float)

    # Normalize to sum to ternary_sum to be safe
    total = clay + sand + silt
    total[total == 0] = ternary_sum
    clay = clay * ternary_sum / total
    sand = sand * ternary_sum / total
    silt = silt * ternary_sum / total

    # Place triangle with one vertex at (0, 0), base horizontal
    # Many ternary implementations use:
    # x = 0.5 * (2*sand + silt) / ternary_sum
    # y = (np.sqrt(3)/2) * silt / ternary_sum
    # but we’ll keep units ~percent and let plotting handle scaling.
    x = sand + 0.5 * silt
    y = (np.sqrt(3) / 2.0) * silt

    return np.stack([x, y], axis=-1)
