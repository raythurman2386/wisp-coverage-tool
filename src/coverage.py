import math
from typing import List, Tuple
from .antenna import Antenna


def calculate_free_space_path_loss(distance: float, frequency: float) -> float:
    """
    Calculate Free Space Path Loss (FSPL) in dB.

    Args:
        distance: Distance in kilometers
        frequency: Frequency in GHz

    Returns:
        Path loss in dB
    """
    return 20 * math.log10(distance) + 20 * math.log10(frequency) + 92.45


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
    wavelength = 0.3 / frequency  # wavelength in meters (c = 3x10^8 m/s)
    d1 = distance * 1000  # convert to meters
    d2 = distance * 1000  # assuming point is in the middle
    return math.sqrt((n * wavelength * d1 * d2) / (d1 + d2))


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
    # Calculate base radius from 8-mile circumference
    # circumference = 2πr -> r = c/(2π)
    MILES_TO_KM = 1.60934
    CIRCUMFERENCE_MILES = 8
    BASE_RADIUS_MILES = CIRCUMFERENCE_MILES / (2 * math.pi)  # ≈ 1.27 miles
    BASE_RADIUS_KM = BASE_RADIUS_MILES * MILES_TO_KM  # ≈ 2.05 km
    
    # Apply basic adjustments based on antenna height and power
    # These factors can be tuned based on more real-world data
    height_factor = math.sqrt(antenna.height / 30)  # normalize to 30m reference height
    power_factor = math.sqrt(antenna.power / 1000)  # normalize to 1000W reference power
    
    # Combine factors - can be adjusted based on real-world measurements
    adjusted_radius = BASE_RADIUS_KM * height_factor * power_factor
    
    return adjusted_radius
