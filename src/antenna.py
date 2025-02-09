from dataclasses import dataclass
from typing import Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


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
        logger.debug(f"Validating antenna parameters for {self.name}")

        if not -180 <= self.longitude <= 180:
            msg = f"Longitude must be between -180 and 180 degrees, got {self.longitude}"
            logger.error(msg)
            raise ValueError(msg)

        if not -90 <= self.latitude <= 90:
            msg = f"Latitude must be between -90 and 90 degrees, got {self.latitude}"
            logger.error(msg)
            raise ValueError(msg)

        if self.height <= 0:
            msg = f"Height must be positive, got {self.height}"
            logger.error(msg)
            raise ValueError(msg)

        if self.power <= 0:
            msg = f"Power must be positive, got {self.power}"
            logger.error(msg)
            raise ValueError(msg)

        if self.frequency <= 0:
            msg = f"Frequency must be positive, got {self.frequency}"
            logger.error(msg)
            raise ValueError(msg)

        # Optional parameter validation
        if self.azimuth is not None and not 0 <= self.azimuth < 360:
            msg = f"Azimuth must be between 0 and 360 degrees, got {self.azimuth}"
            logger.error(msg)
            raise ValueError(msg)

        if self.beam_width is not None and not 0 < self.beam_width <= 360:
            msg = f"Beam width must be between 0 and 360 degrees, got {self.beam_width}"
            logger.error(msg)
            raise ValueError(msg)

        if self.tilt is not None and not -90 <= self.tilt <= 90:
            msg = f"Tilt must be between -90 and 90 degrees, got {self.tilt}"
            logger.error(msg)
            raise ValueError(msg)

        logger.info(
            f"Successfully created antenna {self.name} at ({self.latitude}, {self.longitude})"
        )
        if self.beam_width is not None:
            logger.info(
                f"Antenna {self.name} configured with {self.beam_width}° beam width, azimuth: {self.azimuth}°"
            )
