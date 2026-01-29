use crate::FloatType;

use crate::utils::geometry::polygon_radius_sqr;

use geo::{Centroid, Contains, Polygon};

use kiddo::{ImmutableKdTree, SquaredEuclidean};

pub fn points_in_polygons(
    pointcloud: &[[FloatType; 2]],
    polygons: &[&Polygon<FloatType>],
) -> Vec<Vec<usize>> {
    crate::profile_function!();

    let mut result = vec![Vec::new(); polygons.len()];

    if pointcloud.is_empty() || polygons.is_empty() {
        return result; // Early return for empty pointcloud
    }

    let kdtree: ImmutableKdTree<FloatType, 2> = {
        crate::profile_scope!("kdtree_build");
        ImmutableKdTree::new_from_slice(pointcloud)
    };

    for (i, p) in polygons.iter().enumerate() {
        let r = polygon_radius_sqr(p); // squared radius for squared euclidean distance
        if r == 0.0 {
            // if the polygon has no area or is invalid it contains no points
            continue;
        }
        let Some(centroid) = p.centroid() else {
            continue; // Skip polygons without valid centroid
        };
        let (c_x, c_y) = centroid.x_y();

        let pt_candidates = {
            crate::profile_scope!("kdtree_query");
            kdtree.within_unsorted::<SquaredEuclidean>(&[c_x, c_y], r)
        };

        let pts_in_poly = {
            crate::profile_scope!("exact_contains");
            pt_candidates
                .iter()
                .map(|&nn| nn.item as usize)
                .filter(|&idx| (*p).contains(&geo::Point::new(pointcloud[idx][0], pointcloud[idx][1])))
                .collect::<Vec<_>>()
        };

        result[i] = pts_in_poly;
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use geo::{Coord, Polygon};
    #[test]
    fn test_multiple_polygons_comprehensive() {
        let pointcloud = vec![[0.5, 0.5], [1.5, 1.5], [5.5, 5.5], [6.5, 6.5], [3.0, 9.0]];

        let polygons = [
            Polygon::new(
                vec![
                    Coord { x: 0.0, y: 0.0 },
                    Coord { x: 2.0, y: 0.0 },
                    Coord { x: 2.0, y: 2.0 },
                    Coord { x: 0.0, y: 2.0 },
                    Coord { x: 0.0, y: 0.0 },
                ]
                .into(),
                vec![],
            ),
            Polygon::new(
                vec![
                    Coord { x: 5.0, y: 5.0 },
                    Coord { x: 8.0, y: 5.0 },
                    Coord { x: 8.0, y: 7.0 },
                    Coord { x: 5.0, y: 7.0 },
                    Coord { x: 5.0, y: 5.0 },
                ]
                .into(),
                vec![],
            ),
            Polygon::new(
                vec![
                    Coord { x: 2.0, y: 8.0 },
                    Coord { x: 4.0, y: 8.0 },
                    Coord { x: 3.0, y: 10.0 },
                    Coord { x: 2.0, y: 8.0 },
                ]
                .into(),
                vec![],
            ),
        ];

        let polygon_refs: Vec<&Polygon<FloatType>> = polygons.iter().collect();
        let result = points_in_polygons(&pointcloud, &polygon_refs);

        assert_eq!(
            result.len(),
            polygons.len(),
            "Should return results for all polygons"
        );

        for (i, indices) in result.iter().enumerate() {
            assert!(
                !indices.is_empty(),
                "Polygon {} should contain at least one point",
                i
            );

            let unique_indices: Vec<_> = indices.to_vec();
            assert_eq!(
                unique_indices.len(),
                indices.len(),
                "Polygon {} should not have duplicate indices",
                i
            );

            for &idx in indices {
                assert!(
                    idx < pointcloud.len(),
                    "Index {} for polygon {} is out of bounds",
                    idx,
                    i
                );
            }
        }
    }

    #[test]
    fn test_polygon_with_holes() {
        let pointcloud = vec![[0.5, 0.5], [1.5, 1.5], [2.5, 2.5], [3.5, 1.5], [5.0, 5.0]];

        let exterior = vec![
            Coord { x: 0.0, y: 0.0 },
            Coord { x: 4.0, y: 0.0 },
            Coord { x: 4.0, y: 4.0 },
            Coord { x: 0.0, y: 4.0 },
            Coord { x: 0.0, y: 0.0 },
        ];

        let hole = vec![
            Coord { x: 2.0, y: 2.0 },
            Coord { x: 3.0, y: 2.0 },
            Coord { x: 3.0, y: 3.0 },
            Coord { x: 2.0, y: 3.0 },
            Coord { x: 2.0, y: 2.0 },
        ];

        let polygon_with_hole = Polygon::new(exterior.into(), vec![hole.into()]);

        let result = points_in_polygons(&pointcloud, &[&polygon_with_hole]);

        assert_eq!(result.len(), 1, "Should return results for 1 polygon");
        assert_eq!(
            result[0],
            vec![0, 1, 3],
            "Points inside the hole should be excluded"
        );
    }
}
