// BoundingBox2D and SearchTree implementation using standard Rust crates
// Cargo.toml dependencies:
// rstar = "0.11.0"

use crate::FloatType;
use rstar::{RTree, RTreeObject, AABB};
use std::fmt;

/// IndexedBBox - a bounding box with an associated index
/// This is used to link bounding boxes with their original objects in the R-tree
#[derive(Debug, Clone)]
pub struct IndexedBBox {
    /// The bounding box
    pub bbox: AABB<[FloatType; 2]>,
    /// The index of the original object
    pub index: usize,
}

impl IndexedBBox {
    /// Create a new indexed bounding box
    pub fn new(bbox: AABB<[FloatType; 2]>, index: usize) -> Self {
        Self { bbox, index }
    }
}

/// RTreeObject implementation for IndexedBBox
impl RTreeObject for IndexedBBox {
    type Envelope = AABB<[FloatType; 2]>;
    fn envelope(&self) -> Self::Envelope {
        self.bbox
    }
}

/// SearchTree for 2D bounding boxes using RTree as the backend
#[derive(Debug, Clone)]
pub struct SearchTree {
    /// The R-tree used for spatial indexing
    rtree: RTree<IndexedBBox>,
}

impl SearchTree {
    /// Create a new empty search tree
    pub fn new() -> Self {
        Self {
            rtree: RTree::new(),
        }
    }

    /// Build the search tree from a collection of bounding boxes
    pub fn build(&mut self, bboxes: Vec<AABB<[FloatType; 2]>>) {
        // Create indexed bounding boxes for the RTree
        let indexed_bboxes: Vec<IndexedBBox> = bboxes
            .into_iter()
            .enumerate()
            .map(|(index, bbox)| IndexedBBox::new(bbox, index))
            .collect();

        // Build the RTree
        self.rtree = RTree::bulk_load(indexed_bboxes);
    }

    /// Find all bounding boxes that contain a point
    #[allow(dead_code)]
    pub fn find_containing_point(&self, point_array: &[FloatType; 2]) -> Vec<usize> {
        // Find all boxes containing the point
        self.rtree
            .locate_in_envelope_intersecting(&AABB::from_point(*point_array))
            .map(|box_entry| box_entry.index)
            .collect()
    }

    /// Find all bounding boxes that intersect with a given bounding box
    pub fn find_intersecting(&self, query_bbox: &AABB<[FloatType; 2]>) -> Vec<usize> {
        // Convert to rstar's AABB format

        // Find all intersecting boxes and return their indices
        self.rtree
            .locate_in_envelope_intersecting(query_bbox)
            .map(|box_entry| box_entry.index)
            .collect()
    }

    /// Find all pairs of intersecting bounding boxes between this tree and another tree
    pub fn find_intersecting_pairs(&self, other: &SearchTree) -> Vec<(usize, usize)> {
        let mut result = Vec::new();

        // Iterate through all boxes in the other tree

        for other_entry in other.rtree.iter() {
            let other_idx = other_entry.index;
            let other_bbox = &other_entry.bbox;
            let intersecting_indices = self.find_intersecting(other_bbox);

            //Add pairs to the result
            for this_idx in intersecting_indices {
                result.push((this_idx, other_idx));
            }
        }

        result
    }

    /// Get the number of bounding boxes in the tree
    pub fn len(&self) -> usize {
        self.rtree.size()
    }
}

impl fmt::Display for SearchTree {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "SearchTree with {} objects", self.len())
    }
}

// Example usage
#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;

    #[test]
    fn test_search_tree() {
        // Create some bounding boxes
        let bboxes = vec![
            AABB::from_corners([0.0, 0.0], [10.0, 10.0]),
            AABB::from_corners([5.0, 5.0], [15.0, 15.0]),
            AABB::from_corners([20.0, 20.0], [30.0, 30.0]),
        ];

        // Build the tree
        let mut tree = SearchTree::new();
        tree.build(bboxes);

        // Test point queries
        let point1 = [7.0, 7.0];

        let point2 = [25.0, 25.0];
        let point3 = [17.0, 17.0];

        let containing1 = tree.find_containing_point(&point1);
        let containing2 = tree.find_containing_point(&point2);
        let containing3 = tree.find_containing_point(&point3);

        // Point1 should be in both bbox 0 and 1
        assert_eq!(containing1.len(), 2);
        assert!(containing1.contains(&0));
        assert!(containing1.contains(&1));

        // Point2 should be in bbox 2
        assert_eq!(containing2.len(), 1);
        assert!(containing2.contains(&2));

        // Point3 should be in no bbox
        assert_eq!(containing3.len(), 0);

        // Test bbox queries
        let query_bbox = AABB::from_corners([8.0, 8.0], [22.0, 22.0]);

        let intersecting = tree.find_intersecting(&query_bbox);

        // Query bbox should intersect with bbox 0, 1, and 2
        assert_eq!(intersecting.len(), 3);
        assert!(intersecting.contains(&0));
        assert!(intersecting.contains(&1));
        assert!(intersecting.contains(&2));
    }

    #[test]
    fn test_find_intersecting_pairs_no_intersection() {
        // Create two search trees with non-overlapping bounding boxes
        let bboxes1 = vec![AABB::from_corners([0.0, 0.0], [5.0, 5.0])];
        let bboxes2 = vec![AABB::from_corners([10.0, 10.0], [25.0, 25.0])];

        let mut tree1 = SearchTree::new();
        let mut tree2 = SearchTree::new();
        tree1.build(bboxes1);
        tree2.build(bboxes2);

        let pairs = tree1.find_intersecting_pairs(&tree2);
        assert!(pairs.is_empty());
    }

    #[test]
    fn test_find_intersecting_pairs_with_intersection() {
        // Create two search trees with overlapping bounding boxes

        let bboxes1 = vec![AABB::from_corners([0.0, 0.0], [10.0, 10.0])];
        let bboxes2 = vec![AABB::from_corners([5.0, 5.0], [15.0, 15.0])];

        let mut tree1 = SearchTree::new();
        let mut tree2 = SearchTree::new();
        tree1.build(bboxes1);
        tree2.build(bboxes2);

        let pairs = tree1.find_intersecting_pairs(&tree2);
        assert_eq!(pairs.len(), 1);
        assert_eq!(pairs[0], (0, 0));
    }

    #[test]
    fn test_find_intersecting_pairs_multiple_intersections() {
        // Create two search trees with multiple overlapping bounding boxes
        let bboxes1 = vec![
            AABB::from_corners([0.0, 0.0], [10.0, 10.0]),
            AABB::from_corners([20.0, 20.0], [30.0, 30.0]),
        ];
        let bboxes2 = vec![
            AABB::from_corners([5.0, 5.0], [7.0, 7.0]),
            AABB::from_corners([5.0, 5.0], [25.0, 25.0]),
            AABB::from_corners([25.0, 25.0], [35.0, 35.0]),
        ];

        let mut tree1 = SearchTree::new();
        let mut tree2 = SearchTree::new();
        tree1.build(bboxes1);
        tree2.build(bboxes2);

        let pairs = tree1.find_intersecting_pairs(&tree2);
        assert_eq!(pairs.len(), 4);
        assert!(pairs.contains(&(0, 0)));
        assert!(pairs.contains(&(0, 1)));
        assert!(pairs.contains(&(1, 1)));
        assert!(pairs.contains(&(1, 2)));
    }
}
