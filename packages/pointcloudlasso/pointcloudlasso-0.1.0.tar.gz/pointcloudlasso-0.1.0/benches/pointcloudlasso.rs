use criterion::{criterion_group, criterion_main, Criterion};

use pointcloudlasso::pointcloudlasso;

use geo::{Coord, LineString, Polygon};
use shapefile::{Shape, ShapeReader};
use std::path::Path;

pub type FloatType = f32;

fn load_las_file(file_path: &Path) -> Result<Vec<[FloatType; 3]>, Box<dyn std::error::Error>> {
    // Load the LAS file and return the point cloud as a 2D array
    // This is a placeholder implementation

    let mut reader = las::Reader::from_path(file_path)?;
    let num_points = reader.header().number_of_points() as usize;
    let mut pt_vec: Vec<[FloatType; 3]> = Vec::with_capacity(num_points);

    for wrapped_pt in reader.points() {
        let pt = wrapped_pt?;
        pt_vec.push([pt.x as FloatType, pt.y as FloatType, pt.z as FloatType]);
    }

    println!("Loaded {} points", pt_vec.len());

    Ok(pt_vec)
}

fn load_polygons(
    file_path: &Path,
) -> Result<Vec<geo::Polygon<FloatType>>, Box<dyn std::error::Error>> {
    // Load the polygons from a file and return them as a vector
    // This is a placeholder implementation

    let mut polygons: Vec<Polygon<FloatType>> = Vec::new();
    let mut reader = ShapeReader::from_path(file_path)?;
    for result in reader.iter_shapes() {
        let shape = result?;

        if let Shape::PolygonZ(shp_polygon) = shape {
            let rings = shp_polygon.rings();

            if rings.is_empty() {
                continue; // skip empty shapes
            }

            let convert_ring =
                |ring: &shapefile::PolygonRing<shapefile::PointZ>| -> LineString<FloatType> {
                    LineString::from(
                        ring.points()
                            .iter()
                            .map(|pt| Coord {
                                x: pt.x as FloatType,
                                y: pt.y as FloatType,
                            })
                            .collect::<Vec<_>>(),
                    )
                };

            let exterior = convert_ring(&rings[0]);
            let interiors = rings[1..].iter().map(convert_ring).collect::<Vec<_>>();

            let polygon = Polygon::new(exterior, interiors);
            polygons.push(polygon);
        }
    }
    println!("Loaded {} polygons", polygons.len());

    Ok(polygons)
}

fn benchmark_pointcloudlasso(c: &mut Criterion) {
    let data_root = Path::new("./benches/data");
    let data_path = data_root.join("helsingborg_residential");
    let las_file = data_path.join("pointcloud.las");
    let polygons_file = data_path.join("footprints.shp");
    let polygons = load_polygons(&polygons_file).unwrap();
    let pointcloud = load_las_file(&las_file).unwrap();

    c.bench_function("pointcloudlasso", |b| {
        b.iter(|| {
            pointcloudlasso(&pointcloud, &polygons.clone()).expect("pointcloudlasso failed");
        })
    });
}

criterion_group! {
    name = benches;
    config = Criterion::default().sample_size(50).measurement_time(std::time::Duration::new(10, 0));
    targets = benchmark_pointcloudlasso
}
criterion_main!(benches);
