use crate::tiling::spatial_hash_tiler::pointcloud_to_tiles_spatial_hash;
use crate::FloatType;
use rstar::AABB;

/// Adaptive selector that chooses the best algorithm based on data characteristics
pub fn pointcloud_to_tiles<P: crate::Point2DLike + Sync>(
    pointcloud: &[P],
    tiles: &[AABB<[FloatType; 2]>],
) -> Vec<Vec<usize>> {
    let _point_count = pointcloud.len();
    let _tile_count = tiles.len();

    pointcloud_to_tiles_spatial_hash(pointcloud, tiles)
}

#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;

    #[test]
    fn test_pointcloud_to_tiles() {
        let pointcloud = vec![
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0],
        ];
        let tiles = vec![
            AABB::from_corners([0.0, 0.0], [1.5, 1.5]),
            AABB::from_corners([1.5, 1.5], [3.0, 3.0]),
        ];
        let result = pointcloud_to_tiles(&pointcloud, &tiles);
        assert_eq!(result.len(), 2);
        let mut result_0 = result[0].clone();
        let mut result_1 = result[1].clone();
        result_0.sort();
        result_1.sort();
        assert_eq!(result_0, vec![0, 1]);
        assert_eq!(result_1, vec![2, 3]);
    }

    #[test]
    fn test_points_outside_of_tiles() {
        let pointcloud = vec![
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0],
        ];
        let tiles = vec![
            AABB::from_corners([4.0, 4.0], [5.5, 5.5]),
            AABB::from_corners([5.5, 5.5], [7.0, 7.0]),
            AABB::from_corners([2.5, 2.5], [3.5, 3.5]),
        ];
        let result = pointcloud_to_tiles(&pointcloud, &tiles);
        assert_eq!(result.len(), 3);
        assert_eq!(result[0].len(), 0);
        assert_eq!(result[1].len(), 0);
        assert_eq!(result[2], vec![3]);
    }

    #[test]
    fn test_spatial_hash_implementation() {
        let pointcloud = vec![
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0],
        ];
        let tiles = vec![
            AABB::from_corners([0.0, 0.0], [1.5, 1.5]),
            AABB::from_corners([1.5, 1.5], [3.0, 3.0]),
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
}
