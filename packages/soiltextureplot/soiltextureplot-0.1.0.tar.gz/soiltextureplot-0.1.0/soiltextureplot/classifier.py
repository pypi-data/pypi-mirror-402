from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from matplotlib.path import Path

from .systems import TextureSystem
from .utils import ternary_to_cartesian


@dataclass
class PolygonClassifier:
    """
    Classifies points into soil texture classes using polygon inclusion.

    Parameters
    ----------
    system : TextureSystem
        The texture system definition containing polygon vertices.
    _paths : Dict[str, Path]
        Precomputed matplotlib Paths for point testing.
    _class_order : List[str]
        Ordered list of class names for consistency.
    """
    system: TextureSystem
    _paths: Dict[str, Path]
    _class_order: List[str]

    @classmethod
    def from_system(cls, system: TextureSystem) -> "PolygonClassifier":
        """
        Create a classifier from a TextureSystem.

        Parameters
        ----------
        system : TextureSystem
            The texture classification system to use.

        Returns
        -------
        PolygonClassifier
            Initialized classifier instance.
        """
        paths: Dict[str, Path] = {}

        for name, vertices in system.polygons.items():
            verts = np.array(vertices, dtype=float)  # shape (N, 3) (clay, sand, silt)
            clay, sand, silt = verts.T
            xy = ternary_to_cartesian(clay, sand, silt)
            # Ensure polygon is closed
            if not np.allclose(xy[0], xy[-1]):
                xy = np.vstack([xy, xy[0]])

            paths[name] = Path(xy)

        class_order = list(system.polygons.keys())
        return cls(system=system, _paths=paths, _class_order=class_order)

    def classify_points(
        self,
        clay: np.ndarray,
        sand: np.ndarray,
        silt: np.ndarray
    ) -> np.ndarray:
        """
        Classify many points at once.

        Parameters
        ----------
        clay : np.ndarray
            Array of clay percentages.
        sand : np.ndarray
            Array of sand percentages.
        silt : np.ndarray
            Array of silt percentages.

        Returns
        -------
        np.ndarray
            Array of class names (dtype=object). Returns 'Unknown' if no
            polygon contains the point.
        """
        xy = ternary_to_cartesian(clay, sand, silt)
        n = xy.shape[0]
        result = np.full(n, "Unknown", dtype=object)

        # Vectorized point-in-polygon: test all points against each Path
        for class_name in self._class_order:
            path = self._paths[class_name]
            inside = path.contains_points(xy)
            # Only overwrite where still Unknown
            mask = inside & (result == "Unknown")
            result[mask] = class_name

        return result
