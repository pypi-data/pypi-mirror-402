"""
Raster to Geohash Module

This module provides functionality to convert raster data to Geohash DGGS format with automatic resolution determination and multi-band support.

Key Functions:
    raster2geohash: Main conversion function with multiple output formats
    get_nearest_geohash_resolution: Automatically determines optimal Geohash resolution
    raster2geohash_cli: Command-line interface for conversion process
"""

import os
import argparse
from math import cos, radians
from tqdm import tqdm
from vgrid.stats.geohashstats import geohash_metrics
from vgrid.conversion.latlon2dggs import latlon2geohash
from vgrid.utils.io import validate_geohash_resolution, convert_to_output_format
from vgrid.conversion.dggs2geo.geohash2geo import geohash2geo
from vgrid.utils.constants import (
    OUTPUT_FORMATS,
    STRUCTURED_FORMATS,
    DGGS_TYPES,
    MIN_CELL_AREA,
)
import geopandas as gpd
from pyproj import datadir

os.environ["PROJ_LIB"] = datadir.get_data_dir()
import rasterio

min_res = DGGS_TYPES["geohash"]["min_res"]
max_res = DGGS_TYPES["geohash"]["max_res"]


def get_nearest_geohash_resolution(raster_path):
    """
    Automatically determine the optimal Geohash resolution for a given raster.

    Analyzes the raster's pixel size and determines the most appropriate Geohash resolution
    that best matches the raster's spatial resolution.

    Parameters
    ----------
    raster_path : str
        Path to the raster file to analyze.

    Returns
    -------
    tuple
        A tuple containing (cell_size, resolution) where:
        - cell_size: The calculated cell size in square meters
        - resolution: The optimal Geohash resolution level

    Examples
    --------
    >>> cell_size, resolution = get_nearest_geohash_resolution("data.tif")
    >>> print(f"Cell size: {cell_size} m², Resolution: {resolution}")
    Cell size: 1000000.0 m², Resolution: 5
    """
    with rasterio.open(raster_path) as src:
        transform = src.transform
        crs = src.crs
        pixel_width = transform.a
        pixel_height = -transform.e
        cell_size = pixel_width * pixel_height

        if crs.is_geographic:
            # Latitude of the raster center
            center_latitude = (src.bounds.top + src.bounds.bottom) / 2
            # Convert degrees to meters
            meter_per_degree_lat = 111_320  # Roughly 1 degree latitude in meters
            meter_per_degree_lon = meter_per_degree_lat * cos(radians(center_latitude))

            pixel_width_m = pixel_width * meter_per_degree_lon
            pixel_height_m = pixel_height * meter_per_degree_lat
            cell_size = pixel_width_m * pixel_height_m

    min_diff = float("inf")
    nearest_resolution = min_res

    for res in range(min_res, max_res + 1):
        _, _, avg_area, _ = geohash_metrics(res)
        if avg_area < MIN_CELL_AREA:
            break
        diff = abs(avg_area - cell_size)
        # If the difference is smaller than the current minimum, update the nearest resolution
        if diff < min_diff:
            min_diff = diff
            nearest_resolution = res
    return cell_size, nearest_resolution


def raster2geohash(raster_path, resolution=None, output_format="gpd"):
    """
    Convert raster data to Geohash DGGS format.

    Converts raster data to Geohash DGGS format with automatic resolution
    determination and multi-band support. Each pixel is assigned to a Geohash cell and
    the first sample value per cell is preserved.

    Parameters
    ----------
    raster_path : str
        Path to the raster file to convert.
    resolution : int, optional
        Geohash resolution level. If None, automatically determined based on raster pixel size.
        Valid range: 1-12.
    output_format : str, default "gpd"
        Output format. Options:
        - "gpd": Returns GeoPandas GeoDataFrame (default)
        - "csv": Returns CSV file path
        - "geojson": Returns GeoJSON file path
        - "geojson_dict": Returns GeoJSON FeatureCollection as Python dict
        - "parquet": Returns Parquet file path
        - "shapefile"/"shp": Returns Shapefile file path
        - "gpkg"/"geopackage": Returns GeoPackage file path

    Returns
    -------
    geopandas.GeoDataFrame or str or dict
        The converted data in the specified format. Each row represents a Geohash cell
        with geometry and band values from the original raster.

    Examples
    --------
    >>> # Convert with automatic resolution
    >>> result = raster2geohash("data.tif")
    >>> print(f"Converted {len(result)} Geohash cells")

    >>> # Convert with specific resolution
    >>> result = raster2geohash("data.tif", resolution=5)

    >>> # Convert to GeoJSON file
    >>> result = raster2geohash("data.tif", output_format="geojson")
    >>> print(f"Saved to: {result}")
    """
    # Step 1: Determine the nearest geohash resolution if none is provided
    if resolution is None:
        cell_size, resolution = get_nearest_geohash_resolution(raster_path)
        print(f"Cell size: {cell_size} m2")
        print(f"Nearest Geohash resolution determined: {resolution}")
    else:
        resolution = validate_geohash_resolution(resolution)

    # Open the raster file to get metadata and data
    with rasterio.open(raster_path) as src:
        raster_data = src.read()  # Read all bands
        transform = src.transform
        width, height = src.width, src.height
        band_count = src.count  # Number of bands in the raster

    # Collect band values during the pixel scan, storing the first sample per Geohash cell
    geohash_band_values = {}
    for row in range(height):
        for col in range(width):
            lon, lat = transform * (col, row)
            geohash_id = latlon2geohash(lat, lon, resolution)
            if geohash_id not in geohash_band_values:
                vals = raster_data[:, int(row), int(col)]
                geohash_band_values[geohash_id] = [
                    (v.item() if hasattr(v, "item") else v) for v in vals
                ]

    properties = []
    for geohash_id, band_values in tqdm(
        geohash_band_values.items(), desc="Converting raster to Geohash", unit=" cells"
    ):
        cell_polygon = geohash2geo(geohash_id)
        base_props = {"geohash": geohash_id, "geometry": cell_polygon}
        band_props = {f"band_{i + 1}": band_values[i] for i in range(band_count)}
        base_props.update(band_props)
        properties.append(base_props)
    gdf = gpd.GeoDataFrame(properties, geometry="geometry", crs="EPSG:4326")

    # Use centralized output utility
    base_name = os.path.splitext(os.path.basename(raster_path))[0]
    output_name = f"{base_name}2geohash" if output_format is not None else None
    return convert_to_output_format(gdf, output_format, output_name)


def raster2geohash_cli():
    parser = argparse.ArgumentParser(
        description="Convert Raster in Geographic CRS to Geohash DGGS"
    )
    parser.add_argument("-raster", type=str, required=True, help="Raster file path")

    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        required=False,
        default=None,
        help=f"Geohash resolution [{min_res}..{max_res}].",
    )

    parser.add_argument(
        "-f",
        "--output_format",
        type=str,
        choices=OUTPUT_FORMATS,
        default="gpd",
    )

    args = parser.parse_args()
    raster = args.raster
    resolution = args.resolution
    output_format = args.output_format

    if not os.path.exists(raster):
        print(f"Error: The file {raster} does not exist.")
        return

    result = raster2geohash(raster, resolution, output_format)
    if output_format in STRUCTURED_FORMATS:
        print(result)


if __name__ == "__main__":
    raster2geohash_cli()
