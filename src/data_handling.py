import json
from typing import List, Dict, Any
import pandas as pd
from .antenna import Antenna


def load_antenna_data(file_path: str) -> List[Antenna]:
    """
    Load antenna data from a JSON or CSV file.

    Args:
        file_path: Path to the data file

    Returns:
        List of Antenna objects
    """
    if file_path.endswith(".json"):
        with open(file_path, "r") as f:
            data = json.load(f)
            return [Antenna(**ant_data) for ant_data in data]
    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
        return [Antenna(**row) for row in df.to_dict("records")]
    else:
        raise ValueError("Unsupported file format. Use JSON or CSV.")


def save_antenna_data(antennas: List[Antenna], file_path: str) -> None:
    """
    Save antenna data to a file.

    Args:
        antennas: List of Antenna objects
        file_path: Path to save the data
    """
    data = [
        {
            "name": ant.name,
            "longitude": ant.longitude,
            "latitude": ant.latitude,
            "height": ant.height,
            "power": ant.power,
            "frequency": ant.frequency,
            "azimuth": ant.azimuth,
            "beam_width": ant.beam_width,
            "tilt": ant.tilt,
        }
        for ant in antennas
    ]

    if file_path.endswith(".json"):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    elif file_path.endswith(".csv"):
        pd.DataFrame(data).to_csv(file_path, index=False)
    else:
        raise ValueError("Unsupported file format. Use JSON or CSV.")
