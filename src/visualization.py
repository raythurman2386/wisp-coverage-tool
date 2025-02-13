from typing import List, Optional
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid
import numpy as np
import math
from tqdm import tqdm

from src.antenna import Antenna
from src.elevation import ElevationData
from src.coverage import check_line_of_sight, estimate_coverage_radius
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
    logger.debug(f"Creating coverage polygon for {ant.name} with radius {radius_km}km")
    
    # Ensure we have a valid radius
    if radius_km <= 0:
        logger.warning(f"Invalid radius {radius_km}km for {ant.name}, using minimum radius")
        radius_km = 0.5  # 500m minimum radius
    
    # Calculate the center point
    center = (ant.longitude, ant.latitude)
    
    # Get antenna base elevation and height
    if elevation_data:
        base_elevation = elevation_data.get_elevation(ant.latitude, ant.longitude)
        if base_elevation is not None:
            total_height = base_elevation + ant.height
            logger.debug(f"Antenna {ant.name} base elevation: {base_elevation}m, total height: {total_height}m")
        else:
            total_height = ant.height
            logger.warning(f"Could not get elevation for {ant.name}, using antenna height only")
    else:
        total_height = ant.height

    # For backhaul antennas, create a narrow beam pattern
    is_backhaul = "backhaul" in ant.name.lower()
    
    if is_backhaul:
        # Use antenna's azimuth and beam width to create a narrow beam pattern
        azimuth = ant.azimuth if ant.azimuth is not None else 0
        beam_width = ant.beam_width if ant.beam_width is not None else 10  # Default 10° beam width
        
        points = []
        points.append(center)  # Start with center point
        
        # Calculate angles for the beam edges
        left_angle = (azimuth - beam_width/2) % 360
        right_angle = (azimuth + beam_width/2) % 360
        
        # Convert radius to degrees (approximate)
        radius_deg = radius_km / 111.0
        
        # Add points along the arc at maximum distance
        num_arc_points = 5
        angles = np.linspace(left_angle, right_angle, num_arc_points)
        
        for angle in angles:
            angle_rad = math.radians(angle)
            
            # Calculate point coordinates
            dx = radius_deg * math.cos(angle_rad) / math.cos(math.radians(ant.latitude))
            dy = radius_deg * math.sin(angle_rad)
            point = (center[0] + dx, center[1] + dy)
            
            # Check terrain if available
            if elevation_data:
                target_lat = ant.latitude + dy
                target_lon = ant.longitude + dx
                has_los, _ = check_line_of_sight(
                    ant, target_lat, target_lon, total_height,
                    elevation_data, samples=10
                )
                if has_los:
                    points.append(point)
            else:
                points.append(point)
        
        # Create and return the beam polygon if we have enough points
        if len(points) >= 3:
            try:
                return Polygon(points)
            except Exception as e:
                logger.warning(f"Failed to create backhaul beam polygon for {ant.name}: {str(e)}")
        
        # Fallback to a minimal directional indicator
        return Point(center).buffer(0.2/111.0)  # 200m radius minimum
    
    # For regular antennas, create a coverage area considering terrain
    points = []
    points.append(center)  # Start with center point
    
    # Calculate points around the circumference
    num_points = 72  # Every 5 degrees
    angles = np.linspace(0, 360, num_points, endpoint=False)
    
    for angle in angles:
        angle_rad = math.radians(angle)
        
        # Convert to degrees for coordinate calculation
        radius_deg = radius_km / 111.0
        
        # Calculate point coordinates
        dx = radius_deg * math.cos(angle_rad) / math.cos(math.radians(ant.latitude))
        dy = radius_deg * math.sin(angle_rad)
        point = (center[0] + dx, center[1] + dy)
        
        # Check terrain if available
        if elevation_data:
            target_lat = ant.latitude + dy
            target_lon = ant.longitude + dx
            has_los, _ = check_line_of_sight(
                ant, target_lat, target_lon, total_height,
                elevation_data, samples=10
            )
            if has_los:
                points.append(point)
        else:
            points.append(point)
    
    # Create the coverage polygon if we have enough points
    if len(points) >= 3:
        try:
            return Polygon(points)
        except Exception as e:
            logger.warning(f"Failed to create polygon for {ant.name}: {str(e)}")
    
    # Fallback to a minimal circle
    logger.warning(f"Not enough points to create polygon for {ant.name}, creating minimal circle")
    return Point(center).buffer(0.5/111.0)  # 500m radius minimum


def create_simple_beam_polygon(ant: Antenna, radius_deg: float) -> Polygon:
    """
    Create a simple beam polygon for backhaul antennas when terrain analysis fails.
    
    Args:
        ant: Antenna object
        radius_deg: Maximum coverage radius in degrees
        
    Returns:
        Shapely Polygon representing a simple beam coverage area
    """
    points = []
    points.append((ant.longitude, ant.latitude))  # Center point
    
    # Use 3 points to create a simple triangular beam
    beam_width = ant.beam_width if ant.beam_width else 4
    half_beam = beam_width / 2
    
    # Calculate angles
    start_angle = (ant.azimuth - half_beam) % 360
    end_angle = (ant.azimuth + half_beam) % 360
    
    # Add points at the maximum radius
    for angle in [start_angle, end_angle]:
        angle_rad = math.radians(angle)
        dx = radius_deg * math.cos(angle_rad) / math.cos(math.radians(ant.latitude))
        dy = radius_deg * math.sin(angle_rad)
        points.append((ant.longitude + dx, ant.latitude + dy))
    
    # Close the polygon
    points.append((ant.longitude, ant.latitude))
    
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

    logger.debug("Calculating coverage areas for each antenna")
    for ant in tqdm(antennas, desc="Processing antennas"):
        names.append(ant.name)
        points.append(Point(ant.longitude, ant.latitude))

        coverage = create_coverage_polygon(ant, estimate_coverage_radius(ant), elevation_data)

        # Validate and fix the coverage polygon if needed
        if not coverage.is_valid:
            logger.warning(f"Invalid coverage polygon for antenna {ant.name}. Attempting to fix...")
            coverage = make_valid(coverage)

        if coverage.is_valid:
            # Add a small buffer to handle precision issues (1e-8 degrees ≈ 1mm)
            coverage = coverage.buffer(1e-8)
            coverage_areas.append(coverage)
        else:
            logger.error(f"Could not create valid coverage polygon for antenna {ant.name}")
            continue

    # Create GeoDataFrame for antenna points
    antenna_gdf = gpd.GeoDataFrame({"name": names, "geometry": points}, crs="EPSG:4326")  # WGS84

    if unified_view and coverage_areas:
        logger.debug("Creating unified coverage area")
        try:
            # Create unified coverage area with error handling
            unified_coverage = unary_union(coverage_areas)
            if not unified_coverage.is_valid:
                logger.warning("Invalid unified coverage. Attempting to fix...")
                unified_coverage = make_valid(unified_coverage)

            coverage_gdf = gpd.GeoDataFrame(
                {"name": ["Total Coverage Area"]},
                geometry=[unified_coverage],
                crs="EPSG:4326",  # WGS84
            )
        except Exception as e:
            logger.error(f"Failed to create unified coverage: {str(e)}")
            # Fall back to individual coverage areas
            unified_view = False

    if not unified_view:
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
