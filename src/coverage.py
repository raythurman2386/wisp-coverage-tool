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
    logger.debug(f"Calculating FSPL for distance={distance}km, frequency={frequency}GHz")
    path_loss = 20 * math.log10(distance) + 20 * math.log10(frequency) + 92.45
    logger.debug(f"Calculated path loss: {path_loss:.2f}dB")
    return path_loss


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
    logger.debug(
        f"Calculating Fresnel zone {n} radius at distance={distance}km, frequency={frequency}GHz"
    )
    wavelength = 0.3 / frequency  # wavelength in meters (c = 3x10^8 m/s)
    d1 = distance * 1000  # convert to meters
    d2 = distance * 1000  # assuming point is in the middle
    radius = math.sqrt((n * wavelength * d1 * d2) / (d1 + d2))
    logger.debug(f"Calculated Fresnel zone radius: {radius:.2f}m")
    return radius


def calculate_directional_factor(antenna: Antenna) -> float:
    """
    Calculate a coverage factor based on antenna directionality.

    Args:
        antenna: Antenna object

    Returns:
        Directional factor (1.0 means omnidirectional, >1.0 means more focused)
    """
    # For backhaul antennas, return a much higher factor to represent their focused beam
    if "backhaul" in antenna.name.lower():
        logger.debug(f"Backhaul antenna detected: {antenna.name}")
        # Use beam width to calculate a more accurate directional factor
        # Narrower beam width means more focused power
        if antenna.beam_width:
            # For a 10-degree beam width, this gives factor of about 36
            # For a 5-degree beam width, this gives factor of about 72
            factor = 360 / antenna.beam_width if antenna.beam_width > 0 else 72
            logger.debug(
                f"Backhaul directional factor: {factor:.2f} (beam width: {antenna.beam_width}°)"
            )
            return factor
        return 72.0  # Default factor for backhaul if no beam width specified

    # For standard antennas, use the original calculation
    if antenna.beam_width and antenna.beam_width < 360:
        # More focused beam means higher factor
        factor = 2.0 * (360 / antenna.beam_width) ** 0.5
        logger.debug(
            f"Standard antenna directional factor: {factor:.2f} (beam width: {antenna.beam_width}°)"
        )
        return factor
    return 1.0  # Omnidirectional


def check_line_of_sight(
    antenna: Antenna,
    target_lat: float,
    target_lon: float,
    target_height: float,
    elevation_data: ElevationData,
    samples: int = 100,
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
    # Get elevation points along the path
    points = elevation_data.get_elevation_profile(
        antenna.latitude, antenna.longitude, target_lat, target_lon, samples
    )

    # Calculate distances from antenna to each point
    distances = []
    total_distance = 0
    prev_point = points[0]

    for point in points[1:]:
        dist = (
            math.sqrt(
                (point.latitude - prev_point.latitude) ** 2
                + (point.longitude - prev_point.longitude) ** 2
            )
            * 111
        )  # Convert degrees to km (approximate)
        total_distance += dist
        distances.append(total_distance)
        prev_point = point

    # Calculate the line of sight path
    antenna_height = antenna.height + points[0].elevation
    target_height = target_height + points[-1].elevation

    # Linear interpolation of heights along the path
    line_of_sight = np.linspace(antenna_height, target_height, len(points))

    # Calculate Fresnel zone clearance required at each point
    clearances = []
    min_clearance_ratio = float("inf")

    for i, point in enumerate(points[1:-1], 1):
        # Calculate Fresnel zone radius at this point
        distance = distances[i - 1]
        fresnel_radius = calculate_fresnel_zone_radius(distance, antenna.frequency)

        # Required clearance is 0.6 times the first Fresnel zone radius
        required_clearance = fresnel_radius * 0.6

        # Actual clearance is the difference between line of sight and terrain
        actual_clearance = line_of_sight[i] - point.elevation

        # Calculate clearance ratio
        clearance_ratio = actual_clearance / required_clearance
        clearances.append(clearance_ratio)

        if clearance_ratio < min_clearance_ratio:
            min_clearance_ratio = clearance_ratio

    # We have line of sight if all clearance ratios are >= 1
    has_line_of_sight = min_clearance_ratio >= 1

    logger.debug(f"Line of sight check from {antenna.name} to ({target_lat}, {target_lon}):")
    logger.debug(f"- Minimum clearance ratio: {min_clearance_ratio:.2f}")
    logger.debug(f"- Has line of sight: {has_line_of_sight}")

    return has_line_of_sight, min_clearance_ratio


def calculate_terrain_loss(clearance_ratio: float) -> float:
    """
    Calculate additional path loss due to terrain obstruction.

    Args:
        clearance_ratio: Ratio of actual clearance to required Fresnel zone clearance

    Returns:
        Additional loss in dB
    """
    if clearance_ratio >= 1:
        return 0
    elif clearance_ratio <= 0:
        return float("inf")
    else:
        # Simplified knife-edge diffraction model
        # Loss increases as clearance ratio decreases
        return -20 * math.log10(clearance_ratio)


def estimate_coverage_radius(
    antenna: Antenna,
    elevation_data: Optional[ElevationData] = None,
    min_signal_strength: float = -80,
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
    logger.info(f"Estimating coverage radius for antenna {antenna.name}")

    # Special handling for backhaul antennas
    is_backhaul = "backhaul" in antenna.name.lower()

    if is_backhaul:
        # For backhaul, use free space path loss calculation to estimate range
        # Typically backhaul links can maintain connection at lower signal strengths
        backhaul_min_signal = -90  # dBm, backhaul radios can usually work with weaker signals

        # Calculate maximum theoretical range based on FSPL formula
        # FSPL = 20log10(d) + 20log10(f) + 92.45
        # Solving for d: d = 10^((EIRP - min_signal - 92.45 - 20log10(f))/20)
        eirp = antenna.power + 10 * math.log10(
            calculate_directional_factor(antenna)
        )  # Effective radiated power
        max_path_loss = eirp - backhaul_min_signal
        theoretical_range = 10 ** (
            (max_path_loss - 92.45 - 20 * math.log10(antenna.frequency)) / 20
        )

        logger.debug(f"Backhaul theoretical range for {antenna.name}: {theoretical_range:.2f}km")
        return min(theoretical_range, 50.0)  # Cap at 50km for practical purposes

    # For non-backhaul antennas, use the original calculation
    # Calculate base radius from 8-mile circumference
    MILES_TO_KM = 1.60934
    CIRCUMFERENCE_MILES = 8
    BASE_RADIUS_MILES = CIRCUMFERENCE_MILES / (2 * math.pi)
    BASE_RADIUS_KM = BASE_RADIUS_MILES * MILES_TO_KM

    # Apply basic adjustments based on antenna height and power
    height_factor = math.sqrt(antenna.height / 30)  # normalize to 30m reference height
    power_factor = math.sqrt(antenna.power / 1000)  # normalize to 1000W reference power
    directional_factor = calculate_directional_factor(antenna)

    # Calculate initial radius without terrain
    initial_radius = BASE_RADIUS_KM * height_factor * power_factor * directional_factor
    logger.debug(f"Initial radius estimate for {antenna.name}: {initial_radius:.2f}km")

    if elevation_data is None:
        return initial_radius

    # Get antenna base elevation
    antenna_base_elevation = elevation_data.get_elevation(antenna.latitude, antenna.longitude)
    if antenna_base_elevation is None:  # Failed to get elevation data
        logger.warning(f"Could not get elevation data for {antenna.name}, using initial radius")
        return initial_radius

    antenna_height = antenna_base_elevation + antenna.height
    logger.debug(
        f"Antenna {antenna.name} base elevation: {antenna_base_elevation}m, total height: {antenna_height}m"
    )

    # Sample points in different directions
    angles = np.linspace(0, 360, 36)  # Every 10 degrees
    radii = []

    for angle in angles:
        # Convert angle to radians
        rad = math.radians(angle)

        # Try different distances with more granular sampling
        distances = np.linspace(
            0.1, initial_radius * 1.2, 30
        )  # Test 30 points from 100m to 120% of initial radius
        max_distance = 0.1  # Minimum 100m radius

        for distance in distances:
            # Calculate test point location
            dlat = distance * math.cos(rad) / 111  # Approx km per degree
            dlon = distance * math.sin(rad) / (111 * math.cos(math.radians(antenna.latitude)))

            test_lat = antenna.latitude + dlat
            test_lon = antenna.longitude + dlon

            # Get elevation profile
            profile = elevation_data.get_elevation_profile(
                antenna.latitude, antenna.longitude, test_lat, test_lon, num_points=20
            )

            if not profile:  # Skip if we couldn't get elevation data
                logger.warning(
                    f"Could not get elevation profile for {antenna.name} at angle {angle}"
                )
                continue

            # Get end point elevation and add receiver height
            end_elevation = profile[-1].elevation + 5  # Assume 5m receiver height

            # Check if we have a clear path
            has_los = True

            # Calculate Fresnel zone radius at midpoint
            wavelength = 3e8 / (antenna.frequency * 1e9)  # Convert GHz to Hz
            fresnel_radius = math.sqrt(wavelength * distance * 1000 / 4)  # in meters

            # Check each point along the path
            for i, point in enumerate(profile[1:-1], 1):  # Skip first and last points
                # Calculate ratio along the path
                ratio = i / (len(profile) - 1)

                # Calculate expected height at this point (straight line)
                expected_height = antenna_height + (end_elevation - antenna_height) * ratio

                # Calculate required clearance (60% of first Fresnel zone)
                required_clearance = fresnel_radius * 0.6

                # Add earth curvature correction
                # Earth's radius is approximately 6371 km
                earth_curvature = (distance * 1000 * ratio) ** 2 / (2 * 6371000)

                # Check if terrain blocks the path
                if point.elevation > (expected_height - required_clearance - earth_curvature):
                    has_los = False
                    break

            if has_los:
                # Calculate path loss
                path_loss = calculate_free_space_path_loss(distance, antenna.frequency)
                received_power = antenna.power - path_loss

                # Update max distance if signal is strong enough
                if received_power >= min_signal_strength:
                    max_distance = distance
                else:
                    break
            else:
                break

        radii.append(max_distance)
        logger.debug(f"Maximum distance at {angle}°: {max_distance:.2f}km")

    # Use the median radius as our final estimate
    final_radius = np.median(radii)
    logger.info(f"Final coverage radius for {antenna.name}: {final_radius:.2f}km")

    return final_radius
