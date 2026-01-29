import fiona
import laspy
import numpy as np
from shapely.geometry import shape, Polygon, Point
from shapely import STRtree

import pointcloudlasso
from pathlib import Path


def read_shapefile(file_path):
    """
    Reads a shapefile and returns a list of polygons.

    :param file_path: Path to the shapefile.
    :return: List of shapely Polygon objects.
    """
    polygons = []
    with fiona.open(file_path) as src:
        for feature in src:
            geom = shape(feature["geometry"])
            if isinstance(geom, Polygon):
                polygons.append(geom)
    return polygons


def read_las_file_as_np(file_path):
    """
    Reads a LAS file and returns a numpy array of points.
    """
    with laspy.open(file_path) as las_file:
        las = las_file.read()
        points = np.array(las.xyz)
    return points


def read_las_file_as_pt(file_path):
    points = []
    with laspy.open(file_path) as las_file:
        las = las_file.read()
        for x, y, _ in zip(las.x, las.y, las.z):
            points.append(Point(x, y))
    return points


def filter_points_in_polygons(points, polygons):
    """
    Filters points that are inside any of the given polygons.

    :param points: Numpy array of points (shape: Nx3).
    :param polygons: List of shapely Polygon objects.
    :return: Numpy array of points inside the polygons.
    """
    start_time = time()
    tree = STRtree(polygons)
    print(f"STRtree construction took {time() - start_time:.2f} seconds")
    # start_time = time()
    # s_pts = [Point(p) for p in points[:, :2]]
    # print(f"Point conversion took {time() - start_time:.2f} seconds")
    s_pts = points
    start_time = time()
    query_result = tree.query(s_pts, "within")
    print(f"STRtree query took {time() - start_time:.2f} seconds")
    start_time = time()
    result = []
    for i in range(len(polygons)):
        result.append([])
    for pt_idx, poly_idx in zip(*query_result):
        result[poly_idx].append(pt_idx)
    print(f"Result aggregation took {time() - start_time:.2f} seconds")
    return result


if __name__ == "__main__":
    from time import time

    data_dir = Path("/Users/dwastberg/repos/pointcloudlasso/benches/data/")

    data_set = "helsingborg_residential"

    data_dir = data_dir / data_set

    shapefile_path = data_dir / "footprints.shp"

    las_file_path = data_dir / "pointcloud.las"
    polygons = read_shapefile(shapefile_path)
    start_time = time()
    points = read_las_file_as_pt(las_file_path)
    print(f"Reading LAS as Points took {time() - start_time:.2f} seconds")
    time_start = time()
    shapely_result = filter_points_in_polygons(points, polygons)
    print(f"Shapely filtering took {time() - time_start:.2f} seconds")
    start_time = time()
    points = read_las_file_as_np(las_file_path)
    print(f"Reading LAS as Numpy array took {time() - start_time:.2f} seconds")
    time_start = time()
    pclasso_result = pointcloudlasso.pointcloudlasso(points, polygons)
    print(f"PointCloudLasso 3D filtering took {time() - time_start:.2f} seconds")

    points = read_las_file_as_np(las_file_path)
    time_start = time()
    pclasso_result_2d = pointcloudlasso.pointcloudlasso(points[:, :2], polygons)
    print(f"PointCloudLasso 2D filtering took {time() - time_start:.2f} seconds")
    pass
