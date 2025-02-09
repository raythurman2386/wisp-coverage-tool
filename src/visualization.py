from typing import List, Optional
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import numpy as np
import math
from .antenna import Antenna
from .coverage import estimate_coverage_radius
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_coverage_polygon(ant: Antenna, radius_km: float) -> Polygon:
    """
    Create a polygon representing the coverage area of an antenna.

    Args:
        ant: Antenna object
        radius_km: Coverage radius in kilometers

    Returns:
        Shapely Polygon representing the coverage area
    """
    logger.debug(f"Creating coverage polygon for antenna {ant.name} with radius {radius_km:.2f}km")

    # Convert radius from km to degrees (approximate)
    # At the equator, 1 degree is approximately 111 km
    radius_deg = radius_km / 111.0

    if ant.beam_width is None or ant.azimuth is None:
        # Omnidirectional antenna - create a circle
        logger.debug(f"Creating circular coverage for omnidirectional antenna {ant.name}")
        circle = Point(ant.longitude, ant.latitude).buffer(radius_deg)
        return circle

    # For directional antennas, create a sector
    logger.debug(
        f"Creating sector coverage for directional antenna {ant.name} "
        f"(beam width: {ant.beam_width}°, azimuth: {ant.azimuth}°)"
    )
    points = []
    center = (ant.longitude, ant.latitude)

    # Calculate start and end angles for the sector
    half_beam = ant.beam_width / 2
    start_angle = (ant.azimuth - half_beam) % 360
    end_angle = (ant.azimuth + half_beam) % 360

    # Add center point
    points.append(center)

    # Add points along the arc
    num_points = 32  # Number of points to approximate the arc
    if start_angle <= end_angle:
        angles = np.linspace(start_angle, end_angle, num_points)
    else:
        # Handle case where sector crosses 0/360 degrees
        logger.debug(f"Sector for {ant.name} crosses 0/360° boundary")
        angles = np.concatenate(
            [
                np.linspace(start_angle, 360, num_points // 2),
                np.linspace(0, end_angle, num_points // 2),
            ]
        )

    for angle in angles:
        # Convert angle to radians for math functions
        angle_rad = math.radians(angle)

        # Calculate the point position
        dx = radius_deg * math.cos(angle_rad)
        dy = radius_deg * math.sin(angle_rad)

        # Adjust for latitude compression
        dx = dx / math.cos(math.radians(ant.latitude))

        points.append((center[0] + dx, center[1] + dy))

    # Close the polygon
    points.append(center)

    return Polygon(points)


def export_coverage_geojson(
    antennas: List[Antenna],
    output_path: str,
) -> None:
    """
    Export the unified coverage area as a GeoJSON file.

    Args:
        antennas: List of Antenna objects
        output_path: Path to save the GeoJSON file
    """
    logger.info(f"Exporting unified coverage area to {output_path}")

    # Create coverage areas for antennas
    coverage_areas = []

    for ant in antennas:
        logger.debug(f"Calculating coverage area for antenna {ant.name}")
        # Create coverage area
        radius_km = estimate_coverage_radius(ant)
        coverage = create_coverage_polygon(ant, radius_km)
        coverage_areas.append(coverage)

    # Create unified coverage area
    logger.debug("Creating unified coverage area from all antenna coverages")
    unified_coverage = unary_union(coverage_areas)

    # Create GeoDataFrame with proper CRS
    coverage_gdf = gpd.GeoDataFrame(
        {"name": ["Total Coverage Area"]},
        geometry=[unified_coverage],
        crs="EPSG:4326",  # WGS84
    )

    # Export to GeoJSON
    logger.info("Saving coverage area as GeoJSON")
    coverage_gdf.to_file(output_path, driver="GeoJSON")
    logger.info(f"Successfully exported coverage area to {output_path}")


def plot_coverage_map(
    antennas: List[Antenna],
    background_map: bool = True,
    save_path: Optional[str] = None,
    export_geojson: Optional[str] = None,
    unified_view: bool = True,
) -> None:
    """
    Create a coverage map visualization for the given antennas.

    Args:
        antennas: List of Antenna objects to plot
        background_map: Whether to include OpenStreetMap background
        save_path: Optional path to save the plot
        export_geojson: Optional path to export coverage as GeoJSON
        unified_view: Whether to show unified coverage area instead of individual polygons
    """
    logger.info("Generating coverage map")
    logger.debug(f"Processing {len(antennas)} antennas")

    # Create points and coverage areas for antennas
    points = []
    coverage_areas = []
    names = []

    for ant in antennas:
        logger.debug(f"Processing antenna {ant.name}")
        # Create point for antenna location
        point = Point(ant.longitude, ant.latitude)
        points.append(point)
        names.append(ant.name)

        # Create coverage area
        radius_km = estimate_coverage_radius(ant)
        coverage = create_coverage_polygon(ant, radius_km)
        coverage_areas.append(coverage)

    # Create GeoDataFrame for antenna points
    antenna_gdf = gpd.GeoDataFrame({"name": names, "geometry": points}, crs="EPSG:4326")  # WGS84

    if unified_view:
        logger.debug("Creating unified coverage area")
        # Create unified coverage area
        unified_coverage = unary_union(coverage_areas)
        coverage_gdf = gpd.GeoDataFrame(
            {"name": ["Total Coverage Area"]},
            geometry=[unified_coverage],
            crs="EPSG:4326",  # WGS84
        )
    else:
        logger.debug("Using individual coverage areas")
        # Use individual coverage areas
        coverage_gdf = gpd.GeoDataFrame(
            {"name": names, "geometry": coverage_areas}, crs="EPSG:4326"  # WGS84
        )

    # Convert to Web Mercator for proper display with contextily
    logger.debug("Converting coordinate systems to Web Mercator")
    antenna_gdf = antenna_gdf.to_crs(epsg=3857)
    coverage_gdf = coverage_gdf.to_crs(epsg=3857)

    # Create the plot
    logger.debug("Creating plot")
    fig, ax = plt.subplots(figsize=(15, 15))

    # Plot coverage areas with transparency
    coverage_gdf.plot(ax=ax, alpha=0.3, color="blue", edgecolor="blue", linewidth=1)

    # Plot antenna points
    antenna_gdf.plot(ax=ax, color="red", marker="^", markersize=100, label="Antennas")

    if background_map:
        logger.debug("Adding OpenStreetMap background")
        # Set the extent of the map to cover all antennas with some padding
        bounds = coverage_gdf.total_bounds
        ax.set_xlim(bounds[0] - 1000, bounds[2] + 1000)
        ax.set_ylim(bounds[1] - 1000, bounds[3] + 1000)

        # Add the background map
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, attribution=False)

    # Add labels for antennas
    logger.debug("Adding antenna labels")
    for idx, row in antenna_gdf.iterrows():
        plt.annotate(
            row["name"],
            xy=(row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points",
        )

    # Add legend and title
    plt.title("WISP Coverage Map")
    plt.legend()

    # Remove axis labels as they're not meaningful with the background map
    ax.set_axis_off()

    # Export GeoJSON if requested
    if export_geojson:
        logger.info(f"Exporting coverage area to GeoJSON: {export_geojson}")
        # Export the WGS84 version for compatibility
        coverage_gdf_wgs84 = coverage_gdf.to_crs(epsg=4326)
        coverage_gdf_wgs84.to_file(export_geojson, driver="GeoJSON")

    if save_path:
        logger.info(f"Saving coverage map to: {save_path}")
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
    else:
        logger.debug("Displaying coverage map")
        plt.show()
