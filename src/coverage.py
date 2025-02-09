import math
from typing import List, Tuple
from .antenna import Antenna
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


def calculate_fresnel_zone_radius(
    distance: float, frequency: float, n: int = 1
) -> float:
    """
    Calculate the nth Fresnel zone radius at a given point.

    Args:
        distance: Distance from transmitter in kilometers
        frequency: Frequency in GHz
        n: Fresnel zone number (default is 1 for first Fresnel zone)

    Returns:
        Radius in meters
    """
    logger.debug(f"Calculating Fresnel zone {n} radius at distance={distance}km, frequency={frequency}GHz")
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
    if antenna.beam_width is None:
        logger.debug(f"Antenna {antenna.name} is omnidirectional, using factor=1.0")
        return 1.0
    
    # The narrower the beam, the stronger the signal in that direction
    factor = math.sqrt(360 / antenna.beam_width)
    logger.debug(f"Calculated directional factor for {antenna.name}: {factor:.2f} (beam width: {antenna.beam_width}°)")
    return factor


def estimate_coverage_radius(
    antenna: Antenna, min_signal_strength: float = -80
) -> float:
    """
    Estimate the maximum coverage radius for an antenna.
    Currently calibrated to match real-world observations of ~1.27 mile radius
    (8-mile circumference).

    Args:
        antenna: Antenna object
        min_signal_strength: Minimum acceptable signal strength in dBm

    Returns:
        Estimated coverage radius in kilometers
    """
    logger.info(f"Estimating coverage radius for antenna {antenna.name}")
    
    # Calculate base radius from 8-mile circumference
    # circumference = 2πr -> r = c/(2π)
    MILES_TO_KM = 1.60934
    CIRCUMFERENCE_MILES = 8
    BASE_RADIUS_MILES = CIRCUMFERENCE_MILES / (2 * math.pi)  # ≈ 1.27 miles
    BASE_RADIUS_KM = BASE_RADIUS_MILES * MILES_TO_KM  # ≈ 2.05 km
    
    # Apply basic adjustments based on antenna height and power
    height_factor = math.sqrt(antenna.height / 30)  # normalize to 30m reference height
    power_factor = math.sqrt(antenna.power / 1000)  # normalize to 1000W reference power
    
    logger.debug(f"Base factors for {antenna.name}:")
    logger.debug(f"- Height factor: {height_factor:.2f} (height: {antenna.height}m)")
    logger.debug(f"- Power factor: {power_factor:.2f} (power: {antenna.power}W)")
    
    # Calculate directional factor based on beam width
    directional_factor = calculate_directional_factor(antenna)
    
    # Combine all factors
    adjusted_radius = BASE_RADIUS_KM * height_factor * power_factor * directional_factor
    
    # For point-to-point antennas (very narrow beam width), extend the range
    if antenna.beam_width is not None and antenna.beam_width <= 5:  # Point-to-point threshold
        logger.info(f"Antenna {antenna.name} is point-to-point, extending range by 1.5x")
        adjusted_radius *= 1.5  # More realistic range for point-to-point
    
    logger.info(f"Final coverage radius for {antenna.name}: {adjusted_radius:.2f}km")
    return adjusted_radius
