use crate::FloatType;
use cgmath::Vector3;
use dashmap::DashMap;
use rayon::prelude::*;
use rstar::AABB;
use spatial_hash_3d::SpatialHashGrid;
use std::collections::HashMap;

/// Configuration for the spatial hash grid
pub struct HashGridConfig {
    /// Cell size in world units
    pub cell_size: FloatType,
    /// Grid origin (min point)
    pub origin: [FloatType; 2],
    /// Grid dimensions (number of cells in X and Y)
    pub dimensions: [usize; 2],
}

impl HashGridConfig {
    /// Auto-detect optimal configuration from tiles
    pub fn from_tiles(tiles: &[AABB<[FloatType; 2]>]) -> Self {
        if tiles.is_empty() {
            return Self {
                cell_size: 1.0,
                origin: [0.0, 0.0],
                dimensions: [1, 1],
            };
        }

        // Find overall bounds
        let mut min_x = FloatType::MAX;
        let mut min_y = FloatType::MAX;
        let mut max_x = FloatType::MIN;
        let mut max_y = FloatType::MIN;

        for tile in tiles {
            min_x = min_x.min(tile.lower()[0]);
            min_y = min_y.min(tile.lower()[1]);
            max_x = max_x.max(tile.upper()[0]);
            max_y = max_y.max(tile.upper()[1]);
        }

        // Calculate average tile size to determine cell size
        let mut avg_width = 0.0;
        let mut avg_height = 0.0;
        for tile in tiles {
            avg_width += tile.upper()[0] - tile.lower()[0];
            avg_height += tile.upper()[1] - tile.lower()[1];
        }
        avg_width /= tiles.len() as FloatType;
        avg_height /= tiles.len() as FloatType;

        // Use smaller dimension for cell size to ensure good granularity
        let cell_size = avg_width.min(avg_height);

        // Calculate grid dimensions with some padding
        let width = max_x - min_x;
        let height = max_y - min_y;
        let x_cells = ((width / cell_size).ceil() as usize).max(1);
        let y_cells = ((height / cell_size).ceil() as usize).max(1);

        Self {
            cell_size,
            origin: [min_x, min_y],
            dimensions: [x_cells, y_cells],
        }
    }

    /// Convert world coordinates to grid cell
    fn world_to_cell(&self, point: &[FloatType; 2]) -> Option<(usize, usize)> {
        let x = ((point[0] - self.origin[0]) / self.cell_size) as isize;
        let y = ((point[1] - self.origin[1]) / self.cell_size) as isize;

        if x >= 0 && y >= 0 && x <= self.dimensions[0] as isize && y <= self.dimensions[1] as isize
        {
            // Clamp to valid cell indices (handle points exactly on upper boundary)
            let x_clamped = (x as usize).min(self.dimensions[0] - 1);
            let y_clamped = (y as usize).min(self.dimensions[1] - 1);
            Some((x_clamped, y_clamped))
        } else {
            None
        }
    }

    /// Convert to Vector3 for spatial_hash_3d (Z=0 for 2D)
    fn cell_to_vector3(&self, x: usize, y: usize) -> Vector3<u32> {
        Vector3::new(x as u32, y as u32, 0)
    }
}

/// Build a spatial hash grid containing tile indices
fn build_tile_hash(
    tiles: &[AABB<[FloatType; 2]>],
    config: &HashGridConfig,
) -> SpatialHashGrid<Vec<usize>> {
    // Create grid (Z dimension is 1 for 2D)
    let mut grid = SpatialHashGrid::new(
        config.dimensions[0],
        config.dimensions[1],
        1,
        Vec::new, // Each cell contains a Vec of tile indices
    );

    // For each tile, add its index to all cells it overlaps
    for (tile_idx, tile) in tiles.iter().enumerate() {
        let min_cell = config.world_to_cell(&[tile.lower()[0], tile.lower()[1]]);
        let max_cell = config.world_to_cell(&[tile.upper()[0], tile.upper()[1]]);

        if let (Some((min_x, min_y)), Some((max_x, max_y))) = (min_cell, max_cell) {
            // Insert tile index into all cells it overlaps
            for x in min_x..=max_x.min(config.dimensions[0] - 1) {
                for y in min_y..=max_y.min(config.dimensions[1] - 1) {
                    let vec3 = config.cell_to_vector3(x, y);
                    grid[vec3].push(tile_idx);
                }
            }
        }
    }

    grid
}

/// Main function: Assign points to tiles using spatial hash
pub fn pointcloud_to_tiles_spatial_hash<P: crate::Point2DLike + Sync>(
    pointcloud: &[P],
    tiles: &[AABB<[FloatType; 2]>],
) -> Vec<Vec<usize>> {
    // Step 1: Build configuration
    let config = HashGridConfig::from_tiles(tiles);

    // Step 2: Build spatial hash of tiles
    let tile_hash = build_tile_hash(tiles, &config);

    // Step 3: Query each point against the hash grid
    let result: DashMap<usize, Vec<usize>> = DashMap::with_capacity(tiles.len());

    // Process points in parallel with chunking for better cache performance
    const CHUNK_SIZE: usize = 1024;
    pointcloud
        .par_chunks(CHUNK_SIZE)
        .enumerate()
        .for_each(|(chunk_idx, chunk)| {
            // Thread-local buffer to reduce synchronization
            let mut local_results: HashMap<usize, Vec<usize>> = HashMap::new();

            for (local_idx, point) in chunk.iter().enumerate() {
                let global_idx = chunk_idx * CHUNK_SIZE + local_idx;

                // Get grid cell for this point (O(1))
                let point_x = point.x();
                let point_y = point.y();
                if let Some((x, y)) = config.world_to_cell(&[point_x, point_y]) {
                    let vec3 = config.cell_to_vector3(x, y);
                    let candidate_tiles = &tile_hash[vec3];

                    // Test exact containment for candidate tiles only
                    for &tile_idx in candidate_tiles {
                        let tile = &tiles[tile_idx];
                        if point_x >= tile.lower()[0]
                            && point_x <= tile.upper()[0]
                            && point_y >= tile.lower()[1]
                            && point_y <= tile.upper()[1]
                        {
                            local_results.entry(tile_idx).or_default().push(global_idx);
                        }
                    }
                }
            }

            // Batch merge to global results
            for (tile_idx, point_indices) in local_results {
                result.entry(tile_idx).or_default().extend(point_indices);
            }
        });

    // Step 4: Convert to final result format
    let mut final_result = vec![Vec::new(); tiles.len()];
    for (tile_idx, point_indices) in result.into_iter() {
        final_result[tile_idx] = point_indices;
    }

    final_result
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tiling::pointcloud_to_tiles;
    use pretty_assertions::assert_eq;

    #[test]
    fn test_spatial_hash_basic() {
        let pointcloud = vec![
            [0.5, 0.5, 1.0],
            [1.5, 1.5, 2.0],
            [5.5, 5.5, 3.0],
            [6.5, 6.5, 4.0],
        ];

        let tiles = vec![
            AABB::from_corners([0.0, 0.0], [2.0, 2.0]),
            AABB::from_corners([5.0, 5.0], [7.0, 7.0]),
        ];

        let result = pointcloud_to_tiles_spatial_hash(&pointcloud, &tiles);

        assert_eq!(result.len(), 2);

        let mut result_0 = result[0].clone();
        let mut result_1 = result[1].clone();
        result_0.sort();
        result_1.sort();

        assert_eq!(result_0, vec![0, 1]);
        assert_eq!(result_1, vec![2, 3]);
    }

    #[test]
    fn test_spatial_hash_dense() {
        // Generate dense uniform point cloud
        let mut pointcloud = Vec::new();
        for x in 0..100 {
            for y in 0..100 {
                pointcloud.push([x as FloatType, y as FloatType, x as FloatType / 10.0]);
            }
        }

        let tiles = vec![
            AABB::from_corners([0.0, 0.0], [50.0, 50.0]),
            AABB::from_corners([50.0, 50.0], [100.0, 100.0]),
        ];

        let result_hash = pointcloud_to_tiles_spatial_hash(&pointcloud, &tiles);

        // Compare with R-tree implementation to ensure consistency
        let result_rtree = pointcloud_to_tiles::pointcloud_to_tiles(&pointcloud, &tiles);

        assert_eq!(result_hash.len(), 2);
        assert_eq!(result_rtree.len(), 2);

        // Results should match the R-tree implementation
        assert_eq!(result_hash[0].len(), result_rtree[0].len());
        assert_eq!(result_hash[1].len(), result_rtree[1].len());

        // Verify the actual point indices match (after sorting)
        let mut hash_0 = result_hash[0].clone();
        let mut hash_1 = result_hash[1].clone();
        let mut rtree_0 = result_rtree[0].clone();
        let mut rtree_1 = result_rtree[1].clone();

        hash_0.sort();
        hash_1.sort();
        rtree_0.sort();
        rtree_1.sort();

        assert_eq!(hash_0, rtree_0);
        assert_eq!(hash_1, rtree_1);
    }
}
