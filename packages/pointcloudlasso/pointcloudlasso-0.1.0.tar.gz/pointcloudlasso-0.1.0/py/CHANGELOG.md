# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-09

### Added
- Initial PyPI release
- Fast point-in-polygon tests for 2D and 3D point clouds
- Python bindings with NumPy and Shapely integration
- Parallel processing with spatial tiling optimization for improved performance
- Support for polygons with holes (interior rings)
- Type hints with PEP 561 compliance (py.typed marker and .pyi stubs)
- Comprehensive test suite with edge case coverage
- Multi-platform support (Linux, Windows, macOS) for x86_64 and aarch64
- Python 3.10, 3.11, 3.12, and 3.13 compatibility

### Features
- Zero-copy NumPy array handling for optimal performance
- Automatic spatial tiling to reduce search space
- Lock-free concurrent result aggregation using DashMap
- Support for both 2D [[f32; 2]] and 3D [[f32; 3]] point clouds
- Returns point indices for each polygon as NumPy arrays
