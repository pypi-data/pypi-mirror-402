use crate::search_tree::SearchTree;
use crate::search_tree::{aabb_from_polygon, aabb_from_polygons, tile_aabb};
use crate::FloatType;
use geo::Polygon;
use rstar::{Envelope, AABB};
use std::collections::HashMap;

type PolyTiles = Vec<(Vec<usize>, AABB<[FloatType; 2]>)>;

/// Tile size multiplier for automatic tiling.
/// 2.5x the average polygon size balances between:
/// Based on some empirical tests.
const TILE_SIZE_MULTIPLIER: FloatType = 2.5;

pub fn polygon_stats(polygons: &[Polygon<FloatType>]) -> FloatType {
    if polygons.is_empty() {
        return 0.0;
    }
    let mut side_length = 0.0;
    for polygon in polygons {
        let bbox = aabb_from_polygon(polygon);
        let width = bbox.upper()[0] - bbox.lower()[0];
        let height = bbox.upper()[1] - bbox.lower()[1];
        side_length += (width * height).sqrt();
    }

    side_length / polygons.len() as FloatType
}

pub fn group_polygons_by_tile(
    polygons: &[Polygon<FloatType>],
    x_tile_arg: usize,
    y_tile_arg: usize,
) -> PolyTiles {
    let bbox = aabb_from_polygons(polygons);
    let mut x_tiles = x_tile_arg;
    let mut y_tiles = y_tile_arg;
    if x_tiles == 0 || y_tiles == 0 {
        let avg_side_length = polygon_stats(polygons);
        let tile_size: FloatType = avg_side_length * TILE_SIZE_MULTIPLIER;

        if tile_size <= 0.0 {
            // Fallback: if tile_size is invalid, create a single tile containing all polygons
            x_tiles = 1;
            y_tiles = 1;
        } else {
            let box_width = bbox.upper()[0] - bbox.lower()[0];
            let box_height = bbox.upper()[1] - bbox.lower()[1];
            x_tiles = ((box_width / tile_size).ceil() as usize).max(1);
            y_tiles = ((box_height / tile_size).ceil() as usize).max(1);
        }
    }

    let tiled_bboxes = tile_aabb(&bbox, x_tiles, y_tiles);
    let mut result: PolyTiles = vec![(Vec::new(), AABB::from_point([0.0, 0.0])); x_tiles * y_tiles];

    let poly_bboxes: Vec<AABB<[FloatType; 2]>> = polygons.iter().map(aabb_from_polygon).collect();

    let mut tile_search_tree = SearchTree::new();
    let mut polygon_search_tree = SearchTree::new();
    tile_search_tree.build(tiled_bboxes);
    polygon_search_tree.build(poly_bboxes);

    let polygon_tile_pairs = polygon_search_tree.find_intersecting_pairs(&tile_search_tree);
    let mut poly_index_to_tile_index: HashMap<usize, usize> = HashMap::new();

    for (polygon_index, tile_index) in polygon_tile_pairs {
        poly_index_to_tile_index.insert(polygon_index, tile_index);
    }

    for (key, value) in &poly_index_to_tile_index {
        result[*value].0.push(*key);
    }

    for tile in result.iter_mut() {
        let mut tile_bbox = AABB::from_point([0.0, 0.0]);
        for idx in tile.0.iter() {
            let polygon_bbox = aabb_from_polygon(&polygons[*idx]);
            if tile_bbox.area() == 0.0 {
                tile_bbox = polygon_bbox;
            } else {
                tile_bbox.merge(&polygon_bbox);
            }
        }
        tile.1 = tile_bbox;
    }

    result.retain(|tile| !tile.0.is_empty());

    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use geo::{LineString, Polygon};

    use pretty_assertions::assert_eq;

    #[test]
    fn test_group_polygons_by_tile() {
        let polygons = vec![
            Polygon::new(
                LineString::from(vec![
                    (0.0, 0.0),
                    (1.0, 0.0),
                    (1.0, 1.0),
                    (0.0, 1.0),
                    (0.0, 0.0),
                ]),
                vec![],
            ),
            Polygon::new(
                LineString::from(vec![
                    (2.0, 2.0),
                    (3.0, 2.0),
                    (3.0, 3.0),
                    (2.0, 3.0),
                    (2.0, 2.0),
                ]),
                vec![],
            ),
        ];

        let x_tiles = 3;
        let y_tiles = 3;

        let result = group_polygons_by_tile(&polygons, x_tiles, y_tiles);

        assert_eq!(result.len(), 2);
        let mut num_poly = 0;
        for r in result.iter() {
            num_poly += r.0.len();
            assert_eq!(r.0.len(), 1); // each tile should contain only one polygon
        }
        assert_eq!(num_poly, polygons.len());
    }

    #[test]
    fn test_polygon_stats_empty() {
        let polygons: Vec<Polygon<FloatType>> = vec![];
        assert_eq!(polygon_stats(&polygons), 0.0);
    }

    #[test]
    fn test_polygon_stats() {
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
                    (0.0, 0.0),
                    (4.0, 0.0),
                    (4.0, 4.0),
                    (0.0, 4.0),
                    (0.0, 0.0),
                ]),
                vec![],
            ),
        ];
        let avg = polygon_stats(&polygons);
        // First polygon: sqrt(4) = 2, Second: sqrt(16) = 4, Avg: (2+4)/2 = 3
        assert_eq!(avg, 3.0);
    }

    #[test]
    fn test_group_polygons_auto_tiling() {
        let polygons = vec![
            Polygon::new(
                LineString::from(vec![
                    (0.0, 0.0),
                    (1.0, 0.0),
                    (1.0, 1.0),
                    (0.0, 1.0),
                    (0.0, 0.0),
                ]),
                vec![],
            ),
            Polygon::new(
                LineString::from(vec![
                    (10.0, 10.0),
                    (11.0, 10.0),
                    (11.0, 11.0),
                    (10.0, 11.0),
                    (10.0, 10.0),
                ]),
                vec![],
            ),
        ];

        let result = group_polygons_by_tile(&polygons, 0, 0);
        assert!(!result.is_empty());
        let total_polys: usize = result.iter().map(|(indices, _)| indices.len()).sum();
        assert_eq!(total_polys, polygons.len());
    }
}
