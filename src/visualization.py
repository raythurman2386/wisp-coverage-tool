from typing import List, Optional
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
from .antenna import Antenna
from .coverage import estimate_coverage_radius


def plot_coverage_map(
    antennas: List[Antenna],
    background_map: bool = True,
    save_path: Optional[str] = None,
) -> None:
    """
    Create a coverage map visualization for the given antennas.

    Args:
        antennas: List of Antenna objects to plot
        background_map: Whether to include OpenStreetMap background
        save_path: Optional path to save the plot
    """
    # Create points and coverage circles for antennas
    points = []
    circles = []
    names = []
    for ant in antennas:
        # Create point for antenna location
        point = Point(ant.longitude, ant.latitude)
        points.append(point)
        names.append(ant.name)
        
        # Create circle for coverage area
        radius_km = estimate_coverage_radius(ant)
        # Convert km to degrees (approximate, varies with latitude)
        radius_deg = radius_km / 111.0  # at equator, 1 degree ≈ 111 km
        circle = point.buffer(radius_deg)
        circles.append(circle)

    # Create GeoDataFrame for antenna points
    points_gdf = gpd.GeoDataFrame(
        {"name": names}, geometry=points, crs="EPSG:4326"
    )
    
    # Create unified coverage area by merging all circles
    unified_coverage = unary_union(circles)
    coverage_gdf = gpd.GeoDataFrame(
        {"name": ["Total Coverage Area"]},
        geometry=[unified_coverage],
        crs="EPSG:4326"
    )

    # Convert to Web Mercator for contextily
    points_gdf = points_gdf.to_crs(epsg=3857)
    coverage_gdf = coverage_gdf.to_crs(epsg=3857)

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot unified coverage area
    coverage_gdf.plot(
        ax=ax,
        color="blue",
        alpha=0.2,
        edgecolor="blue",
        linewidth=1
    )
    
    # Plot antenna points
    points_gdf.plot(
        ax=ax,
        color="red",
        marker="^",
        markersize=100
    )

    if background_map:
        ctx.add_basemap(
            ax,
            source=ctx.providers.OpenStreetMap.Mapnik,
            zoom=12
        )

    # Add labels for antennas
    for idx, row in points_gdf.iterrows():
        plt.annotate(
            row["name"],
            xy=(row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points",
        )

    plt.title("WISP Coverage Map")

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
    else:
        plt.show()
