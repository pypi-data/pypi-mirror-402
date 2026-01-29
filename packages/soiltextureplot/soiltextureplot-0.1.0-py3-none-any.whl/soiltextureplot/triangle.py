import numpy as np
import pandas as pd

from dataclasses import dataclass, field
from pathlib import Path as PathLibPath
from typing import Optional, Union, TYPE_CHECKING
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from .systems import get_texture_system, TextureSystem
from .classifier import PolygonClassifier
from . import plotting

if TYPE_CHECKING:
    # Avoid circular import at runtime by only importing for type checking if needed
    pass


@dataclass
class SoilTextureTriangle:
    """
    Main interface for loading soil data, classifying it, and plotting it.

    Parameters
    ----------
    system_name : str, optional
        Name of the texture classification system. Defaults to 'USDA'.
    df : pd.DataFrame, optional
        Initial DataFrame. Can be set later via load functions.
    """
    system_name: str = "USDA"
    df: Optional[pd.DataFrame] = field(default=None, repr=False)

    def __post_init__(self):
        self.system: TextureSystem = get_texture_system(self.system_name)
        self._classifier = PolygonClassifier.from_system(self.system)

    # data loading
    def load_csv(
        self,
        path: Union[str, PathLibPath],
        sand_col: str = "sand",
        silt_col: str = "silt",
        clay_col: str = "clay",
    ) -> "SoilTextureTriangle":
        """
        Load data from a CSV file.

        Parameters
        ----------
        path : str or Path
            Path to the CSV file.
        sand_col : str
            Name of the column containing sand percentages.
        silt_col : str
            Name of the column containing silt percentages.
        clay_col : str
            Name of the column containing clay percentages.

        Returns
        -------
        SoilTextureTriangle
            Self for chaining.
        """
        df = pd.read_csv(path)
        return self.load_dataframe(df, sand_col, silt_col, clay_col)

    def load_dataframe(
        self,
        df: pd.DataFrame,
        sand_col: str = "sand",
        silt_col: str = "silt",
        clay_col: str = "clay",
    ) -> "SoilTextureTriangle":
        """
        Load data from an existing DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame containing soil data.
        sand_col : str
            Name of the column containing sand percentages.
        silt_col : str
            Name of the column containing silt percentages.
        clay_col : str
            Name of the column containing clay percentages.

        Returns
        -------
        SoilTextureTriangle
            Self for chaining.
        """
        # normalize column names internally
        self.df = df.rename(
            columns={sand_col: "sand", silt_col: "silt", clay_col: "clay"}
        )
        return self

    # classification
    def classify(self) -> pd.DataFrame:
        """
        Classify loaded data into texture classes.

        Adds a 'texture_class' column to the internal DataFrame.

        Returns
        -------
        pd.DataFrame
            The DataFrame with the added 'texture_class' column.

        Raises
        ------
        ValueError
            If no data has been loaded.
        """
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv or load_dataframe first.")

        clay = self.df["clay"].to_numpy()
        sand = self.df["sand"].to_numpy()
        silt = self.df["silt"].to_numpy()

        classes = self._classifier.classify_points(clay, sand, silt)
        self.df["texture_class"] = classes
        return self.df

    # plotting
    def plot(
        self,
        size_by: Optional[str] = None,
        size_min: float = 40,
        size_max: float = 160,
        show_labels: bool = True,
        cmap: Optional[str] = None,
        color_points: Optional[str] = "black",
    ) -> tuple[Figure, Axes]:
        """
        Plot current data on the soil texture triangle using mpltern.

        Parameters
        ----------
        size_by : str, optional
            Column name for sizing points.
        size_min : float, optional
            Min point size.
        size_max : float, optional
            Max point size.
        show_labels : bool, optional
            Show labels on points.
        cmap : str, optional
            Colormap name for background polygons.
        color_points : str, optional
            Color for sample points.

        Returns
        -------
        fig, ax
            Matplotlib Figure and Axes.

        Raises
        ------
        ValueError
            If no data is loaded.
        """
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv or load_dataframe first.")

        return plotting.plot_triangle_with_points(
            df=self.df,
            system=self.system,
            size_by=size_by,
            size_min=size_min,
            size_max=size_max,
            show_labels=show_labels,
            cmap=cmap,
            color_points=color_points,
        )
