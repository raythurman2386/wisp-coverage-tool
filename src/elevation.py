from typing import Dict, Tuple, Optional, List
import numpy as np
from dataclasses import dataclass


@dataclass
class ElevationPoint:
    """Represents a single elevation point with coordinates and height."""

    latitude: float
    longitude: float
    elevation: float  # meters above sea level


class ElevationData:
    """
    Class for managing elevation data and terrain analysis.
    Currently uses dummy data - will be replaced with real elevation service.
    """

    def __init__(self):
        """Initialize with dummy elevation data around Palmyra, Indiana."""
        self._elevation_cache: Dict[Tuple[float, float], float] = {}
        # Center point near Palmyra, IN
        self._base_lat = 38.4064
        self._base_lon = -86.1091
        # Generate some dummy terrain with rolling hills
        self._generate_dummy_terrain()

    def _generate_dummy_terrain(self, grid_size: int = 100):
        """
        Generate dummy terrain data with rolling hills.

        Args:
            grid_size: Size of the grid for dummy data generation
        """
        # Create a grid of points
        x = np.linspace(-0.1, 0.1, grid_size)
        y = np.linspace(-0.1, 0.1, grid_size)
        X, Y = np.meshgrid(x, y)

        # Generate some rolling hills using sine waves
        base_elevation = 200  # base elevation in meters
        hills = (
            np.sin(5 * X) * np.cos(5 * Y) * 20  # rolling hills
            + np.sin(2 * X) * np.sin(2 * Y) * 30  # larger features
            + base_elevation  # base elevation
        )

        # Store in cache
        for i in range(grid_size):
            for j in range(grid_size):
                lat = self._base_lat + y[i]
                lon = self._base_lon + x[j]
                self._elevation_cache[(lat, lon)] = float(hills[i, j])

    def get_elevation(self, latitude: float, longitude: float) -> float:
        """
        Get elevation for a specific coordinate.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Elevation in meters above sea level
        """
        # Check if point is in cache
        if (latitude, longitude) in self._elevation_cache:
            return self._elevation_cache[(latitude, longitude)]

        # If not in cache, interpolate from nearby points
        return self._interpolate_elevation(latitude, longitude)

    def _interpolate_elevation(self, latitude: float, longitude: float) -> float:
        """
        Interpolate elevation from nearby cached points.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Interpolated elevation in meters
        """
        # Find nearest cached point
        nearest_lat = (
            self._base_lat + round((latitude - self._base_lat) / 0.002) * 0.002
        )
        nearest_lon = (
            self._base_lon + round((longitude - self._base_lon) / 0.002) * 0.002
        )

        # Return elevation of nearest point
        return self._elevation_cache.get(
            (nearest_lat, nearest_lon),
            200.0,  # default elevation if point is outside our dummy data range
        )

    def get_elevation_profile(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        num_points: int = 100,
    ) -> List[ElevationPoint]:
        """
        Get elevation profile between two points.

        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Ending latitude
            end_lon: Ending longitude
            num_points: Number of points to sample

        Returns:
            List of ElevationPoint objects along the path
        """
        # Generate points along the path
        lats = np.linspace(start_lat, end_lat, num_points)
        lons = np.linspace(start_lon, end_lon, num_points)

        # Get elevation for each point
        return [
            ElevationPoint(
                latitude=lat, longitude=lon, elevation=self.get_elevation(lat, lon)
            )
            for lat, lon in zip(lats, lons)
        ]

    def get_average_elevation(
        self,
        center_lat: float,
        center_lon: float,
        radius_km: float,
        num_points: int = 16,
    ) -> float:
        """
        Get average elevation in a circular area.

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers
            num_points: Number of points to sample

        Returns:
            Average elevation in meters
        """
        # Convert radius to degrees (approximate)
        radius_deg = radius_km / 111.0  # rough conversion

        # Sample points in a circle
        angles = np.linspace(0, 2 * np.pi, num_points)
        elevations = []

        for angle in angles:
            lat = center_lat + radius_deg * np.cos(angle)
            lon = center_lon + radius_deg * np.sin(angle)
            elevations.append(self.get_elevation(lat, lon))

        return sum(elevations) / len(elevations)
