"""
Type stubs for pointcloudlasso

This file provides type hints for IDEs and type checkers.
"""

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import Polygon
from typing import Union

__version__: str

def pointcloudlasso(
    points: NDArray[np.float32], polygons: list[Polygon]
) -> list[NDArray[np.intp]]:
    """
    Determine which points in a point cloud are inside given polygons.

    Parameters
    ----------
    points : NDArray[np.float32]
        Array of shape (N, 2) or (N, 3) containing point coordinates.
    polygons : list[Polygon]
        List of shapely Polygon objects to test against.

    Returns
    -------
    list[NDArray[np.intp]]
        A list of NumPy arrays of indices, one array per input polygon.
    """
    ...

def lasso_single(points: NDArray[np.float32], polygon: Polygon) -> NDArray[np.intp]:
    """
    Determine which points in a point cloud are inside a single polygon.

    Parameters
    ----------
    points : NDArray[np.float32]
        Array of shape (N, 2) or (N, 3) containing point coordinates.
    polygon : Polygon
        Single shapely Polygon object to test against.

    Returns
    -------
    NDArray[np.intp]
        Array of indices of points inside the polygon.
    """
    ...
