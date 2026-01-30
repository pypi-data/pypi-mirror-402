"""
Raster to DGGRID Module

This module provides functionality to convert raster data to DGGRID DGGS format with automatic resolution determination and multi-band support.

Key Functions:
    raster2dggrid: Main conversion function with multiple output formats
    get_nearest_dggrid_resolution: Automatically determines optimal DGGRID resolution
    raster2dggrid_cli: Command-line interface for conversion process
"""

import os
import argparse
import json
from tqdm import tqdm
from vgrid.utils.io import convert_to_output_format
from vgrid.utils.constants import (
    OUTPUT_FORMATS,
    STRUCTURED_FORMATS,
    DGGRID_TYPES,
    MIN_CELL_AREA,
)
import geopandas as gpd
from vgrid.utils.io import (
    validate_dggrid_type,
    validate_dggrid_resolution,
    create_dggrid_instance,
)
from vgrid.stats.dggridstats import dggridstats
from vgrid.conversion.latlon2dggs import latlon2dggrid
from vgrid.conversion.dggs2geo.dggrid2geo import dggrid2geo
from vgrid.utils.geometry import geodesic_dggs_metrics
from pyproj import datadir

os.environ["PROJ_LIB"] = datadir.get_data_dir()
import rasterio
import math


def get_nearest_dggrid_resolution(dggrid_instance, dggs_type, raster_path):
    """
    Automatically determine the optimal DGGRID resolution for a given raster.

    Analyzes the raster's pixel size and determines the most appropriate DGGRID resolution
    that best matches the raster's spatial resolution for the specified DGGS type.

    Parameters
    ----------
    dggrid_instance : object
        DGGRID instance for processing.
    dggs_type : str
        DGGRID DGGS type (e.g., "ISEA7H", "ISEA4T").
    raster_path : str
        Path to the raster file to analyze.

    Returns
    -------
    tuple
        A tuple containing (cell_size, resolution) where:
        - cell_size: The calculated cell size in square meters
        - resolution: The optimal DGGRID resolution level

    Examples
    --------
    >>> cell_size, resolution = get_nearest_dggrid_resolution(instance, "ISEA7H", "data.tif")
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
            meter_per_degree_lon = meter_per_degree_lat * math.cos(
                math.radians(center_latitude)
            )

            pixel_width_m = pixel_width * meter_per_degree_lon
            pixel_height_m = pixel_height * meter_per_degree_lat
            cell_size = pixel_width_m * pixel_height_m

    min_diff = float("inf")
    min_res = int(DGGRID_TYPES[dggs_type]["min_res"])
    max_res = int(DGGRID_TYPES[dggs_type]["max_res"])
    nearest_resolution = min_res

    try:
        # Get stats with area in m^2 to compare directly with raster cell size
        grid_stats = dggridstats(dggrid_instance, dggs_type, unit="m")
        for res in range(min_res, max_res + 1):
            res_stats = grid_stats[grid_stats["resolution"] == res]
            if res_stats.empty:
                continue
            avg_area_m2 = res_stats["area_m2"].iloc[0]
            if avg_area_m2 < MIN_CELL_AREA:
                break
            diff = math.fabs(avg_area_m2 - cell_size)
            if diff < min_diff:
                min_diff = diff
                nearest_resolution = res
    except Exception:
        # Fallback to using min_res if grid stats fail
        nearest_resolution = min_res

    return cell_size, nearest_resolution


def raster2dggrid(
    dggrid_instance,
    dggs_type: str,
    raster_path,
    resolution: int | None = None,
    output_format: str = "gpd",
    split_antimeridian: bool = False,
    aggregate: bool = False,
    options=None,
):
    """
    Convert raster data to DGGRID DGGS format.

    Converts raster data to DGGRID DGGS format with automatic resolution
    determination and multi-band support. Each pixel is assigned to a DGGRID cell and
    the first sample value per cell is preserved.

    Parameters
    ----------
    dggrid_instance : object
        DGGRID instance for processing.
    dggs_type : str
        DGGRID DGGS type (e.g., "ISEA7H", "ISEA4T").
    raster_path : str
        Path to the raster file to convert.
    resolution : int, optional
        DGGRID resolution level. If None, automatically determined based on raster pixel size.
        Valid range depends on the DGGS type.
    output_format : str, default "gpd"
        Output format. Options:
        - "gpd": Returns GeoPandas GeoDataFrame (default)
        - "csv": Returns CSV file path
        - "geojson": Returns GeoJSON file path
        - "geojson_dict": Returns GeoJSON FeatureCollection as Python dict
        - "parquet": Returns Parquet file path
        - "shapefile"/"shp": Returns Shapefile file path
        - "gpkg"/"geopackage": Returns GeoPackage file path
    split_antimeridian : bool, optional
        When True, apply antimeridian fixing to the resulting polygons.
        Defaults to False when None or omitted.
    aggregate : bool, optional
        When True, aggregate the resulting polygons.
        Defaults to False when None or omitted.
    options : dict, optional
        Options to pass to grid_cell_polygons_from_cellids. 
        For example: {"densification": 2} to add densification points.
        Defaults to None.
    Returns
    -------
    geopandas.GeoDataFrame or str or dict
        The converted data in the specified format. Each row represents a DGGRID cell
        with geometry and band values from the original raster.

    Examples
    --------
    >>> # Convert with automatic resolution
    >>> result = raster2dggrid(instance, "ISEA7H", "data.tif")
    >>> print(f"Converted {len(result)} DGGRID cells")

    >>> # Convert with specific resolution
    >>> result = raster2dggrid(instance, "ISEA7H", "data.tif", resolution=5)

    >>> # Convert to GeoJSON file
    >>> result = raster2dggrid(instance, "ISEA7H", "data.tif", output_format="geojson")
    >>> print(f"Saved to: {result}")
    """
    dggs_type = validate_dggrid_type(dggs_type)

    # Auto-select resolution if not provided
    if resolution is None:
        cell_size, resolution = get_nearest_dggrid_resolution(
            dggrid_instance, dggs_type, raster_path
        )
        print(f"Cell size: {cell_size} m2")
        print(f"Nearest {dggs_type.upper()} resolution determined: {resolution}")
    else:
        resolution = validate_dggrid_resolution(dggs_type, resolution)

    # Open the raster file to get metadata and data
    with rasterio.open(raster_path) as src:
        raster_data = src.read()  # Read all bands
        transform = src.transform
        width, height = src.width, src.height
        band_count = src.count  # Number of bands in the raster

    # Collect band values during the pixel scan, storing the first sample per DGGRID cell
    dggrid_ids_band_values = {}
    for row in range(height):
        for col in range(width):
            lon, lat = transform * (col, row)
            try:
                dggrid_id = latlon2dggrid(
                    dggrid_instance, dggs_type, lat, lon, resolution
                )
                if dggrid_id not in dggrid_ids_band_values:
                    vals = raster_data[:, int(row), int(col)]
                    dggrid_ids_band_values[dggrid_id] = [
                        (v.item() if hasattr(v, "item") else v) for v in vals
                    ]
            except Exception:
                continue

    # Build GeoDataFrame as the base
    properties = []
    for dggrid_id, band_values in tqdm(
        dggrid_ids_band_values.items(),
        desc="Converting raster to DGGRID",
        unit=" cells",
    ):
        try:
            # Convert zone to geometry using dggrid2geo
            cell_polygon = dggrid2geo(
                dggrid_instance,
                dggs_type,
                dggrid_id,
                resolution,
                split_antimeridian=split_antimeridian,
                aggregate=aggregate,
                options=options,
            )

            # Get cell metrics
            if isinstance(cell_polygon, gpd.GeoDataFrame) and not cell_polygon.empty:
                cell_geom = cell_polygon.iloc[0].geometry
                centroid_lat, centroid_lon, avg_edge_len, cell_area, cell_perimeter = (
                    geodesic_dggs_metrics(cell_geom, len(cell_geom.exterior.coords) - 1)
                )
            else:
                # Fallback metrics if geometry conversion fails
                centroid_lat, centroid_lon, avg_edge_len, cell_area, cell_perimeter = (
                    0,
                    0,
                    0,
                    0,
                    0,
                )

            base_props = {
                f"dggrid_{dggs_type}": dggrid_id,
                "resolution": resolution,
                "center_lat": centroid_lat,
                "center_lon": centroid_lon,
                "avg_edge_len": avg_edge_len,
                "cell_area": cell_area,
                "cell_perimeter": cell_perimeter,
                "geometry": cell_geom
                if isinstance(cell_polygon, gpd.GeoDataFrame) and not cell_polygon.empty
                else None,
            }
            band_properties = {
                f"band_{i + 1}": band_values[i] for i in range(band_count)
            }
            base_props.update(band_properties)
            properties.append(base_props)
        except Exception:
            continue

    # Build GeoDataFrame
    gdf = gpd.GeoDataFrame(properties, geometry="geometry", crs="EPSG:4326")

    # Use centralized output utility
    base_name = os.path.splitext(os.path.basename(raster_path))[0]
    output_name = f"{base_name}2dggrid" if output_format is not None else None
    return convert_to_output_format(gdf, output_format, output_name)


def raster2dggrid_cli():
    parser = argparse.ArgumentParser(
        description="Convert Raster in Geographic CRS to DGGRID DGGS"
    )
    parser.add_argument("-raster", type=str, required=True, help="Raster file path")
    parser.add_argument(
        "-dggs",
        "--dggs_type",
        type=str,
        required=True,
        choices=DGGRID_TYPES.keys(),
        help="DGGRID type",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        required=False,
        default=None,
        help="Resolution (integer). If omitted, auto-selected",
    )
    parser.add_argument(
        "-f",
        "--output_format",
        type=str,
        choices=OUTPUT_FORMATS,
        default="gpd",
    )

    parser.add_argument(
        "-split",
        "--split_antimeridian",
        action="store_true",
        default=False,
        help="Apply antimeridian fixing to the resulting polygons",
    )
    parser.add_argument(
        "-aggregate",
        "--aggregate",
        action="store_true",
        help="Aggregate the resulting polygons",
    )
    parser.add_argument(
        "-options",
        "--options",
        type=str,
        default=None,
        help="JSON string of options to pass to grid_cell_polygons_from_cellids. "
             "Example: '{\"densification\": 2}'",
    )
    args = parser.parse_args()
    raster = args.raster
    dggs_type = args.dggs_type
    resolution = args.resolution
    output_format = args.output_format
    split_antimeridian = args.split_antimeridian
    aggregate = args.aggregate
    if not os.path.exists(raster):
        print(f"Error: The file {raster} does not exist.")
        return

    # Create DGGRID instance
    dggrid_instance = create_dggrid_instance()

    # Parse options JSON if provided
    options = None
    if args.options:
        try:
            options = json.loads(args.options)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in options: {str(e)}")
            return

    result = raster2dggrid(
        dggrid_instance,
        dggs_type,
        raster,
        resolution,
        output_format,
        split_antimeridian,
        aggregate,
        options,
    )
    if output_format in STRUCTURED_FORMATS:
        print(result)


if __name__ == "__main__":
    raster2dggrid_cli()
