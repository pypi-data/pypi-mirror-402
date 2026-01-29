//! Python bindings for the pointcloudlasso library.
//!
//! This module provides PyO3 bindings that expose the fast Rust-based
//! point-in-polygon operations to Python. It handles conversion between
//! Python types (NumPy arrays, Shapely polygons) and Rust types.

use geo::{Coord, LineString};
use numpy::{PyReadonlyArray2, ToPyArray};
use pointcloudlasso::{pointcloudlasso, FloatType};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList, PyTuple};
use std::slice;

/// Converts a Python tuple of coordinate tuples to a geo::LineString.
///
/// Expects a tuple of (x, y) tuples, e.g., ((0.0, 0.0), (1.0, 1.0), ...)
fn py_coords_list_to_geo_linestring(
    _py: Python<'_>,
    coords_list: &Bound<'_, PyTuple>,
) -> PyResult<LineString<FloatType>> {
    let mut points: Vec<Coord<FloatType>> = Vec::with_capacity(coords_list.len());
    for c in coords_list.iter() {
        let coord_tuple = c.downcast::<PyTuple>()?;

        let x: FloatType = coord_tuple.get_item(0)?.extract()?;
        let y: FloatType = coord_tuple.get_item(1)?.extract()?;
        points.push(Coord { x, y });
    }

    Ok(LineString(points))
}

/// Converts a Python object with `__geo_interface__` to a geo::Polygon.
///
/// This function supports any Python object that implements the `__geo_interface__`
/// protocol (e.g., Shapely polygons). It extracts the exterior ring and any holes.
fn py_poly_to_geo_poly(
    py: Python<'_>,
    py_poly: &Bound<'_, PyAny>,
) -> PyResult<geo::Polygon<FloatType>> {
    let geo_interface_dict = py_poly.getattr("__geo_interface__")?;
    let geo_dict = geo_interface_dict.downcast::<PyDict>()?;
    let geom_type = geo_dict
        .get_item("type")?
        .ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyKeyError, _>("'type' missing in __geo_interface__")
        })?
        .extract::<String>()?;
    if geom_type != "Polygon" {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
            "Expected geometry type 'Polygon' from __geo_interface__, got '{}'",
            geom_type
        )));
    }

    let coordinates_obj = geo_dict.get_item("coordinates")?.ok_or_else(|| {
        PyErr::new::<pyo3::exceptions::PyKeyError, _>("'coordinates' missing in __geo_interface__")
    })?;
    let coordinates_pylist = coordinates_obj.downcast::<PyTuple>()?;
    if coordinates_pylist.is_empty() {
        return Ok(geo::Polygon::new(LineString::new(Vec::new()), Vec::new()));
    } // Should be a list of rings

    let py_exterior = coordinates_pylist.get_item(0)?;
    let exterior_coords = py_exterior.downcast::<PyTuple>()?;
    let exterior_line_string = py_coords_list_to_geo_linestring(py, exterior_coords)?;
    let holes: Vec<LineString<FloatType>> = coordinates_pylist
        .iter()
        .skip(1)
        .map(|hole| {
            let hole_list = hole.downcast::<PyTuple>()?;
            py_coords_list_to_geo_linestring(py, hole_list)
        })
        .collect::<PyResult<Vec<_>>>()?;
    Ok(geo::Polygon::new(exterior_line_string, holes))
}

/// Converts a NumPy array to a zero-copy slice of fixed-size arrays.
///
/// This function performs an unsafe transmutation to avoid copying data.
/// It validates that the array is C-contiguous and has the expected shape.
///
/// # Type Parameters
/// * `N` - The number of dimensions per point (2 or 3)
///
/// # Safety
/// This function uses unsafe code to reinterpret the memory layout. It is safe
/// because we verify:
/// - The array is C-contiguous (guaranteed memory layout)
/// - The shape matches N columns exactly
/// - The total size is a multiple of N
fn np_to_slice<'a, const N: usize>(
    np_array: &'a PyReadonlyArray2<f32>,
) -> PyResult<&'a [[f32; N]]> {
    let array_view = np_array.as_array();

    // Validate array dimensions
    if array_view.ndim() != 2 || array_view.shape()[1] != N {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
            "Input array must be 2-dimensional with shape N x {}. Got shape {:?}",
            N,
            array_view.shape()
        )));
    }

    // Ensure array is C-contiguous for zero-copy access
    let flat_slice = match array_view.as_slice() {
        Some(s) => s,
        None => {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "NumPy array must be C-contiguous. Try using np.ascontiguousarray(points) before calling this function.",
            ));
        }
    };

    // Zero-copy transmutation: reinterpret flat f32 slice as [[f32; N]]
    // SAFETY: We've verified the array is C-contiguous with N columns,
    // so the memory layout matches [[f32; N]].
    let num_points = array_view.shape()[0];
    unsafe {
        assert!(flat_slice.len() % N == 0);
        assert!(flat_slice.len() / N == num_points);
        Ok(slice::from_raw_parts(
            flat_slice.as_ptr() as *const [f32; N],
            num_points,
        ))
    }
}

/// Python function to perform point-in-polygon tests on a point cloud.
///
/// # Arguments
/// * `np_array` - NumPy array of shape (N, 2) or (N, 3) containing point coordinates
/// * `shapely_polygons` - List of Shapely Polygon objects
///
/// # Returns
/// A list of NumPy arrays, where each array contains the indices of points
/// that fall within the corresponding polygon.
#[pyfunction]
fn pypointcloudlasso(
    py: Python<'_>,
    np_array: PyReadonlyArray2<f32>,
    shapely_polygons: &Bound<'_, PyList>,
) -> PyResult<Py<PyList>> {
    // Convert Shapely polygons to geo::Polygon
    let geo_polygons = shapely_polygons
        .iter()
        .enumerate()
        .map(|(i, poly)| {
            py_poly_to_geo_poly(py, &poly).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "Failed to convert polygon at index {}: {}",
                    i, e
                ))
            })
        })
        .collect::<PyResult<Vec<_>>>()?;

    let array_view = np_array.as_array();
    let num_dims = array_view.shape()[1];

    // Dispatch to 2D or 3D version based on array shape
    let pc_indices: Vec<Vec<usize>> = match num_dims {
        3 => {
            let points_slice = np_to_slice::<3>(&np_array)?;
            pointcloudlasso(points_slice, &geo_polygons).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Point cloud lasso operation failed: {}",
                    e
                ))
            })?
        }
        2 => {
            let points_slice = np_to_slice::<2>(&np_array)?;
            pointcloudlasso(points_slice, &geo_polygons).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Point cloud lasso operation failed: {}",
                    e
                ))
            })?
        }
        _ => {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Input array must have 2 or 3 columns (got {}). Shape: {:?}",
                num_dims,
                array_view.shape()
            )));
        }
    };

    // Convert results to Python list of NumPy arrays
    let py_list = PyList::empty(py);
    for idx_vec in pc_indices {
        let np_indices_array = idx_vec.to_pyarray(py);
        py_list.append(np_indices_array)?;
    }

    Ok(py_list.into())
}

#[pymodule]
fn _pointcloudlasso_ext(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pypointcloudlasso, m)?)?;
    Ok(())
}
