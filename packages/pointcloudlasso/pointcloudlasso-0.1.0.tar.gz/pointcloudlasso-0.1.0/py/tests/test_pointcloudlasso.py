"""
Tests for the pointcloudlasso Python bindings

This module tests the point-in-polygon functionality using pytest best practices.
"""

import numpy as np
import pytest
from shapely.geometry import Polygon

import pointcloudlasso


class TestPointCloudLasso:
    """Test suite for pointcloudlasso functionality."""

    @pytest.fixture
    def simple_points(self):
        """Fixture providing a simple set of test points."""
        return np.array(
            [
                [0.5, 0.5, 1.0],  # Inside polygon 1
                [1.5, 1.5, 2.0],  # Inside polygon 1
                [2.5, 2.5, 3.0],  # Inside polygon 2
                [3.5, 3.5, 4.0],  # Inside polygon 2
                [5.0, 5.0, 5.0],  # Outside all polygons
            ],
            dtype=np.float32,
        )

    @pytest.fixture
    def simple_polygons(self):
        """Fixture providing two non-overlapping square polygons."""
        polygon1 = Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)])
        polygon2 = Polygon([(2.0, 2.0), (4.0, 2.0), (4.0, 4.0), (2.0, 4.0)])
        return [polygon1, polygon2]

    @pytest.fixture
    def grid_points(self):
        """Fixture providing a grid of points for comprehensive testing."""
        x = np.linspace(0, 10, 11)
        y = np.linspace(0, 10, 11)
        xx, yy = np.meshgrid(x, y)
        z = np.zeros_like(xx)
        return np.stack([xx.ravel(), yy.ravel(), z.ravel()], axis=1).astype(np.float32)

    @pytest.fixture
    def large_pointcloud(self):
        """Fixture providing a large random point cloud for performance testing."""
        np.random.seed(42)  # Ensure reproducibility
        return np.random.rand(100_000, 3).astype(np.float32) * 100

    def test_basic_point_in_polygon_functionality(self, simple_points, simple_polygons):
        """Test that points are correctly assigned to their containing polygons."""
        result = pointcloudlasso.pointcloudlasso(simple_points, simple_polygons)

        assert len(result) == 2, "Should return results for 2 polygons"

        # Points 0 and 1 should be in polygon 1
        expected_polygon1 = np.array([0, 1])
        np.testing.assert_array_equal(
            np.sort(result[0]),
            expected_polygon1,
            err_msg="Points 0 and 1 should be in polygon 1",
        )

        # Points 2 and 3 should be in polygon 2
        expected_polygon2 = np.array([2, 3])
        np.testing.assert_array_equal(
            np.sort(result[1]),
            expected_polygon2,
            err_msg="Points 2 and 3 should be in polygon 2",
        )

    def test_polygon_with_hole(self):
        """Test that points inside polygon holes are correctly excluded."""
        points = np.array(
            [
                [1.5, 1.5, 0.0],  # Inside outer, outside hole
                [2.5, 2.5, 0.0],  # Inside hole (should be excluded)
                [3.5, 1.5, 0.0],  # Inside outer, outside hole
                [4.5, 4.5, 0.0],  # Outside all polygons
            ],
            dtype=np.float32,
        )

        # Create a square with a square hole
        exterior = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
        hole = [(2.0, 2.0), (3.0, 2.0), (3.0, 3.0), (2.0, 3.0)]
        polygon_with_hole = Polygon(shell=exterior, holes=[hole])

        result = pointcloudlasso.pointcloudlasso(points, [polygon_with_hole])

        assert len(result) == 1, "Should return result for 1 polygon"
        expected_indices = np.array([0, 2])
        np.testing.assert_array_equal(
            np.sort(result[0]),
            expected_indices,
            err_msg="Only points outside the hole should be included",
        )

    @pytest.mark.parametrize("num_points", [0, 1, 2, 5])
    def test_empty_results_with_various_point_counts(self, num_points):
        """Test behavior when no points are inside any polygon."""
        if num_points == 0:
            points = np.empty((0, 3), dtype=np.float32)
        else:
            # Points far from the polygon
            points = np.random.rand(num_points, 3).astype(np.float32) * 10 + 20

        polygon = Polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
        result = pointcloudlasso.pointcloudlasso(points, [polygon])

        assert len(result) == 1, "Should return result for 1 polygon"
        assert len(result[0]) == 0, "No points should be inside the polygon"

    def test_multiple_polygons_comprehensive(self, grid_points):
        """Test correct assignment with multiple polygons of different shapes."""
        polygons = [
            Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]),  # Square
            Polygon([(5.0, 5.0), (8.0, 5.0), (8.0, 7.0), (5.0, 7.0)]),  # Rectangle
            Polygon([(2.0, 8.0), (4.0, 8.0), (3.0, 10.0)]),  # Triangle
        ]

        result = pointcloudlasso.pointcloudlasso(grid_points, polygons)

        assert len(result) == len(
            polygons
        ), f"Should return results for {len(polygons)} polygons"

        # All polygons should contain some points from the grid
        for i, indices in enumerate(result):
            assert len(indices) > 0, f"Polygon {i} should contain at least one point"

            # Verify indices are unique within each polygon
            unique_indices = np.unique(indices)
            assert len(unique_indices) == len(
                indices
            ), f"Polygon {i} should not have duplicate indices"

            # Verify indices are within valid range
            assert np.all(
                indices >= 0
            ), f"All indices for polygon {i} should be non-negative"
            assert np.all(
                indices < len(grid_points)
            ), f"All indices for polygon {i} should be within bounds"

    def test_large_pointcloud_performance(self, large_pointcloud):
        """Test performance and correctness with a large point cloud."""
        polygons = [
            Polygon([(10.0, 10.0), (30.0, 10.0), (30.0, 30.0), (10.0, 30.0)]),
            Polygon([(50.0, 50.0), (70.0, 50.0), (70.0, 70.0), (50.0, 70.0)]),
        ]

        result = pointcloudlasso.pointcloudlasso(large_pointcloud, polygons)

        assert len(result) == 2, "Should return results for 2 polygons"

        for i, polygon_indices in enumerate(result):
            # Both polygons should capture some points (statistically very likely with 100k random points)
            assert len(polygon_indices) > 0, f"Polygon {i} should contain points"

            # Validate all indices
            assert np.all(
                polygon_indices >= 0
            ), f"All indices for polygon {i} should be non-negative"
            assert np.all(
                polygon_indices < len(large_pointcloud)
            ), f"All indices for polygon {i} should be within bounds"

            # Check for duplicates
            unique_indices = np.unique(polygon_indices)
            assert len(unique_indices) == len(
                polygon_indices
            ), f"Polygon {i} should not have duplicate indices"

    @pytest.mark.parametrize("polygon_count", [0, 1, 3, 10])
    def test_various_polygon_counts(self, simple_points, polygon_count):
        """Test behavior with different numbers of polygons."""
        if polygon_count == 0:
            polygons = []
        else:
            # Create simple square polygons at different positions
            polygons = []
            for i in range(polygon_count):
                offset = i * 2.0
                polygon = Polygon(
                    [
                        (offset, offset),
                        (offset + 1, offset),
                        (offset + 1, offset + 1),
                        (offset, offset + 1),
                    ]
                )
                polygons.append(polygon)

        result = pointcloudlasso.pointcloudlasso(simple_points, polygons)

        assert (
            len(result) == polygon_count
        ), f"Should return results for {polygon_count} polygons"

        if polygon_count > 0:
            # Verify each result is a valid numpy array
            for i, polygon_result in enumerate(result):
                assert isinstance(
                    polygon_result, np.ndarray
                ), f"Result {i} should be a numpy array"

    def test_input_validation_and_edge_cases(self):
        """Test edge cases and potential error conditions."""
        # Test with minimal valid input
        single_point = np.array([[1.0, 1.0, 1.0]], dtype=np.float32)
        small_polygon = Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)])

        result = pointcloudlasso.pointcloudlasso(single_point, [small_polygon])
        assert len(result) == 1, "Should handle single point correctly"
        assert len(result[0]) == 1, "Single point should be inside the polygon"

        # Test with empty polygon list
        result_empty = pointcloudlasso.pointcloudlasso(single_point, [])
        assert len(result_empty) == 0, "Empty polygon list should return empty result"

    @pytest.mark.parametrize("dtype", [np.float32, np.float64])
    def test_different_data_types(self, dtype):
        """Test that the function works with different numpy data types."""
        points = np.array([[0.5, 0.5, 1.0], [1.5, 1.5, 2.0]], dtype=dtype)
        polygon = Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)])

        result = pointcloudlasso.pointcloudlasso(points, [polygon])

        assert len(result) == 1, "Should return result for 1 polygon"
        assert len(result[0]) == 2, "Both points should be inside the polygon"
        np.testing.assert_array_equal(result[0], np.array([0, 1]))

    def test_boundary_conditions(self):
        """Test points exactly on polygon boundaries."""
        # Points on the boundary of a unit square
        boundary_points = np.array(
            [
                [0.0, 0.5, 0.0],  # Left edge
                [1.0, 0.5, 0.0],  # Right edge
                [0.5, 0.0, 0.0],  # Bottom edge
                [0.5, 1.0, 0.0],  # Top edge
                [0.0, 0.0, 0.0],  # Corner
            ],
            dtype=np.float32,
        )

        unit_square = Polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])

        result = pointcloudlasso.pointcloudlasso(boundary_points, [unit_square])

        assert len(result) == 1, "Should return result for 1 polygon"
        # The exact behavior for boundary points depends on the implementation
        # but the function should handle them gracefully without errors
        assert isinstance(result[0], np.ndarray), "Result should be a numpy array"
