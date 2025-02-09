from typing import Dict, Tuple, Optional, List
import numpy as np
from dataclasses import dataclass
import os
import rasterio
import tempfile
import requests
import math
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ElevationPoint:
    """Represents a single elevation point with coordinates and height."""

    latitude: float
    longitude: float
    elevation: float  # meters above sea level


class ElevationData:
    """
    Class for managing elevation data and terrain analysis using SRTM data.
    Uses NASA's Shuttle Radar Topography Mission (SRTM) 30m resolution data
    through OpenTopography API.
    """

    def __init__(self):
        """Initialize the elevation data manager with SRTM data cache."""
        self._elevation_cache: Dict[Tuple[float, float], float] = {}
        self._data_dir = os.path.join(tempfile.gettempdir(), "srtm_cache")
        os.makedirs(self._data_dir, exist_ok=True)
        self._current_bounds = None
        self._current_dataset = None

        # Get API key from environment
        self._api_key = os.getenv("OPEN_TOPO")
        if not self._api_key:
            raise ValueError(
                "OpenTopography API key not found. Please set OPEN_TOPO in .env file"
            )

    def _get_srtm_tile_name(self, latitude: float, longitude: float) -> str:
        """
        Get the SRTM tile name for given coordinates.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            SRTM tile name (e.g., 'N37W086')
        """
        lat_base = math.floor(latitude)
        lon_base = math.floor(longitude)

        if lat_base >= 0:
            lat_str = f"N{lat_base:02d}"
        else:
            lat_str = f"S{abs(lat_base):02d}"

        if lon_base >= 0:
            lon_str = f"E{lon_base:03d}"
        else:
            lon_str = f"W{abs(lon_base):03d}"

        return f"{lat_str}{lon_str}"

    def _download_srtm_tile(self, latitude: float, longitude: float) -> str:
        """
        Download SRTM tile if not already in cache using OpenTopography API.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Path to the downloaded file
        """
        tile_name = self._get_srtm_tile_name(latitude, longitude)
        output_file = os.path.join(self._data_dir, f"{tile_name}.tif")

        if not os.path.exists(output_file):
            try:
                print(f"Downloading elevation data for {tile_name}...")

                # Calculate bounds
                lat_base = math.floor(latitude)
                lon_base = math.floor(longitude)

                # OpenTopography API URL
                url = (
                    "https://portal.opentopography.org/API/globaldem"
                    f"?demtype=SRTMGL1"
                    f"&south={lat_base}"
                    f"&north={lat_base + 1}"
                    f"&west={lon_base}"
                    f"&east={lon_base + 1}"
                    f"&outputFormat=GTiff"
                    f"&API_Key={self._api_key}"
                )

                response = requests.get(url, stream=True)
                response.raise_for_status()

                # Save to temporary file first
                temp_file = output_file + ".tmp"
                with open(temp_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # If download successful, rename to final filename
                os.rename(temp_file, output_file)
                print(f"Successfully downloaded elevation data for {tile_name}")

            except requests.exceptions.RequestException as e:
                print(f"Failed to download elevation data: {e}")
                return None
            except Exception as e:
                print(f"Error downloading elevation data: {e}")
                return None

        return output_file

    def _ensure_data_available(self, latitude: float, longitude: float):
        """
        Ensure SRTM data is available for the given coordinates.
        Downloads data if necessary.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
        """
        # Check if we already have data for these coordinates
        if self._current_bounds is not None:
            min_lat, max_lat, min_lon, max_lon = self._current_bounds
            if min_lat <= latitude < max_lat and min_lon <= longitude < max_lon:
                return

        # Download the tile if necessary
        tile_path = self._download_srtm_tile(latitude, longitude)

        if tile_path is None or not os.path.exists(tile_path):
            # If download failed, set current dataset to None
            self._current_dataset = None
            self._current_bounds = None
            return

        # Load the dataset
        if self._current_dataset is not None:
            self._current_dataset.close()

        try:
            # Open with rasterio
            self._current_dataset = rasterio.open(tile_path)

            # Update bounds
            bounds = self._current_dataset.bounds
            self._current_bounds = (
                bounds.bottom,  # min_lat
                bounds.top,  # max_lat
                bounds.left,  # min_lon
                bounds.right,  # max_lon
            )

        except Exception as e:
            print(f"Error opening elevation data: {e}")
            self._current_dataset = None
            self._current_bounds = None

    def get_elevation(self, latitude: float, longitude: float) -> float:
        """
        Get elevation for a specific coordinate using SRTM data.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Elevation in meters above sea level
        """
        # Check cache first
        cache_key = (latitude, longitude)
        if cache_key in self._elevation_cache:
            return self._elevation_cache[cache_key]

        # Ensure we have data for these coordinates
        self._ensure_data_available(latitude, longitude)

        # If we don't have a dataset (download failed), return 0
        if self._current_dataset is None:
            return 0

        try:
            # Convert coordinates to dataset coordinates
            row, col = self._current_dataset.index(longitude, latitude)
            elevation_data = self._current_dataset.read(1)
            elevation_value = float(elevation_data[row, col])

            # Handle no data value
            if elevation_value < -1000:  # Common no-data values
                elevation_value = 0

        except (IndexError, ValueError) as e:
            print(f"Error reading elevation data: {e}")
            elevation_value = 0

        # Cache the result
        self._elevation_cache[cache_key] = elevation_value
        return elevation_value

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
