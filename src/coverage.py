import math
from typing import List, Tuple, Optional
import numpy as np
from .antenna import Antenna
from .elevation import ElevationData
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_free_space_path_loss(distance: float, frequency: float) -> float:
    """
    Calculate Free Space Path Loss (FSPL) in dB.

    Args:
        distance: Distance in kilometers
        frequency: Frequency in GHz

    Returns:
        Path loss in dB
    """
    # FSPL formula: 20log10(d) + 20log10(f) + 92.45
    # where d is in km and f is in GHz
    return 20 * math.log10(distance) + 20 * math.log10(frequency) + 92.45


def calculate_fresnel_zone_radius(distance: float, frequency: float, n: int = 1) -> float:
    """
    Calculate the nth Fresnel zone radius at a given point.

    Args:
        distance: Distance from transmitter in kilometers
        frequency: Frequency in GHz
        n: Fresnel zone number (default is 1 for first Fresnel zone)

    Returns:
        Radius in meters
    """
    # Convert frequency to wavelength (c = 3x10^8 m/s)
    wavelength = 0.3 / frequency  # wavelength in meters
    
    # Convert distance to meters
    d1 = distance * 1000  # first half of the path
    d2 = distance * 1000  # second half (assuming point is in middle)
    
    # Fresnel zone radius formula: r = sqrt((n * λ * d1 * d2)/(d1 + d2))
    return math.sqrt((n * wavelength * d1 * d2) / (d1 + d2))


def calculate_directional_factor(antenna: Antenna) -> float:
    """
    Calculate a coverage factor based on antenna directionality.

    Args:
        antenna: Antenna object

    Returns:
        Directional factor (1.0 means omnidirectional, >1.0 means more focused)
    """
    # For backhaul antennas, use a much higher factor
    if "backhaul" in antenna.name.lower():
        if antenna.beam_width:
            # For narrow beams, factor increases as beam width decreases
            # e.g., 5° beam = factor of 72, 10° beam = factor of 36
            factor = 360 / antenna.beam_width if antenna.beam_width > 0 else 72
            return factor
        return 72.0  # Default factor for backhaul if no beam width specified
    
    # For standard antennas, calculate based on beam width
    if antenna.beam_width and antenna.beam_width < 360:
        # More focused beam means higher factor
        # Square root relationship provides reasonable scaling
        factor = 2.0 * (360 / antenna.beam_width) ** 0.5
        return factor
    
    return 1.0  # Default for omnidirectional antennas


def check_line_of_sight(
    antenna: Antenna,
    target_lat: float,
    target_lon: float,
    target_height: float,
    elevation_data: ElevationData,
    samples: int = 100
) -> Tuple[bool, float]:
    """
    Check if there is a clear line of sight between antenna and target point.
    
    Args:
        antenna: Source antenna
        target_lat: Target latitude
        target_lon: Target longitude
        target_height: Height of target point above ground in meters
        elevation_data: ElevationData object for terrain information
        samples: Number of points to check along the path
    
    Returns:
        Tuple of (has_line_of_sight, clearance_ratio)
        clearance_ratio is the minimum ratio of actual clearance to required clearance
    """
    # Get elevation profile between points
    profile = elevation_data.get_elevation_profile(
        antenna.latitude, antenna.longitude,
        target_lat, target_lon,
        num_points=samples
    )
    
    if not profile:
        return False, 0.0
    
    # Calculate path distance in kilometers
    path_distance = calculate_distance(
        antenna.latitude, antenna.longitude,
        target_lat, target_lon
    )
    
    # Get endpoint elevations
    start_elevation = profile[0].elevation + antenna.height
    end_elevation = profile[-1].elevation + target_height
    
    # Track minimum clearance ratio
    min_clearance_ratio = float('inf')
    
    # Check each point along the path
    for i, point in enumerate(profile[1:-1], 1):
        # Calculate ratio of distance along the path (0 to 1)
        ratio = i / (len(profile) - 1)
        
        # Calculate expected height at this point (straight line)
        expected_height = start_elevation + (end_elevation - start_elevation) * ratio
        
        # Calculate Fresnel zone radius at this point
        # Use point distance from start for Fresnel calculation
        point_distance = path_distance * ratio
        fresnel_radius = calculate_fresnel_zone_radius(point_distance, antenna.frequency)
        
        # Required clearance is 60% of first Fresnel zone
        required_clearance = fresnel_radius * 0.6
        
        # Add earth curvature correction
        # Earth radius is approximately 6371 km
        # Correction = d²/2R where d is distance in same units as R
        earth_curvature = (point_distance * 1000) ** 2 / (2 * 6371000)
        
        # Calculate actual clearance above terrain
        actual_clearance = expected_height - point.elevation - earth_curvature
        
        # Update minimum clearance ratio
        if required_clearance > 0:
            clearance_ratio = actual_clearance / required_clearance
            min_clearance_ratio = min(min_clearance_ratio, clearance_ratio)
    
    # We have line of sight if all clearance ratios are >= 1
    has_line_of_sight = min_clearance_ratio >= 1
    
    return has_line_of_sight, min_clearance_ratio


def calculate_terrain_loss(clearance_ratio: float) -> float:
    """
    Calculate additional path loss due to terrain obstruction.
    
    Args:
        clearance_ratio: Ratio of actual clearance to required Fresnel zone clearance
    
    Returns:
        Additional loss in dB
    """
    if clearance_ratio >= 1.0:
        return 0.0  # No additional loss when Fresnel zone is clear
    elif clearance_ratio <= 0:
        return float('inf')  # Complete obstruction
    
    # Calculate loss based on clearance ratio
    # Uses ITU-R P.526 approximation for knife-edge diffraction
    v = -0.6 + math.sqrt(2) * (1 - clearance_ratio)
    loss = 6.9 + 20 * math.log10(math.sqrt((v - 0.1) ** 2 + 1) + v - 0.1)
    
    return max(0.0, loss)


def estimate_coverage_radius(
    antenna: Antenna,
    elevation_data: Optional[ElevationData] = None,
    min_signal_strength: float = -80
) -> float:
    """
    Estimate the maximum coverage radius for an antenna considering terrain.

    Args:
        antenna: Antenna object
        elevation_data: Optional ElevationData object for terrain analysis
        min_signal_strength: Minimum acceptable signal strength in dBm

    Returns:
        Estimated coverage radius in kilometers
    """
    # Calculate base radius from antenna parameters
    # Start with theoretical free space path loss calculation
    eirp = antenna.power  # Effective Isotropic Radiated Power in dBm
    
    # Apply antenna gain based on directional factor
    directional_factor = calculate_directional_factor(antenna)
    eirp += 10 * math.log10(directional_factor)
    
    # Maximum allowable path loss
    max_path_loss = eirp - min_signal_strength
    
    # Calculate initial radius using free space path loss formula
    # FSPL = 20log10(d) + 20log10(f) + 92.45
    # Solving for d: d = 10^((max_path_loss - 20log10(f) - 92.45)/20)
    initial_radius = 10 ** ((max_path_loss - 20 * math.log10(antenna.frequency) - 92.45) / 20)
    
    # Apply height factor adjustment
    # Higher antennas generally have better coverage
    height_factor = math.sqrt(antenna.height / 30)  # Normalize to 30m reference height
    initial_radius *= height_factor
    
    # For backhaul antennas, allow longer ranges
    if "backhaul" in antenna.name.lower():
        initial_radius = min(initial_radius * 1.5, 50.0)  # Cap at 50km
        return initial_radius
    
    # For regular antennas, consider terrain if available
    if elevation_data:
        # Sample points in different directions
        angles = np.linspace(0, 360, 36)  # Every 10 degrees
        radii = []
        
        for angle in angles:
            angle_rad = math.radians(angle)
            max_radius = initial_radius
            
            # Binary search for maximum radius with line of sight
            min_r = 0.1  # 100m minimum
            max_r = initial_radius
            
            while max_r - min_r > 0.1:  # 100m precision
                test_r = (min_r + max_r) / 2
                
                # Calculate test point location
                dx = test_r * math.cos(angle_rad) / 111.0
                dy = test_r * math.sin(angle_rad)
                test_lat = antenna.latitude + dy
                test_lon = antenna.longitude + dx / math.cos(math.radians(antenna.latitude))
                
                # Check line of sight to this point
                has_los, clearance = check_line_of_sight(
                    antenna, test_lat, test_lon,
                    5.0,  # Assume 5m receiver height
                    elevation_data
                )
                
                if has_los:
                    min_r = test_r  # Can try farther
                else:
                    max_r = test_r  # Need to try closer
            
            radii.append(min_r)
        
        # Use the median radius to avoid outliers
        final_radius = np.median(radii)
    else:
        final_radius = initial_radius
    
    # Cap the radius at reasonable values based on antenna type
    if "sector" in antenna.name.lower():
        final_radius = min(final_radius, 15.0)  # 15km max for sector antennas
    else:
        final_radius = min(final_radius, 8.0)   # 8km max for standard antennas
    
    return max(0.5, final_radius)  # Minimum 500m radius


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on the Earth's surface.

    Args:
        lat1: Latitude of the first point
        lon1: Longitude of the first point
        lat2: Latitude of the second point
        lon2: Longitude of the second point

    Returns:
        Distance in kilometers
    """
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Earth's radius in kilometers
    R = 6371

    return R * c
