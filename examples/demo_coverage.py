import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.antenna import Antenna
from src.visualization import plot_coverage_map
from src.coverage import estimate_coverage_radius
from src.elevation import ElevationData

# Mock antenna data for Palmyra area
mock_antenna_points = [
    # Center of Palmyra
    {
        "name": "Antenna_1",
        "lon": -86.1091,
        "lat": 38.4064,
        "height": 30,
        "power": 1000,
        "frequency": 5.8,
    },
    # North of Palmyra
    {
        "name": "Antenna_2",
        "lon": -86.1091,
        "lat": 38.4164,
        "height": 25,
        "power": 1000,
        "frequency": 5.8,
    },
    # East of Palmyra
    {
        "name": "Antenna_3",
        "lon": -86.0991,
        "lat": 38.4064,
        "height": 35,
        "power": 1000,
        "frequency": 5.8,
    },
]


def create_antennas():
    """Create antenna objects from mock data."""
    return [
        Antenna(
            name=point["name"],
            longitude=point["lon"],
            latitude=point["lat"],
            height=point["height"],
            power=point["power"],
            frequency=point["frequency"],
        )
        for point in mock_antenna_points
    ]


def analyze_coverage(antennas, elevation_data):
    """Analyze coverage for each antenna."""
    for antenna in antennas:
        # Get coverage radius
        coverage_radius = estimate_coverage_radius(antenna)

        # Get average terrain elevation in coverage area
        avg_elevation = elevation_data.get_average_elevation(
            antenna.latitude,
            antenna.longitude,
            radius_km=coverage_radius / 2,  # Sample half the coverage radius
        )

        print(f"\nAnalysis for {antenna.name}:")
        print(f"Location: ({antenna.latitude:.4f}, {antenna.longitude:.4f})")
        print(f"Height above ground: {antenna.height}m")
        print(f"Average terrain elevation: {avg_elevation:.1f}m")
        print(f"Total height above sea level: {antenna.height + avg_elevation:.1f}m")
        print(f"Estimated coverage radius: {coverage_radius:.2f}km")


def main():
    # Create antenna objects
    antennas = create_antennas()

    # Initialize elevation data
    elevation_data = ElevationData()

    # Analyze coverage for each antenna
    analyze_coverage(antennas, elevation_data)

    # Create and display coverage map
    print("\nGenerating coverage map...")
    plot_coverage_map(antennas, background_map=True)


if __name__ == "__main__":
    main()
