use crate::FloatType;
use geo::{Centroid, Contains, Point, Polygon};

pub fn point_in_polygon(point: &[FloatType; 2], polygon: &Polygon<FloatType>) -> bool {
    let point = Point::new(point[0], point[1]);
    polygon.contains(&point)
}

pub fn polygon_radius_sqr(poly: &Polygon<FloatType>) -> FloatType {
    let mut max_distance = 0.0;
    let Some(centroid) = poly.centroid() else {
        return 0.0;
    };

    let (c_x, c_y) = centroid.x_y();

    for coord in poly.exterior() {
        let distance = (coord.x - c_x).powi(2) + (coord.y - c_y).powi(2);
        if distance > max_distance {
            max_distance = distance;
        }
    }
    max_distance
}

pub fn polygon_radius(poly: &Polygon<FloatType>) -> FloatType {
    polygon_radius_sqr(poly).sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;
    use geo::{Coord, LineString};

    #[test]
    fn test_point_in_polygon_inside() {
        let polygon = Polygon::new(
            LineString::from(vec![
                Coord { x: 0.0, y: 0.0 },
                Coord { x: 4.0, y: 0.0 },
                Coord { x: 4.0, y: 4.0 },
                Coord { x: 0.0, y: 4.0 },
                Coord { x: 0.0, y: 0.0 },
            ]),
            vec![],
        );
        assert!(point_in_polygon(&[2.0, 2.0], &polygon));
    }

    #[test]
    fn test_point_in_polygon_outside() {
        let polygon = Polygon::new(
            LineString::from(vec![
                Coord { x: 0.0, y: 0.0 },
                Coord { x: 4.0, y: 0.0 },
                Coord { x: 4.0, y: 4.0 },
                Coord { x: 0.0, y: 4.0 },
                Coord { x: 0.0, y: 0.0 },
            ]),
            vec![],
        );
        assert!(!point_in_polygon(&[5.0, 5.0], &polygon));
    }

    #[test]
    fn test_polygon_radius_square() {
        let polygon = Polygon::new(
            LineString::from(vec![
                Coord { x: 0.0, y: 0.0 },
                Coord { x: 4.0, y: 0.0 },
                Coord { x: 4.0, y: 4.0 },
                Coord { x: 0.0, y: 4.0 },
                Coord { x: 0.0, y: 0.0 },
            ]),
            vec![],
        );
        let radius = polygon_radius(&polygon);
        // For a square centered at (2,2), the distance to corner (4,4) is sqrt(8)
        assert!((radius - 2.828427).abs() < 0.001);
    }

    #[test]
    fn test_polygon_radius_invalid() {
        let polygon = Polygon::new(LineString::from(vec![Coord { x: 0.0, y: 0.0 }]), vec![]);
        assert_eq!(polygon_radius(&polygon), 0.0);
    }
}
