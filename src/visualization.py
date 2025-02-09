from typing import List, Optional
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import numpy as np
import math

from src.antenna import Antenna
from src.coverage import estimate_coverage_radius
from src.elevation import ElevationData
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_coverage_polygon(
    ant: Antenna,
    radius_km: float,
    elevation_data: Optional[ElevationData] = None
) -> Polygon:
    """
    Create a polygon representing the coverage area of an antenna, considering terrain.

    Args:
        ant: Antenna object
        radius_km: Maximum coverage radius in kilometers
        elevation_data: Optional elevation data for terrain analysis

    Returns:
        Shapely Polygon representing the coverage area
    """
    logger.debug(f"Creating coverage polygon for antenna {ant.name} with radius {radius_km:.2f}km")

    # Get antenna base elevation
    if elevation_data:
        ant_elevation = elevation_data.get_elevation(ant.latitude, ant.longitude)
        ant_height = ant_elevation + ant.height
        logger.debug(f"Antenna {ant.name} base elevation: {ant_elevation}m, total height: {ant_height}m")
    else:
        ant_height = ant.height

    # Convert radius from km to degrees (approximate)
    # At the equator, 1 degree is approximately 111 km
    radius_deg = radius_km / 111.0

    # Sample points more densely for better terrain consideration
    num_angles = 72  # Every 5 degrees
    angles = np.linspace(0, 360, num_angles, endpoint=False)
    points = []
    center = (ant.longitude, ant.latitude)

    # Add center point
    points.append(center)

    for angle in angles:
        # Skip angles outside the beam width for directional antennas
        if ant.beam_width is not None and ant.azimuth is not None:
            angle_diff = (angle - ant.azimuth + 180) % 360 - 180
            if abs(angle_diff) > ant.beam_width / 2:
                continue

        # Convert angle to radians
        angle_rad = math.radians(angle)

        # Sample points along this direction
        distances = np.linspace(0.1, radius_km, 20)  # Sample 20 points along each direction
        max_distance = 0.1  # Minimum distance

        for distance in distances:
            # Calculate test point location
            dx = distance * math.cos(angle_rad) / 111.0
            dy = distance * math.sin(angle_rad) / 111.0
            
            # Adjust for latitude compression
            dx = dx / math.cos(math.radians(ant.latitude))
            
            test_lon = center[0] + dx
            test_lat = center[1] + dy

            if elevation_data:
                # Get elevation profile
                profile = elevation_data.get_elevation_profile(
                    ant.latitude, ant.longitude,
                    test_lat, test_lon,
                    num_points=10
                )

                if not profile:  # Skip if we couldn't get elevation data
                    logger.warning(f"Could not get elevation profile for {ant.name} at angle {angle}")
                    continue

                # Get end point elevation and add receiver height
                end_elevation = profile[-1].elevation + 5  # Assume 5m receiver height

                # Check line of sight
                has_los = True
                for i, point in enumerate(profile[1:-1], 1):
                    # Calculate ratio along the path
                    ratio = i / (len(profile) - 1)
                    
                    # Calculate expected height at this point (straight line)
                    expected_height = ant_height + (end_elevation - ant_height) * ratio
                    
                    # Calculate Fresnel zone clearance
                    wavelength = 3e8 / (ant.frequency * 1e9)  # Convert GHz to Hz
                    fresnel_radius = math.sqrt(wavelength * distance * 1000 / 4)  # in meters
                    required_clearance = fresnel_radius * 0.6  # 60% of first Fresnel zone
                    
                    # Add earth curvature correction
                    # Earth's radius is approximately 6371 km
                    earth_curvature = (distance * 1000 * ratio) ** 2 / (2 * 6371000)
                    
                    # Check if terrain blocks the path
                    if point.elevation > (expected_height - required_clearance - earth_curvature):
                        has_los = False
                        break

                if not has_los:
                    break
            
            max_distance = distance

        # Add the point at the maximum distance for this angle
        if max_distance > 0.1:  # Only add if we found a valid distance
            dx = (max_distance / 111.0) * math.cos(angle_rad) / math.cos(math.radians(ant.latitude))
            dy = (max_distance / 111.0) * math.sin(angle_rad)
            points.append((center[0] + dx, center[1] + dy))

    # Need at least 3 points to create a polygon
    if len(points) < 3:
        logger.warning(f"Not enough points to create polygon for {ant.name}, creating minimal circle")
        return Point(center).buffer(0.1 / 111.0)  # 100m radius minimum

    # Create and return the polygon
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
    elevation_data: Optional[ElevationData] = None,
    background_map: bool = True,
    save_path: Optional[str] = None,
    export_geojson: Optional[str] = None,
    unified_view: bool = True,
) -> None:
    """
    Create a coverage map visualization for the given antennas.

    Args:
        antennas: List of Antenna objects to plot
        elevation_data: Optional elevation data for terrain analysis
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

        # Create coverage area with terrain consideration
        radius_km = estimate_coverage_radius(ant, elevation_data)
        coverage = create_coverage_polygon(ant, radius_km, elevation_data)
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
        logger.debug("Adding background map")
        ctx.add_basemap(
            ax,
            source=ctx.providers.OpenStreetMap.Mapnik,
            attribution_size=8,
        )

    # Add title and legend
    plt.title("WISP Coverage Map", pad=20)
    plt.legend()

    # Remove axis labels (they're in Web Mercator coordinates)
    ax.set_axis_off()

    if save_path:
        logger.info(f"Saving coverage map to {save_path}")
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
        plt.close()

    if export_geojson:
        logger.info(f"Exporting coverage to GeoJSON: {export_geojson}")
        coverage_gdf.to_crs(epsg=4326).to_file(export_geojson, driver="GeoJSON")
