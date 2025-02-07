"""
Utility functions for the WISP Coverage Tool.
"""

import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def dBm_to_watts(dbm: float) -> float:
    """
    Convert power from dBm to watts.

    Args:
        dbm: Power in dBm

    Returns:
        Power in watts
    """
    return 10 ** ((dbm - 30) / 10)


def watts_to_dBm(watts: float) -> float:
    """
    Convert power from watts to dBm.

    Args:
        watts: Power in watts

    Returns:
        Power in dBm
    """
    return 10 * math.log10(watts * 1000)
