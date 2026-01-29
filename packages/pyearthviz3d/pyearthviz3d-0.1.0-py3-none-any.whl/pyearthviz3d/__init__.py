"""
pyearthviz3d: 3D Globe Visualization Tools for Geospatial Data

pyearthviz3d provides 3D visualization capabilities on spherical earth using GeoVista and PyVista:
- 3D globe rendering
- Polyline/polygon visualization on sphere
- Rotating animations
- Time series animations on globe
- Interactive 3D views

Example:
    >>> from pyearthviz3d.geovista import map_single_frame
    >>>
    >>> # Visualize vector data on 3D globe
    >>> map_single_frame(
    ...     'data.geojson',
    ...     'globe.png',
    ...     title='Global Data'
    ... )
"""

__version__ = "0.1.0"
__author__ = "Chang Liao"
__email__ = "changliao.climate@gmail.com"
__url__ = "https://github.com/changliao1025/pyearthviz3d"

# Import main geovista functions for convenience
from .geovista import (
    map_single_frame,
    animate_polyline_file_on_sphere,
    animate_rotating_frames,
    animate_time_series_frames,
)

__all__ = [
    "map_single_frame",
    "animate_polyline_file_on_sphere",
    "animate_rotating_frames",
    "animate_time_series_frames",
]
