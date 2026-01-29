"""
Soil Texture Plotting Package
=============================

A Python package for soil texture classification and plotting on ternary diagrams.

Modules
-------
classifier
    Logic for classifying soil samples into texture classes.
datasets
    Loading sample datasets.
plotting
    Functions for creating ternary plots.
systems
    Definitions of standard soil texture classification systems (USDA, HYPRES, etc.).
triangle
    Core triangle geometry utilities.
utils
    General utility functions.
"""

from .classifier import PolygonClassifier
from .systems import TextureSystem, get_texture_system
from .plotting import plot_triangle_with_points

__all__ = [
    "PolygonClassifier",
    "TextureSystem",
    "get_texture_system",
    "plot_triangle_with_points",
]
