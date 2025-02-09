import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.antenna import Antenna
from src.visualization import plot_coverage_map
from src.elevation import ElevationData
from src.utils.logger import setup_logger

from typing import List
import os

def main():
    """Main demo function."""
    # Set up logging
    logger = setup_logger(__name__)
    logger.info("Starting WISP Coverage Tool Demo")

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Initialize elevation data
    elevation_data = ElevationData()

    # Define antenna configurations for a realistic WISP network
    antennas = [
        # Main Tower 1 - Palmyra Central Hub
        {
            "name": "Palmyra-Hub-Omni",
            "lon": -86.1091,
            "lat": 38.3864,
            "height": 45,  # Tall tower for central distribution
            "power": 1000,
            "frequency": 2.4,  # 2.4GHz for better penetration
            "beam_width": 360,
            "direction": 0,
            "type": "omni"
        },
        # Sector antennas on main hub
        {
            "name": "Palmyra-Sector-North",
            "lon": -86.1091,
            "lat": 38.3864,
            "height": 43,
            "power": 1000,
            "frequency": 5.8,
            "beam_width": 90,
            "direction": 0,
            "type": "sector"
        },
        {
            "name": "Palmyra-Sector-East",
            "lon": -86.1091,
            "lat": 38.3864,
            "height": 43,
            "power": 1000,
            "frequency": 5.8,
            "beam_width": 90,
            "direction": 90,
            "type": "sector"
        },
        {
            "name": "Palmyra-Sector-South",
            "lon": -86.1091,
            "lat": 38.3864,
            "height": 43,
            "power": 1000,
            "frequency": 5.8,
            "beam_width": 90,
            "direction": 180,
            "type": "sector"
        },
        {
            "name": "Palmyra-Sector-West",
            "lon": -86.1091,
            "lat": 38.3864,
            "height": 43,
            "power": 1000,
            "frequency": 5.8,
            "beam_width": 90,
            "direction": 270,
            "type": "sector"
        },
        # Secondary Tower - New Salisbury
        {
            "name": "NewSalisbury-Hub-Omni",
            "lon": -86.1556,
            "lat": 38.3147,
            "height": 40,
            "power": 1000,
            "frequency": 2.4,
            "beam_width": 360,
            "direction": 0,
            "type": "omni"
        },
        # Sectors on New Salisbury tower
        {
            "name": "NewSalisbury-Sector-NE",
            "lon": -86.1556,
            "lat": 38.3147,
            "height": 38,
            "power": 1000,
            "frequency": 5.8,
            "beam_width": 90,
            "direction": 45,
            "type": "sector"
        },
        {
            "name": "NewSalisbury-Sector-SE",
            "lon": -86.1556,
            "lat": 38.3147,
            "height": 38,
            "power": 1000,
            "frequency": 5.8,
            "beam_width": 90,
            "direction": 135,
            "type": "sector"
        },
        # Remote Tower - Corydon
        {
            "name": "Corydon-Hub-Omni",
            "lon": -86.1225,
            "lat": 38.2120,
            "height": 35,
            "power": 1000,
            "frequency": 2.4,
            "beam_width": 360,
            "direction": 0,
            "type": "omni"
        },
        # Backhaul Links
        {
            "name": "Palmyra-Backhaul-South",
            "lon": -86.1091,
            "lat": 38.3864,
            "height": 45,
            "power": 1500,
            "frequency": 5.8,
            "beam_width": 5,
            "direction": 170,
            "type": "ptp"
        },
        {
            "name": "NewSalisbury-Backhaul-North",
            "lon": -86.1556,
            "lat": 38.3147,
            "height": 42,
            "power": 1500,
            "frequency": 5.8,
            "beam_width": 5,
            "direction": 350,
            "type": "ptp"
        },
        # Client Distribution Points
        {
            "name": "Palmyra-East-Relay",
            "lon": -86.0891,
            "lat": 38.3864,
            "height": 25,
            "power": 800,
            "frequency": 5.8,
            "beam_width": 120,
            "direction": 90,
            "type": "sector"
        },
        {
            "name": "Palmyra-West-Relay",
            "lon": -86.1291,
            "lat": 38.3864,
            "height": 25,
            "power": 800,
            "frequency": 5.8,
            "beam_width": 120,
            "direction": 270,
            "type": "sector"
        }
    ]

    # Create Antenna objects
    antenna_objects: List[Antenna] = []
    for config in antennas:
        antenna = Antenna(
            name=config["name"],
            latitude=config["lat"],
            longitude=config["lon"],
            height=config["height"],
            power=config["power"],
            frequency=config["frequency"],
            beam_width=config["beam_width"],
            azimuth=config["direction"]  # Use direction as azimuth
        )
        antenna_objects.append(antenna)

    # Generate coverage maps
    plot_coverage_map(
        antennas=antenna_objects,
        elevation_data=elevation_data,
        background_map=True,
        save_path=output_dir / "coverage_unified.png",
        export_geojson=output_dir / "coverage_unified.geojson",
        unified_view=True,
    )

    plot_coverage_map(
        antennas=antenna_objects,
        elevation_data=elevation_data,
        background_map=True,
        save_path=output_dir / "coverage_individual.png",
        export_geojson=output_dir / "coverage_individual.geojson",
        unified_view=False,
    )

    logger.info("Coverage maps have been generated in the output directory")
    logger.info("The GeoJSON files can be imported into mapping tools like QGIS, Mapbox, or Leaflet")

if __name__ == "__main__":
    main()
