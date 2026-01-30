"""
Raster to RHEALPix Module

This module provides functionality to convert raster data to RHEALPix (Rectified HEALPix) DGGS format with automatic resolution determination and multi-band support.

Key Functions:
    raster2rhealpix: Main conversion function with multiple output formats
    get_nearest_rhealpix_resolution: Automatically determines optimal RHEALPix resolution
    raster2rhealpix_cli: Command-line interface for conversion process
"""

import os
import argparse
from tqdm import tqdm
from vgrid.stats.rhealpixstats import rhealpix_metrics
from vgrid.utils.geometry import geodesic_dggs_metrics
from vgrid.utils.io import validate_rhealpix_resolution, convert_to_output_format
from vgrid.conversion.dggs2geo.rhealpix2geo import rhealpix2geo
from vgrid.utils.constants import (
    OUTPUT_FORMATS,
    STRUCTURED_FORMATS,
    DGGS_TYPES,
    MIN_CELL_AREA,
)
from math import cos, radians
from vgrid.dggs.rhealpixdggs.dggs import RHEALPixDGGS
from vgrid.dggs.rhealpixdggs.ellipsoids import WGS84_ELLIPSOID
import geopandas as gpd
from pyproj import datadir

os.environ["PROJ_LIB"] = datadir.get_data_dir()
import rasterio

E = WGS84_ELLIPSOID
rhealpix_dggs = RHEALPixDGGS(ellipsoid=E, north_square=1, south_square=3, N_side=3)
min_res = DGGS_TYPES["rhealpix"]["min_res"]
max_res = DGGS_TYPES["rhealpix"]["max_res"]


def get_nearest_rhealpix_resolution(raster_path):
    """
    Automatically determine the optimal RHEALPix resolution for a given raster.

    Analyzes the raster's pixel size and determines the most appropriate RHEALPix resolution
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
        - resolution: The optimal RHEALPix resolution level

    Examples
    --------
    >>> cell_size, resolution = get_nearest_rhealpix_resolution("data.tif")
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
        _, _, avg_area, _ = rhealpix_metrics(res)
        if avg_area < MIN_CELL_AREA:
            break
        diff = abs(avg_area - cell_size)
        # If the difference is smaller than the current minimum, update the nearest resolution
        if diff < min_diff:
            min_diff = diff
            nearest_resolution = res

    return cell_size, nearest_resolution


def raster2rhealpix(
    raster_path, resolution=None, output_format="gpd", fix_antimeridian=None
):
    """
    Convert raster data to RHEALPix DGGS format.

    Converts raster data to RHEALPix (Rectified HEALPix) DGGS format with automatic resolution
    determination and multi-band support. Each pixel is assigned to a RHEALPix cell and
    the first sample value per cell is preserved.

    Parameters
    ----------
    raster_path : str
        Path to the raster file to convert.
    resolution : int, optional
        RHEALPix resolution level. If None, automatically determined based on raster pixel size.
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
    fix_antimeridian : Antimeridian fixing method: shift, shift_balanced, shift_west, shift_east, split, none
        When True, apply antimeridian fixing to the resulting polygons.
        Defaults to False when None or omitted.

    Returns
    -------
    geopandas.GeoDataFrame or str or dict
        The converted data in the specified format. Each row represents a RHEALPix cell
        with geometry and band values from the original raster.

    Examples
    --------
    >>> # Convert with automatic resolution
    >>> result = raster2rhealpix("data.tif")
    >>> print(f"Converted {len(result)} RHEALPix cells")

    >>> # Convert with specific resolution
    >>> result = raster2rhealpix("data.tif", resolution=10)

    >>> # Convert to GeoJSON file
    >>> result = raster2rhealpix("data.tif", output_format="geojson")
    >>> print(f"Saved to: {result}")
    """
    # Step 1: Determine the nearest rhealpix resolution if none is provided
    if resolution is None:
        cell_size, resolution = get_nearest_rhealpix_resolution(raster_path)
        print(f"Cell size: {cell_size} m2")
        print(f"Nearest rHEALPix resolution determined: {resolution}")
    else:
        resolution = validate_rhealpix_resolution(resolution)

    # Open the raster file to get metadata and data
    with rasterio.open(raster_path) as src:
        raster_data = src.read()  # Read all bands
        transform = src.transform
        width, height = src.width, src.height
        band_count = src.count  # Number of bands in the raster

    # Collect band values during the pixel scan, storing the first sample per rHEALPix cell
    rhealpix_ids_band_values = {}
    for row in range(height):
        for col in range(width):
            lon, lat = transform * (col, row)
            point = (lon, lat)
            rhealpix_cell = rhealpix_dggs.cell_from_point(
                resolution, point, plane=False
            )
            rhealpix_id = str(rhealpix_cell)
            if rhealpix_id not in rhealpix_ids_band_values:
                vals = raster_data[:, int(row), int(col)]
                rhealpix_ids_band_values[rhealpix_id] = [
                    (v.item() if hasattr(v, "item") else v) for v in vals
                ]

    # Build GeoDataFrame as the base
    properties = []
    for rhealpix_id, band_values in tqdm(
        rhealpix_ids_band_values.items(),
        desc="Converting raster to rHEALPix",
        unit=" cells",
    ):
        cell_polygon = rhealpix2geo(rhealpix_id, fix_antimeridian=fix_antimeridian)
        rhealpix_uids = (rhealpix_id[0],) + tuple(map(int, rhealpix_id[1:]))
        rhealpix_cell = rhealpix_dggs.cell(rhealpix_uids)
        num_edges = 4
        if rhealpix_cell.ellipsoidal_shape() == "dart":
            num_edges = 3
        centroid_lat, centroid_lon, avg_edge_len, cell_area, cell_perimeter = (
            geodesic_dggs_metrics(cell_polygon, num_edges)
        )
        base_props = {
            "rhealpix": rhealpix_id,
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
    output_name = f"{base_name}2rhealpix" if output_format is not None else None
    return convert_to_output_format(gdf, output_format, output_name)


def raster2rhealpix_cli():
    """Command line interface for raster2rhealpix"""
    parser = argparse.ArgumentParser(
        description="Convert Raster in Geographic CRS to rHEALPix DGGS"
    )
    parser.add_argument("-raster", type=str, required=True, help="Raster file path")
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        required=False,
        default=None,
        help=f"rHEALPix resolution [{min_res}..{max_res}]. Required when topology=False, auto-calculated when topology=True",
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
        raise FileNotFoundError(f"The file {raster} does not exist.")

    result = raster2rhealpix(
        raster, resolution, output_format, fix_antimeridian=fix_antimeridian
    )
    if output_format in STRUCTURED_FORMATS:
        print(result)


if __name__ == "__main__":
    raster2rhealpix_cli()
