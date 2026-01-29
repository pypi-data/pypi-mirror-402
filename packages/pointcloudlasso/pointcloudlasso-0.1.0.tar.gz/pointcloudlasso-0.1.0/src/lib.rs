mod pip;
mod search_tree;
mod tiling;
mod utils;

use dashmap::DashMap;
use rayon::prelude::*;
use rstar::AABB;
use std::time::Duration;

// Re-export puffin profiling macros when feature is enabled
#[cfg(feature = "profiling")]
pub use puffin::{profile_function, profile_scope};

// No-op macros when profiling is disabled
#[cfg(not(feature = "profiling"))]
#[macro_export]
macro_rules! profile_function {
    () => {};
}

#[cfg(not(feature = "profiling"))]
#[macro_export]
macro_rules! profile_scope {
    ($name:expr) => {};
}

/// Initialize profiling (call at program start when profiling is enabled)
#[cfg(feature = "profiling")]
pub fn init_profiling() {
    puffin::set_scopes_on(true);
}

#[cfg(not(feature = "profiling"))]
pub fn init_profiling() {}

pub type FloatType = f32;

/// Timing statistics for profiling
#[derive(Debug, Clone, Default)]
pub struct TimingStats {
    pub polygon_tiling: Duration,
    pub pointcloud_tiling: Duration,
    pub parallel_pip: Duration,
    pub aggregation: Duration,
    pub total: Duration,
}

impl TimingStats {
    pub fn print(&self) {
        println!("\n=== Detailed Algorithm Profiling ===");
        println!("{:<30} {:>15}", "Operation", "Duration");
        println!("{:-<30} {:->15}", "", "");
        println!(
            "{:<30} {:>15.3} ms",
            "Polygon tiling",
            self.polygon_tiling.as_secs_f64() * 1000.0
        );
        println!(
            "{:<30} {:>15.3} ms",
            "Pointcloud tiling",
            self.pointcloud_tiling.as_secs_f64() * 1000.0
        );
        println!(
            "{:<30} {:>15.3} ms",
            "Parallel PIP computation",
            self.parallel_pip.as_secs_f64() * 1000.0
        );
        println!(
            "{:<30} {:>15.3} ms",
            "Result aggregation",
            self.aggregation.as_secs_f64() * 1000.0
        );
        println!("{:-<30} {:->15}", "", "");
        println!(
            "{:<30} {:>15.3} ms",
            "Total algorithm time",
            self.total.as_secs_f64() * 1000.0
        );
        println!();
    }
}

thread_local! {
    static TIMING_STATS: std::cell::RefCell<Option<TimingStats>> = std::cell::RefCell::new(None);
}

/// Enable detailed timing collection (call before running algorithm)
pub fn enable_timing() {
    TIMING_STATS.with(|stats| {
        *stats.borrow_mut() = Some(TimingStats::default());
    });
}

/// Retrieve and clear collected timing statistics
pub fn get_timing_stats() -> Option<TimingStats> {
    TIMING_STATS.with(|stats| stats.borrow_mut().take())
}

/// Errors that can occur during point cloud lasso operations
#[derive(Debug, Clone, PartialEq)]
pub enum LassoError {
    /// Mismatch between the number of polygon tiles and point cloud tiles
    TileMismatch {
        /// Number of polygon tiles
        polygon_tiles: usize,
        /// Number of point cloud tiles
        point_tiles: usize,
    },
    /// Input data is empty or invalid
    EmptyInput,
    /// A polygon at the specified index is invalid
    InvalidPolygon {
        /// Index of the invalid polygon
        index: usize,
    },
}

impl std::fmt::Display for LassoError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LassoError::TileMismatch {
                polygon_tiles,
                point_tiles,
            } => write!(
                f,
                "Tile count mismatch: {} polygon tiles vs {} point tiles",
                polygon_tiles, point_tiles
            ),
            LassoError::EmptyInput => write!(f, "Empty input data provided"),
            LassoError::InvalidPolygon { index } => {
                write!(f, "Invalid polygon at index {}", index)
            }
        }
    }
}

impl std::error::Error for LassoError {}

/// Core generic implementation of point-in-polygon lasso
fn pointcloudlasso_impl<P: Point2DLike + Sync>(
    pointcloud: &[P],
    polygons: &[geo::Polygon<FloatType>],
) -> Result<Vec<Vec<usize>>, LassoError> {
    profile_function!();
    let total_start = std::time::Instant::now();

    // ✅ Early validation - handle empty inputs gracefully
    // Empty pointcloud: return empty result for each polygon
    if pointcloud.is_empty() {
        return Ok(vec![vec![]; polygons.len()]);
    }

    // Empty polygons: return empty results list
    if polygons.is_empty() {
        return Ok(vec![]);
    }

    // --- Step 1: Group polygons by tiles ---
    let t1 = std::time::Instant::now();
    let (grouped_polygons, group_bboxes, polygon_tile_indices) = {
        profile_scope!("polygon_tiling");
        let grouped_polygons = tiling::polygon_tiler::group_polygons_by_tile(polygons, 0, 0);
        let group_bboxes: Vec<AABB<[FloatType; 2]>> =
            grouped_polygons.iter().map(|(_, bbox)| *bbox).collect();
        let polygon_tile_indices: Vec<Vec<usize>> = grouped_polygons
            .iter()
            .map(|(indices, _)| indices.clone())
            .collect();
        (grouped_polygons, group_bboxes, polygon_tile_indices)
    };
    let polygon_tiling_time = t1.elapsed();

    // --- Step 2: Assign points to tiles ---
    let t2 = std::time::Instant::now();
    let pointcloud_tiles = {
        profile_scope!("pointcloud_tiling");
        tiling::pointcloud_to_tiles::pointcloud_to_tiles(pointcloud, &group_bboxes)
    };
    let pointcloud_tiling_time = t2.elapsed();

    if polygon_tile_indices.len() != pointcloud_tiles.len() {
        return Err(LassoError::TileMismatch {
            polygon_tiles: polygon_tile_indices.len(),
            point_tiles: pointcloud_tiles.len(),
        });
    }

    // --- Step 3: Parallel point-in-polygon computation ---
    let t3 = std::time::Instant::now();
    let result_map = {
        profile_scope!("parallel_pip");
        let result_map: DashMap<usize, Vec<usize>> = DashMap::with_capacity(polygons.len());

        polygon_tile_indices
            .par_iter()
            .zip(pointcloud_tiles.par_iter())
            .for_each(|(poly_indices, pc_indices)| {
                // Gather points for this tile
                let tile_points: Vec<[FloatType; 2]> = pc_indices
                    .iter()
                    .map(|&i| [pointcloud[i].x(), pointcloud[i].y()])
                    .collect();

                // Polygon references for this tile
                let tile_polygons: Vec<&geo::Polygon<FloatType>> =
                    poly_indices.iter().map(|&i| &polygons[i]).collect();

                // Compute points-in-polygons
                let points_in_polygons = pip::points_in_polygons(&tile_points, &tile_polygons);

                // Merge results into shared concurrent map
                for (i, point_indices) in points_in_polygons.iter().enumerate() {
                    let orig_poly_idx = poly_indices[i];
                    for &p_idx in point_indices {
                        let orig_pc_idx = pc_indices[p_idx];
                        result_map
                            .entry(orig_poly_idx)
                            .or_default()
                            .push(orig_pc_idx);
                    }
                }
            });
        result_map
    };
    let parallel_pip_time = t3.elapsed();

    // --- Step 4: Aggregate results ---
    let t4 = std::time::Instant::now();
    let result = {
        profile_scope!("aggregation");
        let mut result = vec![Vec::new(); polygons.len()];
        for (key, value) in result_map.into_iter() {
            result[key] = value;
        }
        result
    };
    let aggregation_time = t4.elapsed();

    let total_time = total_start.elapsed();

    // Store timing stats if enabled
    TIMING_STATS.with(|stats| {
        if let Some(ref mut timing) = *stats.borrow_mut() {
            timing.polygon_tiling = polygon_tiling_time;
            timing.pointcloud_tiling = pointcloud_tiling_time;
            timing.parallel_pip = parallel_pip_time;
            timing.aggregation = aggregation_time;
            timing.total = total_time;
        }
    });

    Ok(result)
}

/// Trait for types that can be used as point cloud input.
pub trait Point2DLike {
    fn x(&self) -> FloatType;
    fn y(&self) -> FloatType;
    fn real_dim(&self) -> usize;
}

impl Point2DLike for [FloatType; 2] {
    fn x(&self) -> FloatType {
        self[0]
    }
    fn y(&self) -> FloatType {
        self[1]
    }
    fn real_dim(&self) -> usize {
        2
    }
}

impl Point2DLike for [FloatType; 3] {
    #[inline]
    fn x(&self) -> FloatType {
        self[0]
    }
    #[inline]
    fn y(&self) -> FloatType {
        self[1]
    }
    #[inline]
    fn real_dim(&self) -> usize {
        3
    }
    // Z coordinate is ignored
}

/// Trait for types that can be used as point cloud input
pub trait PointCloudInput {
    fn pc_lasso(&self, polygons: &[geo::Polygon<FloatType>])
        -> Result<Vec<Vec<usize>>, LassoError>;
}

// ✅ Blanket implementation to replace the previous repetitive impls
impl<P: Point2DLike + Sync> PointCloudInput for &[P] {
    fn pc_lasso(
        &self,
        polygons: &[geo::Polygon<FloatType>],
    ) -> Result<Vec<Vec<usize>>, LassoError> {
        pointcloudlasso_impl(self, polygons)
    }
}

impl<P: Point2DLike + Sync> PointCloudInput for &Vec<P> {
    fn pc_lasso(
        &self,
        polygons: &[geo::Polygon<FloatType>],
    ) -> Result<Vec<Vec<usize>>, LassoError> {
        pointcloudlasso_impl(self.as_slice(), polygons)
    }
}

/// Performs point-in-polygon tests on a point cloud against multiple polygons.
///
/// This is the main entry point for the library. It accepts any type that implements
/// `PointCloudInput` (2D or 3D point arrays/slices) and returns the indices of points
/// that fall within each polygon.
///
/// # Algorithm
/// The function uses a spatial tiling strategy:
/// 1. Polygons are grouped into spatial tiles based on their bounding boxes
/// 2. Points are partitioned into the same tiles
/// 3. Within each tile, parallel point-in-polygon tests are performed
/// 4. Results are aggregated back to the original polygon indices
///
/// # Errors
///
/// Returns `Err(LassoError)` if:
/// - There's a tile mismatch during processing
/// - Input data is empty or invalid
/// - A polygon is invalid
pub fn pointcloudlasso<T: PointCloudInput>(
    p: T,
    polygons: &[geo::Polygon<FloatType>],
) -> Result<Vec<Vec<usize>>, LassoError> {
    p.pc_lasso(polygons)
}

#[cfg(test)]
mod tests {
    use super::*;
    use geo::{LineString, Polygon};
    use pretty_assertions::assert_eq;

    #[test]
    fn test_pointcloudlasso_2d() {
        let pointcloud = vec![[0.5, 0.5], [1.5, 1.5], [5.5, 5.5], [6.5, 6.5], [3.0, 9.0]];

        let polygons = vec![
            Polygon::new(
                LineString::from(vec![
                    (0.0, 0.0),
                    (2.0, 0.0),
                    (2.0, 2.0),
                    (0.0, 2.0),
                    (0.0, 0.0),
                ]),
                vec![],
            ),
            Polygon::new(
                LineString::from(vec![
                    (5.0, 5.0),
                    (8.0, 5.0),
                    (8.0, 7.0),
                    (5.0, 7.0),
                    (5.0, 5.0),
                ]),
                vec![],
            ),
            Polygon::new(
                LineString::from(vec![(2.0, 8.0), (4.0, 8.0), (3.0, 10.0), (2.0, 8.0)]),
                vec![],
            ),
        ];
        let polygon_count = polygons.len();

        let result = pointcloudlasso(&pointcloud, &polygons).expect("pointcloudlasso failed");
        assert_eq!(result.len(), polygon_count);

        let mut result_0 = result[0].clone();
        let mut result_1 = result[1].clone();
        let mut result_2 = result[2].clone();
        result_0.sort_unstable();
        result_1.sort_unstable();
        result_2.sort_unstable();

        assert_eq!(result_0, vec![0, 1]);
        assert_eq!(result_1, vec![2, 3]);
        assert_eq!(result_2, vec![4]);
    }

    #[test]
    fn test_pointcloud_3d() {
        let pointcloud = vec![
            [0.5, 0.5, 0.0],
            [1.5, 1.5, 0.0],
            [5.5, 5.5, 0.0],
            [6.5, 6.5, 0.0],
            [3.0, 9.0, 0.0],
        ];

        let polygons = vec![
            Polygon::new(
                LineString::from(vec![
                    (0.0, 0.0),
                    (2.0, 0.0),
                    (2.0, 2.0),
                    (0.0, 2.0),
                    (0.0, 0.0),
                ]),
                vec![],
            ),
            Polygon::new(
                LineString::from(vec![
                    (5.0, 5.0),
                    (8.0, 5.0),
                    (8.0, 7.0),
                    (5.0, 7.0),
                    (5.0, 5.0),
                ]),
                vec![],
            ),
            Polygon::new(
                LineString::from(vec![(2.0, 8.0), (4.0, 8.0), (3.0, 10.0), (2.0, 8.0)]),
                vec![],
            ),
        ];
        let polygon_count = polygons.len();

        let result = pointcloudlasso(&pointcloud, &polygons).expect("pointcloudlasso failed");
        assert_eq!(result.len(), polygon_count);

        let mut result_0 = result[0].clone();
        let mut result_1 = result[1].clone();
        let mut result_2 = result[2].clone();
        result_0.sort_unstable();
        result_1.sort_unstable();
        result_2.sort_unstable();

        assert_eq!(result_0, vec![0, 1]);
        assert_eq!(result_1, vec![2, 3]);
        assert_eq!(result_2, vec![4]);
    }

    #[test]
    fn test_tile_mismatch_error() {
        let error = LassoError::TileMismatch {
            polygon_tiles: 5,
            point_tiles: 3,
        };
        assert_eq!(
            error.to_string(),
            "Tile count mismatch: 5 polygon tiles vs 3 point tiles"
        );
    }

    #[test]
    fn test_empty_input_error() {
        let error = LassoError::EmptyInput;
        assert_eq!(error.to_string(), "Empty input data provided");
    }

    #[test]
    fn test_invalid_polygon_error() {
        let error = LassoError::InvalidPolygon { index: 42 };
        assert_eq!(error.to_string(), "Invalid polygon at index 42");
    }

    #[test]
    fn test_early_empty_validation() {
        // Test empty pointcloud with empty polygons
        let points: Vec<[FloatType; 2]> = vec![];
        let polygons: Vec<geo::Polygon<FloatType>> = vec![];
        let res = pointcloudlasso(&points, &polygons).expect("should handle empty inputs");
        assert_eq!(
            res,
            Vec::<Vec<usize>>::new(),
            "Empty polygons should return empty results"
        );

        // Test empty pointcloud with some polygons
        let polygons = vec![Polygon::new(
            LineString::from(vec![(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]),
            vec![],
        )];
        let res = pointcloudlasso(&points, &polygons).expect("should handle empty pointcloud");
        assert_eq!(
            res,
            vec![Vec::<usize>::new()],
            "Empty pointcloud should return empty vec for each polygon"
        );

        // Test non-empty pointcloud with empty polygons
        let points: Vec<[FloatType; 2]> = vec![[0.5, 0.5]];
        let polygons: Vec<geo::Polygon<FloatType>> = vec![];
        let res = pointcloudlasso(&points, &polygons).expect("should handle empty polygons");
        assert_eq!(
            res,
            Vec::<Vec<usize>>::new(),
            "Empty polygons should return empty results"
        );
    }
}
