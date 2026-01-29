"""
Point Cloud Lasso - Fast point-in-polygon tests for point clouds

This package provides efficient spatial operations for determining which points
from a point cloud fall within given polygons. It uses spatial indexing and
parallel processing for optimal performance on large datasets.

The main algorithm uses a tiled spatial index to efficiently match points
to polygons, then performs parallel point-in-polygon tests within each tile.
"""

from . import _pointcloudlasso_ext
import numpy as np
from shapely.geometry import Polygon
from typing import Union

__version__ = "0.1.0"
__all__ = ["pointcloudlasso", "lasso_single", "__version__"]


def pointcloudlasso(
    points: np.ndarray, polygons: list[Polygon]
) -> list[np.ndarray]:
    """
    Determine which points in a point cloud are inside given polygons.

    This function performs fast point-in-polygon tests using spatial indexing
    and parallel processing. Points are tested against polygons using a tiled
    spatial partitioning strategy that reduces the number of comparisons needed.

    Parameters
    ----------
    points : np.ndarray
        Array of shape (N, 2) or (N, 3) containing point coordinates.
        - For 2D: each row is [x, y]
        - For 3D: each row is [x, y, z] (z-coordinate is ignored)
        The array will be automatically converted to C-contiguous float32 format
        if needed.

    polygons : list[Polygon]
        List of shapely Polygon objects to test against. Polygons can include
        holes (interior rings), which will be respected. Empty polygons are
        supported and will return empty results.

    Returns
    -------
    list[np.ndarray]
        A list of NumPy arrays of indices, one array per input polygon.
        - `result[i]` contains the indices of all points inside `polygons[i]`
        - Indices refer to rows in the input `points` array
        - Arrays are of dtype int64 or int32 (platform-dependent)
        - Empty arrays indicate no points were found inside that polygon

    Notes
    -----
    - Points exactly on polygon boundaries may or may not be included (depends
      on the underlying geometric library's boundary handling)
    - The function is parallelized and will use multiple CPU cores
    - For best performance, use C-contiguous arrays (default for most NumPy arrays)
    - For very large datasets (>10M points), consider processing in chunks

    Examples
    --------
    >>> import numpy as np
    >>> from shapely.geometry import Polygon
    >>> import pointcloudlasso
    >>>
    >>> # Create sample points
    >>> points = np.array([[0.5, 0.5], [1.5, 1.5], [2.5, 2.5]], dtype=np.float32)
    >>>
    >>> # Create two square polygons
    >>> poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    >>> poly2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])
    >>>
    >>> # Find points in each polygon
    >>> result = pointcloudlasso.pointcloudlasso(points, [poly1, poly2])
    >>> print(result[0])  # Points in poly1: [0]
    >>> print(result[1])  # Points in poly2: [2]

    Raises
    ------
    ValueError
        If `points` is not a 2D NumPy array with 2 or 3 columns
    ValueError
        If `polygons` contains non-Polygon objects
    ValueError
        If the array is not C-contiguous (will suggest using np.ascontiguousarray)
    """
    # Validate points array
    if not isinstance(points, np.ndarray):
        raise ValueError(
            f"Points must be a numpy array, got {type(points).__name__}"
        )

    if points.ndim != 2:
        raise ValueError(
            f"Points must be a 2D array with shape (N, 2) or (N, 3), "
            f"got {points.ndim}D array with shape {points.shape}"
        )

    if points.shape[1] not in (2, 3):
        raise ValueError(
            f"Points must have 2 or 3 columns (x, y) or (x, y, z), "
            f"got {points.shape[1]} columns"
        )

    # Convert to C-contiguous float32 for optimal performance
    points = np.ascontiguousarray(points, dtype=np.float32)

    # Validate polygons
    if not isinstance(polygons, list):
        raise ValueError(
            f"Polygons must be a list, got {type(polygons).__name__}. "
            f"For a single polygon, use lasso_single() or wrap in a list: [polygon]"
        )

    for i, p in enumerate(polygons):
        if not isinstance(p, Polygon):
            raise ValueError(
                f"All polygons must be shapely Polygon objects. "
                f"Element at index {i} is {type(p).__name__}"
            )

    return _pointcloudlasso_ext.pypointcloudlasso(points, polygons)


def lasso_single(points: np.ndarray, polygon: Polygon) -> np.ndarray:
    """
    Determine which points in a point cloud are inside a single polygon.

    This is a convenience function for the common case of testing against
    a single polygon. It returns the indices directly rather than wrapped
    in a list.

    Parameters
    ----------
    points : np.ndarray
        Array of shape (N, 2) or (N, 3) containing point coordinates.
    polygon : Polygon
        Single shapely Polygon object to test against.

    Returns
    -------
    np.ndarray
        Array of indices of points inside the polygon.

    Examples
    --------
    >>> import numpy as np
    >>> from shapely.geometry import Polygon
    >>> import pointcloudlasso
    >>>
    >>> points = np.array([[0.5, 0.5], [1.5, 1.5]], dtype=np.float32)
    >>> poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    >>> indices = pointcloudlasso.lasso_single(points, poly)
    >>> print(indices)  # [0]

    See Also
    --------
    pointcloudlasso : Test against multiple polygons
    """
    if not isinstance(polygon, Polygon):
        raise ValueError(
            f"Polygon must be a shapely Polygon object, got {type(polygon).__name__}"
        )

    result = pointcloudlasso(points, [polygon])
    return result[0]
