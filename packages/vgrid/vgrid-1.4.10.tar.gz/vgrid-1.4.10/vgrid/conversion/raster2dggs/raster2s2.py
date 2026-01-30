"""
Raster to S2 Module

This module provides functionality to convert raster data to S2 DGGS format with automatic resolution determination and multi-band support.

Key Functions:
    raster2s2: Main conversion function with multiple output formats
    get_nearest_s2_resolution: Automatically determines optimal S2 resolution
    raster2s2_cli: Command-line interface for conversion process
"""

import os
import argparse
from tqdm import tqdm
import rasterio
from vgrid.dggs import s2
from vgrid.stats.s2stats import s2_metrics
from vgrid.utils.geometry import geodesic_dggs_metrics
from math import cos, radians
from vgrid.utils.io import validate_s2_resolution, convert_to_output_format
from vgrid.utils.constants import (
    OUTPUT_FORMATS,
    STRUCTURED_FORMATS,
    DGGS_TYPES,
    MIN_CELL_AREA,
)
import geopandas as gpd
from pyproj import datadir
from vgrid.conversion.dggs2geo.s22geo import s22geo

os.environ["PROJ_LIB"] = datadir.get_data_dir()
min_res = DGGS_TYPES["s2"]["min_res"]
max_res = DGGS_TYPES["s2"]["max_res"]


def get_nearest_s2_resolution(raster_path):
    """
    Automatically determine the optimal S2 resolution for a given raster.

    Analyzes the raster's pixel size and determines the most appropriate S2 resolution
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
        - resolution: The optimal S2 resolution level

    Examples
    --------
    >>> cell_size, resolution = get_nearest_s2_resolution("data.tif")
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
    # Check resolutions from 0 to 15
    nearest_resolution = min_res

    for res in range(min_res, max_res + 1):
        _, _, avg_area, _ = s2_metrics(res)
        if avg_area < MIN_CELL_AREA:
            break
        diff = abs(avg_area - cell_size)
        # If the difference is smaller than the current minimum, update the nearest resolution
        if diff < min_diff:
            min_diff = diff
            nearest_resolution = res

    return cell_size, nearest_resolution


def raster2s2(raster_path, resolution=None, output_format="gpd", fix_antimeridian=None):
    """
    Convert raster data to S2 DGGS format.

    Converts raster data to S2 DGGS format with automatic resolution
    determination and multi-band support. Each pixel is assigned to an S2 cell and
    the first sample value per cell is preserved.

    Parameters
    ----------
    raster_path : str
        Path to the raster file to convert.
    resolution : int, optional
        S2 resolution level. If None, automatically determined based on raster pixel size.
        Valid range: 0-30.
    output_format : str, default "gpd"
        Output format. Options:
        - "gpd": Returns GeoPandas GeoDataFrame (default)
        - "csv": Returns CSV file path
        - "geojson": Returns GeoJSON file path
        - "geojson_dict": Returns GeoJSON FeatureCollection as Python dict
        - "parquet": Returns Parquet file path
        - "shapefile"/"shp": Returns Shapefile file path
        - "gpkg"/"geopackage": Returns GeoPackage file path
    fix_antimeridian : str, optional
        Antimeridian fixing method: shift, shift_balanced, shift_west, shift_east, split, none
        Defaults to None when omitted.
    Returns
    -------
    geopandas.GeoDataFrame or str or dict
        The converted data in the specified format. Each row represents an S2 cell
        with geometry and band values from the original raster.

    Examples
    --------
    >>> # Convert with automatic resolution
    >>> result = raster2s2("data.tif")
    >>> print(f"Converted {len(result)} S2 cells")

    >>> # Convert with specific resolution
    >>> result = raster2s2("data.tif", resolution=10)

    >>> # Convert to GeoJSON file
    >>> result = raster2s2("data.tif", output_format="geojson")
    >>> print(f"Saved to: {result}")
    """
    # Step 1: Determine the nearest s2 resolution if none is provided
    if resolution is None:
        cell_size, resolution = get_nearest_s2_resolution(raster_path)
        print(f"Cell size: {cell_size} m2")
        print(f"Nearest S2 resolution determined: {resolution}")
    else:
        resolution = validate_s2_resolution(resolution)
    # Open the raster file to get metadata and data
    with rasterio.open(raster_path) as src:
        raster_data = src.read()  # Read all bands
        transform = src.transform
        width, height = src.width, src.height
        band_count = src.count  # Number of bands in the raster

    # Collect band values during the pixel scan, storing the first sample per S2 cell
    s2_tokens_band_values = {}
    for row in range(height):
        for col in range(width):
            lon, lat = transform * (col, row)
            lat_lng = s2.LatLng.from_degrees(lat, lon)
            s2_id = s2.CellId.from_lat_lng(lat_lng)
            s2_id = s2_id.parent(resolution)
            s2_token = s2.CellId.to_token(s2_id)
            if s2_token not in s2_tokens_band_values:
                vals = raster_data[:, int(row), int(col)]
                s2_tokens_band_values[s2_token] = [
                    (v.item() if hasattr(v, "item") else v) for v in vals
                ]

    # Build GeoDataFrame as the base
    properties = []
    for s2_token, band_values in tqdm(
        s2_tokens_band_values.items(), desc="Converting raster to S2", unit=" cells"
    ):
        cell_polygon = s22geo(s2_token, fix_antimeridian=fix_antimeridian)
        num_edges = 4
        centroid_lat, centroid_lon, avg_edge_len, cell_area, cell_perimeter = (
            geodesic_dggs_metrics(cell_polygon, num_edges)
        )
        base_props = {
            "s2": s2_token,
            "resolution": resolution,
            "center_lat": centroid_lat,
            "center_lon": centroid_lon,
            "avg_edge_len": avg_edge_len,
            "cell_area": cell_area,
            "cell_perimeter": cell_perimeter,
            "geometry": cell_polygon,
        }
        band_properties = {f"band_{i + 1}": band_values[i] for i in range(band_count)}
        base_props.update(band_properties)
        properties.append(base_props)
    # Build GeoDataFrame
    gdf = gpd.GeoDataFrame(properties, geometry="geometry", crs="EPSG:4326")

    # Use centralized output utility
    base_name = os.path.splitext(os.path.basename(raster_path))[0]
    output_name = f"{base_name}2s2" if output_format is not None else None
    return convert_to_output_format(gdf, output_format, output_name)


def raster2s2_cli():
    parser = argparse.ArgumentParser(
        description="Convert Raster in Geographic CRS to S2 DGGS"
    )
    parser.add_argument("-raster", type=str, required=True, help="Raster file path")

    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        required=False,
        default=None,
        help=f"S2 resolution [{min_res}..{max_res}]",
    )

    parser.add_argument(
        "-f",
        "--output_format",
        type=str,
        choices=OUTPUT_FORMATS,
        default="gpd",
    )

    parser.add_argument(
        "-fix",
        "--fix_antimeridian",
        type=str,
        choices=[
            "shift",
            "shift_balanced",
            "shift_west",
            "shift_east",
            "split",
            "none",
        ],
        default=None,
        help="Antimeridian fixing method: shift, shift_balanced, shift_west, shift_east, split, none",
    )
    args = parser.parse_args()
    raster = args.raster
    resolution = args.resolution
    output_format = args.output_format
    fix_antimeridian = args.fix_antimeridian
    if not os.path.exists(raster):
        print(f"Error: The file {raster} does not exist.")
        return

    result = raster2s2(
        raster, resolution, output_format, fix_antimeridian=fix_antimeridian
    )
    if output_format in STRUCTURED_FORMATS:
        print(result)


if __name__ == "__main__":
    raster2s2_cli()
