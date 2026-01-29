from dataclasses import dataclass
from typing import List, Dict, Mapping, Any, Optional
from . import datasets


@dataclass(frozen=True)
class TextureSystem:
    """
    Represents a soil texture classification system.

    Parameters
    ----------
    name : str
        The unique name of the system (e.g., 'USDA').
    polygons : Mapping[str, Any]
        A mapping of class names to polygon vertices.
    meta : Mapping[str, Any]
        Metadata about the system (description, citation, etc.).
    """
    name: str
    polygons: Mapping[str, Any]
    meta: Mapping[str, Any]


_SYSTEMS: Dict[str, TextureSystem] = {
    "USDA": TextureSystem(
        name="USDA",
        polygons=datasets.USDA_TEXTURE_CLASSES,
        meta={
            "description": "United States Department of Agriculture (USDA) Soil Texture Classification"
        },
    ),
    "HYPRES": TextureSystem(
        name="HYPRES",
        polygons=datasets.HYPRES_TEXTURE_CLASSES,
        meta={
            "description": "The HYdraulic PRoperties of European Soils (HYPRES) is a European framework for classifying soils based on their hydrologic properties"
        },
    ),
    # additional systems can be added here
}


def get_texture_system(system_name: str) -> TextureSystem:
    """
    Retrieve a TextureSystem by name.

    Parameters
    ----------
    system_name : str
        The name of the system to retrieve.

    Returns
    -------
    TextureSystem
        The requested texture system.

    Raises
    ------
    ValueError
        If the system name is not found.
    """
    try:
        return _SYSTEMS[system_name]
    except KeyError:
        raise ValueError(
            f"Unknown texture system {system_name!r}. Available: {list(_SYSTEMS)}"
        )


def list_texture_systems() -> Dict[str, str]:
    """
    List all available texture systems.

    Returns
    -------
    Dict[str, str]
        A dictionary mapping system names to their descriptions.
    """
    return {k: v.meta.get("description", "") for k, v in _SYSTEMS.items()}
