# pointcloudlasso

Fast point-in-polygon tests for large point clouds, optimized for geospatial data processing.

[![PyPI version](https://badge.fury.io/py/pointcloudlasso.svg)](https://badge.fury.io/py/pointcloudlasso)
[![Python versions](https://img.shields.io/pypi/pyversions/pointcloudlasso.svg)](https://pypi.org/project/pointcloudlasso/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A high-performance Python library with Rust core for determining which points in a point cloud fall within given
polygons. Designed for geospatial applications like LiDAR processing, building footprint extraction, and terrain
analysis.

## Features

- **50-100x faster** than pure Python approaches
- **Parallel processing** using all CPU cores automatically
- **Simple interface** with NumPy arrays and Shapely polygons
- **Works with 2D and 3D** point clouds (Z coordinate ignored for tests)

## Installation

```bash
pip install pointcloudlasso
```

Requires Python 3.10+, NumPy, and Shapely.

## Quick Start

```python
import numpy as np
from shapely.geometry import Polygon
import pointcloudlasso

# Create a point cloud (Nx2 or Nx3 array)
points = np.array([
    [0.5, 0.5],
    [1.5, 1.5],
    [5.5, 5.5],
], dtype=np.float32)

# Define a polygon
polygon = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])

# Find which points are inside
indices = pointcloudlasso.lasso_single(points, polygon)
print(indices)  # [0, 1]

# Get the actual points
points_inside = points[indices]
```

## Multiple Polygons

Process multiple polygons in a single call for optimal performance:

```python
import numpy as np
from shapely.geometry import Polygon
import pointcloudlasso

# Large point cloud
points = np.random.rand(100000, 3).astype(np.float32) * 100

# Multiple building footprints
polygons = [
    Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]),
    Polygon([(20, 20), (30, 20), (30, 30), (20, 30)]),
    Polygon([(50, 50), (60, 50), (60, 60), (50, 60)]),
]

# Find points in each polygon
results = pointcloudlasso.pointcloudlasso(points, polygons)

# results[i] contains indices of points in polygons[i]
for i, indices in enumerate(results):
    print(f"Polygon {i}: {len(indices)} points")
    points_in_polygon = points[indices]
```

## Polygons with Holes

Complex polygons with interior holes are fully supported:

```python
import numpy as np
from shapely.geometry import Polygon
import pointcloudlasso

points = np.array([
    [1.5, 1.5],  # Inside outer, outside hole
    [2.5, 2.5],  # Inside hole (excluded)
    [3.5, 1.5],  # Inside outer, outside hole
], dtype=np.float32)

# Square with a square hole
exterior = [(0, 0), (4, 0), (4, 4), (0, 4)]
hole = [(2, 2), (3, 2), (3, 3), (2, 3)]
polygon = Polygon(shell=exterior, holes=[hole])

result = pointcloudlasso.lasso_single(points, polygon)
print(result)  # [0, 2] - point at [2.5, 2.5] is excluded
```

## API Reference

### `pointcloudlasso(points, polygons)`

Find points within multiple polygons.

**Parameters:**

- `points`: NumPy array of shape (N, 2) or (N, 3), dtype float32
- `polygons`: List of Shapely Polygon objects

**Returns:**

- List of NumPy arrays containing point indices for each polygon

### `lasso_single(points, polygon)`

Convenience function for a single polygon.

**Parameters:**

- `points`: NumPy array of shape (N, 2) or (N, 3), dtype float32
- `polygon`: Single Shapely Polygon object

**Returns:**

- NumPy array of point indices inside the polygon

## How It Works

The library uses spatial tiling and parallel processing:

1. Points and polygons are organized into spatial tiles
2. Each tile is processed independently across CPU cores
3. KD-tree filtering quickly eliminates points outside bounding boxes
4. Precise geometric tests are performed on candidate points

## Development

Building from source requires Rust 1.70+ and maturin:

```bash
pip install maturin
cd py
maturin develop --release
pytest tests/
```

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Links

- [GitHub Repository](https://github.com/dwastberg/pointcloudlasso)
- [Issue Tracker](https://github.com/dwastberg/pointcloudlasso/issues)
- [Rust Library Docs](https://docs.rs/pointcloudlasso)
- [PyPI Package](https://pypi.org/project/pointcloudlasso/)

For version history, see [CHANGELOG.md](CHANGELOG.md).
