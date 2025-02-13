# WISP Coverage Analysis Tool

## Project Overview
This tool is designed to create coverage maps for Wireless Internet Service Providers (WISPs) using airFiber technology. It calculates and visualizes coverage areas based on antenna locations, specifications, and real terrain data.

## Project Structure
```
wisp_coverage_tool/
│
├── src/
│   ├── __init__.py
│   ├── config/                # Configuration management
│   │   ├── __init__.py
│   │   └── logging_config.py  # Logging configuration
│   │
│   ├── utils/                 # Utility modules
│   │   ├── __init__.py
│   │   └── logger.py         # Logging implementation
│   │
│   ├── data_handling.py      # Data input/output operations
│   ├── antenna.py            # Antenna class and related functions
│   ├── coverage.py           # Coverage calculation functions
│   ├── elevation.py          # SRTM elevation data handling
│   ├── visualization.py      # Plotting and mapping functions
│   └── helpers.py            # Helper functions
│
├── tests/
│   └── __init__.py
│
├── data/
│   ├── mock_data/           # Store mock datasets
│   └── real_data/           # For actual antenna data later
│
├── examples/
│   └── demo_coverage.py     # Demo script
│
├── requirements.txt
├── .env                     # Environment variables (API keys)
└── README.md
```

## Core Components

### Antenna Class (`src/antenna.py`)
The `Antenna` class is the fundamental data structure for storing antenna information:
- Location (latitude/longitude)
- Height
- Power output
- Frequency
- Directional properties (azimuth, beam width, tilt)

### Coverage Calculations (`src/coverage.py`)
Implements core signal propagation and coverage analysis:
- Fresnel zone calculations
- Signal strength estimation using free space path loss
- Coverage area determination considering terrain
- Multiple antenna overlap analysis

### Elevation Data (`src/elevation.py`)
Handles terrain elevation data using NASA's SRTM dataset:
- Downloads and caches SRTM elevation data
- Provides elevation data for any lat/lon coordinate
- Integrates with OpenTopography API for reliable data access
- Efficient caching system for better performance

### Visualization (`src/visualization.py`)
Handles all mapping and visualization functionality:
- Base map integration using OpenStreetMap
- Coverage overlay generation
- Signal strength heat maps
- Interactive map capabilities

## Current Implementation Status

### Completed Features
- Basic project structure
- Antenna data model
- Basic visualization with mock data
- Fundamental signal calculations
- Real terrain elevation data integration using SRTM
- Elevation data caching system

### Pending Implementation
- Complete coverage calculation with terrain analysis
- Interactive visualization
- Data export functionality
- Real antenna data integration

## Development Guidelines

### Adding New Features
1. Follow the existing module structure
2. Implement new features in appropriate modules
3. Update the demo script to showcase new functionality
4. Add documentation for new features

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters and returns
- Include docstrings for all functions and classes
- Maintain consistent naming conventions

### Testing
- Add unit tests for new functionality
- Ensure mock data testing capabilities
- Validate calculations against real-world data when available

## Technical Requirements

### Dependencies
```
geopandas>=0.9.0
numpy>=1.19.0
pandas>=1.2.0
matplotlib>=3.3.0
contextily>=1.1.0
rasterio>=1.2.0
shapely>=1.7.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### API Keys
The tool requires an API key from OpenTopography to access SRTM elevation data:
1. Sign up for an API key at [OpenTopography](https://portal.opentopography.org/apidocs/)
2. Create a `.env` file in the project root
3. Add your API key:
   ```
   OPEN_TOPO=your_api_key_here
   ```

### Installation
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your `.env` file with the OpenTopography API key

## Usage Examples

### Basic Coverage Map with Real Terrain
```python
from src.antenna import Antenna
from src.elevation import ElevationData
from src.visualization import plot_coverage_map

# Initialize elevation data
elevation_data = ElevationData()

# Create antenna object
antenna = Antenna(
    name="Site1",
    longitude=-86.1091,
    latitude=38.4064,
    height=30,
    power=1000,
    frequency=5.8
)

# Generate and display coverage map with terrain consideration
plot_coverage_map([antenna], elevation_data=elevation_data)
```

## Contributing Guidelines
1. Fork the repository
2. Create a feature branch
3. Implement changes with appropriate tests
4. Submit pull request with detailed description

## Notes for LLM Development Continuation

### Recent Improvements

1. **Coverage Calculation Enhancements**
   - Implemented ITU-R P.526 model for terrain diffraction loss
   - Improved line-of-sight calculations with Fresnel zone consideration
   - Added specialized handling for different antenna types:
     - Backhaul antennas (up to 50km range)
     - Sector antennas (up to 15km range)
     - Standard antennas (up to 8km range)
   - Implemented minimum radius safeguards (500m)

2. **Visualization Improvements**
   - Added support for both backhaul and regular antenna visualization
   - Enhanced coverage polygon creation with terrain consideration
   - Improved beam pattern visualization for directional antennas
   - Added validation for coverage radius calculations

3. **Code Organization**
   - Cleaned up and optimized core functions in coverage.py
   - Enhanced error handling and logging
   - Improved type hints and documentation
   - Separated concerns between coverage calculation and visualization

### Future Development Plans

1. **Elevation Data Optimization**
   - Implement raster-based elevation data storage using GeoTIFF format
   - Create a caching system for frequently accessed elevation data
   - Add support for different resolution options (30m/90m)
   - Implement efficient tile-based data management

2. **Performance Enhancements**
   - Optimize terrain analysis algorithms
   - Implement parallel processing for coverage calculations
   - Add caching for frequently accessed calculations
   - Optimize memory usage for large coverage areas

3. **Feature Additions**
   - Add support for multiple frequency bands
   - Implement rain fade calculations
   - Add vegetation impact analysis
   - Create coverage overlap analysis tools
   - Add network capacity planning features

4. **User Interface**
   - Add interactive coverage adjustment tools
   - Implement coverage comparison views
   - Add terrain profile visualization
   - Create coverage report generation

5. **Documentation and Testing**
   - Add comprehensive API documentation
   - Create usage examples and tutorials
   - Implement automated testing suite
   - Add performance benchmarking tools

### Priority Tasks
1. Implement elevation data raster storage system
2. Add automated testing for core functions
3. Optimize coverage calculation performance
4. Enhance visualization options for different antenna types

## License
MIT License

## Contact
[Raymond Thurman](mailto:raymondthurman5@gmail.com)