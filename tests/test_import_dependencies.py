import pytest

# List of dependencies
dependencies = [
    "affine",
    "colored_logging",  # for packages with hyphens use underscore
    "geopandas",
    "numpy",
    "pyproj",
    "rasterio",
    "scipy",
    "shapely",
    "pandas",
    "rasters",
    "requests",
    "bs4",
    "dateutil",  # python-dateutil imports as dateutil
    "matplotlib",
    "urllib3"
]

# Generate individual test functions for each dependency
@pytest.mark.parametrize("dependency", dependencies)
def test_dependency_import(dependency):
    __import__(dependency)
