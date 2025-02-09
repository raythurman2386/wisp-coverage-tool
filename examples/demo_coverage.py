import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.antenna import Antenna
from src.visualization import plot_coverage_map
from src.coverage import estimate_coverage_radius
from src.elevation import ElevationData
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Mock antenna data for Palmyra area
mock_antenna_points = [
    # Center of Palmyra - Omnidirectional hub
    {
        "name": "Hub-Omni",
        "lon": -86.1091,
        "lat": 38.4064,
        "height": 40,
        "power": 1000,
        "frequency": 5.8,
        # Omnidirectional - no beam_width or azimuth needed
    },
    # North coverage - 90-degree sector array
    {
        "name": "North-90W",
        "lon": -86.1191,
        "lat": 38.4264,
        "height": 30,
        "power": 1000,
        "frequency": 5.8,
        "beam_width": 90,
        "azimuth": 270,  # Facing West
    },
    {
        "name": "North-90E",
        "lon": -86.1191,
        "lat": 38.4264,
        "height": 30,
        "power": 1000,
        "frequency": 5.8,
        "beam_width": 90,
        "azimuth": 90,  # Facing East
    },
    # East coverage - 30-degree sectors
    {
        "name": "East-30N",
        "lon": -86.0891,
        "lat": 38.4064,
        "height": 35,
        "power": 1000,
        "frequency": 5.8,
        "beam_width": 30,
        "azimuth": 330,  # Facing Northwest
    },
    {
        "name": "East-30S",
        "lon": -86.0891,
        "lat": 38.4064,
        "height": 35,
        "power": 1000,
        "frequency": 5.8,
        "beam_width": 30,
        "azimuth": 210,  # Facing Southwest
    },
    # Point-to-Point backhaul links
    {
        "name": "PTP-West",
        "lon": -86.1391,
        "lat": 38.4064,
        "height": 45,
        "power": 1000,
        "frequency": 5.8,
        "beam_width": 5,
        "azimuth": 90,  # Pointing East to hub
    },
    {
        "name": "PTP-South",
        "lon": -86.1091,
        "lat": 38.3864,
        "height": 45,
        "power": 1000,
        "frequency": 5.8,
        "beam_width": 5,
        "azimuth": 0,  # Pointing North to hub
    },
]


def create_antennas():
    """Create antenna objects from mock data."""
    logger.info("Creating antenna objects from mock data")
    antennas = []

    for point in mock_antenna_points:
        logger.debug(f"Creating antenna: {point['name']}")
        antenna = Antenna(
            name=point["name"],
            longitude=point["lon"],
            latitude=point["lat"],
            height=point["height"],
            power=point["power"],
            frequency=point["frequency"],
            beam_width=point.get("beam_width"),  # Optional
            azimuth=point.get("azimuth"),  # Optional
        )
        antennas.append(antenna)

    logger.info(f"Created {len(antennas)} antenna objects")
    return antennas


def analyze_coverage(antennas, elevation_data):
    """Analyze coverage for each antenna."""
    logger.info("Analyzing coverage for all antennas")

    for antenna in antennas:
        logger.debug(f"Analyzing antenna: {antenna.name}")

        # Get coverage radius
        coverage_radius = estimate_coverage_radius(antenna)

        # Get average terrain elevation in coverage area
        avg_elevation = elevation_data.get_average_elevation(
            antenna.latitude,
            antenna.longitude,
            radius_km=coverage_radius / 2,  # Sample half the coverage radius
        )

        logger.info(f"\nAnalysis for {antenna.name}:")
        logger.info(f"Location: ({antenna.latitude:.4f}, {antenna.longitude:.4f})")
        logger.info(f"Height above ground: {antenna.height}m")
        logger.info(f"Average terrain elevation: {avg_elevation:.1f}m")
        logger.info(f"Total height above sea level: {antenna.height + avg_elevation:.1f}m")
        logger.info(f"Estimated coverage radius: {coverage_radius:.2f}km")


def main():
    logger.info("Starting WISP Coverage Tool Demo")

    # Create antenna objects
    antennas = create_antennas()

    # Initialize elevation data
    logger.info("Initializing elevation data")
    elevation_data = ElevationData()

    # Analyze coverage for each antenna
    analyze_coverage(antennas, elevation_data)

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    logger.info(f"Created output directory: {output_dir}")

    # Create and display coverage map with unified coverage
    logger.info("\nGenerating coverage map and exporting data...")
    plot_coverage_map(
        antennas,
        background_map=True,
        save_path=output_dir / "coverage_map.png",
        export_geojson=output_dir / "coverage_area.geojson",
        unified_view=True,
    )

    logger.info("\nDemo completed successfully!")
    logger.info("Coverage map has been saved to 'output/coverage_map.png'")
    logger.info("Coverage area GeoJSON has been exported to 'output/coverage_area.geojson'")
    logger.info("The GeoJSON file can be imported into mapping tools like QGIS, Mapbox, or Leaflet")


if __name__ == "__main__":
    main()
