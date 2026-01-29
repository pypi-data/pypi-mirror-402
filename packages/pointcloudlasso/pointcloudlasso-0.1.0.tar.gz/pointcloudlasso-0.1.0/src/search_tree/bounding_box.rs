use crate::FloatType;
use geo::Polygon;
use rstar::AABB;

pub fn aabb_from_polygon(polygon: &Polygon<FloatType>) -> AABB<[FloatType; 2]> {
    aabb_from_polygons(std::slice::from_ref(polygon))
}

pub fn aabb_from_polygons(polygons: &[Polygon<FloatType>]) -> AABB<[FloatType; 2]> {
    let mut min_x = FloatType::MAX;
    let mut min_y = FloatType::MAX;
    let mut max_x = FloatType::MIN;
    let mut max_y = FloatType::MIN;

    for polygon in polygons {
        for point in polygon.exterior().points() {
            min_x = min_x.min(point.x() as FloatType);
            min_y = min_y.min(point.y() as FloatType);
            max_x = max_x.max(point.x() as FloatType);
            max_y = max_y.max(point.y() as FloatType);
        }
    }
    AABB::from_corners([min_x, min_y], [max_x, max_y])
}

pub fn tile_aabb(
    aabb: &AABB<[FloatType; 2]>,
    x_tiles: usize,
    y_tiles: usize,
) -> Vec<AABB<[FloatType; 2]>> {
    let x_step = (aabb.upper()[0] - aabb.lower()[0]) / (x_tiles as FloatType);
    let y_step = (aabb.upper()[1] - aabb.lower()[1]) / (y_tiles as FloatType);

    let mut tiles = Vec::new();
    for i in 0..x_tiles {
        for j in 0..y_tiles {
            let min_x = aabb.lower()[0] + i as FloatType * x_step;
            let min_y = aabb.lower()[1] + j as FloatType * y_step;
            let max_x = min_x + x_step;
            let max_y = min_y + y_step;
            tiles.push(AABB::from_corners([min_x, min_y], [max_x, max_y]));
        }
    }
    tiles
}

#[cfg(test)]
mod tests {
    use super::*;
    use geo::{Coord, LineString};

    #[test]
    fn test_tile() {
        let bbox = AABB::from_corners([0.0, 0.0], [10.0, 10.0]);
        let tiles = tile_aabb(&bbox, 3, 5);
        assert_eq!(tiles.len(), 15);
        assert_eq!(tiles[0].lower()[0], 0.0);
        assert_eq!(tiles[0].lower()[1], 0.0);
        assert_eq!(tiles[0].upper()[0], 3.3333333333333335);
        assert_eq!(tiles[0].upper()[1], 2.0);
    }

    #[test]
    fn test_aabb_from_polygon() {
        let polygon = Polygon::new(
            LineString::from(vec![
                Coord { x: 1.0, y: 2.0 },
                Coord { x: 5.0, y: 2.0 },
                Coord { x: 5.0, y: 6.0 },
                Coord { x: 1.0, y: 6.0 },
                Coord { x: 1.0, y: 2.0 },
            ]),
            vec![],
        );
        let aabb = aabb_from_polygon(&polygon);
        assert_eq!(aabb.lower()[0], 1.0);
        assert_eq!(aabb.lower()[1], 2.0);
        assert_eq!(aabb.upper()[0], 5.0);
        assert_eq!(aabb.upper()[1], 6.0);
    }

    #[test]
    fn test_aabb_from_polygons() {
        let polygons = vec![
            Polygon::new(
                LineString::from(vec![
                    Coord { x: 0.0, y: 0.0 },
                    Coord { x: 2.0, y: 2.0 },
                    Coord { x: 0.0, y: 0.0 },
                ]),
                vec![],
            ),
            Polygon::new(
                LineString::from(vec![
                    Coord { x: 5.0, y: 5.0 },
                    Coord { x: 10.0, y: 10.0 },
                    Coord { x: 5.0, y: 5.0 },
                ]),
                vec![],
            ),
        ];
        let aabb = aabb_from_polygons(&polygons);
        assert_eq!(aabb.lower()[0], 0.0);
        assert_eq!(aabb.lower()[1], 0.0);
        assert_eq!(aabb.upper()[0], 10.0);
        assert_eq!(aabb.upper()[1], 10.0);
    }

    #[test]
    fn test_tile_aabb_single_tile() {
        let bbox = AABB::from_corners([0.0, 0.0], [10.0, 10.0]);
        let tiles = tile_aabb(&bbox, 1, 1);
        assert_eq!(tiles.len(), 1);
        assert_eq!(tiles[0].lower()[0], 0.0);
        assert_eq!(tiles[0].lower()[1], 0.0);
        assert_eq!(tiles[0].upper()[0], 10.0);
        assert_eq!(tiles[0].upper()[1], 10.0);
    }
}
