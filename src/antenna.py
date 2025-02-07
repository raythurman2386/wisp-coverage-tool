from dataclasses import dataclass
from typing import Optional


@dataclass
class Antenna:
    """
    Class representing a WISP antenna with its specifications and location.
    """

    name: str
    longitude: float
    latitude: float
    height: float  # meters
    power: float  # watts
    frequency: float  # GHz
    azimuth: Optional[float] = None  # degrees
    beam_width: Optional[float] = None  # degrees
    tilt: Optional[float] = None  # degrees

    def __post_init__(self):
        """Validate antenna parameters after initialization."""
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if self.height <= 0:
            raise ValueError("Height must be positive")
        if self.power <= 0:
            raise ValueError("Power must be positive")
        if self.frequency <= 0:
            raise ValueError("Frequency must be positive")

        # Optional parameter validation
        if self.azimuth is not None and not 0 <= self.azimuth < 360:
            raise ValueError("Azimuth must be between 0 and 360 degrees")
        if self.beam_width is not None and not 0 < self.beam_width <= 360:
            raise ValueError("Beam width must be between 0 and 360 degrees")
        if self.tilt is not None and not -90 <= self.tilt <= 90:
            raise ValueError("Tilt must be between -90 and 90 degrees")
