# WISP Coverage Analysis Tool

## Project Overview
This tool is designed to create coverage maps for Wireless Internet Service Providers (WISPs) using airFiber technology. It calculates and visualizes coverage areas based on antenna locations, specifications, and terrain data.

## Project Structure
```
wisp_coverage_tool/
│
├── src/
│   ├── __init__.py
│   ├── data_handling.py      # Data input/output operations
│   ├── antenna.py            # Antenna class and related functions
│   ├── coverage.py           # Coverage calculation functions
│   ├── elevation.py          # Elevation data handling
│   ├── visualization.py      # Plotting and mapping functions
│   └── utils.py              # Utility functions
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

### Pending Implementation
- Terrain analysis integration
- Complete coverage calculation
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

## Future Development Priorities

### Phase 1: Core Functionality
- [ ] Implement terrain analysis
- [ ] Complete coverage calculation algorithm
- [ ] Add validation for antenna parameters
- [ ] Implement basic data export

### Phase 2: Enhanced Features
- [ ] Add interactive visualization
- [ ] Implement weather impact analysis
- [ ] Add batch processing capabilities
- [ ] Create coverage optimization suggestions

### Phase 3: User Interface
- [ ] Develop web interface
- [ ] Add real-time calculation capabilities
- [ ] Implement user data management
- [ ] Create reporting functionality

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

## Usage Examples

### Basic Coverage Map
```python
from src.antenna import Antenna
from src.visualization import plot_coverage_map

# Create antenna object
antenna = Antenna(
    name="Site1",
    longitude=-86.1091,
    latitude=38.4064,
    height=30,
    power=1000,
    frequency=5.8
)

# Generate and display coverage map
plot_coverage_map([antenna])
```

## Contributing Guidelines
1. Fork the repository
2. Create a feature branch
3. Implement changes with appropriate tests
4. Submit pull request with detailed description

## Notes for LLM Development Continuation

### Project Context
1. This tool is designed for WISP (Wireless Internet Service Provider) coverage analysis in Palmyra, Indiana
2. Coverage calculations are calibrated to real-world observations:
   - Coverage area: 8-mile circumference
   - Base radius: 4 miles
   - Adjustments made for antenna height and power
   - Reference configuration: 30m height, 1000W power
3. Current implementation uses mock elevation data centered around Palmyra coordinates:
   - Base latitude: 38.4064
   - Base longitude: -86.1091

### Development Priorities
1. Coverage Calculation Refinements:
   - Incorporate terrain effects on signal propagation
   - Add line-of-sight analysis using elevation data
   - Consider atmospheric effects and weather conditions
   - Implement frequency-specific propagation models
   - Add support for different antenna types and patterns

2. Elevation Data Integration:
   - Replace mock elevation data with real terrain data
   - Implement efficient elevation data caching
   - Add terrain profile visualization
   - Consider using SRTM or similar elevation data sources

3. Visualization Enhancements:
   - Add coverage strength heat maps
   - Implement terrain profile views
   - Add support for different map providers
   - Include coverage overlap analysis visualization
   - Add export options for coverage maps

4. Data Management:
   - Implement proper elevation data storage
   - Add support for batch antenna processing
   - Create data validation and cleaning tools
   - Add export/import functionality for antenna configurations

### Code Style Guidelines
1. Follow PEP 8 standards (black formatter is configured)
2. Use type hints for all function parameters and returns
3. Maintain modular structure as established
4. Keep computation-heavy functions separate from visualization
5. Document all public functions and classes

### Important Technical Details
1. Coverage Calculation:
   ```python
   CIRCUMFERENCE_MILES = 8
   BASE_RADIUS_MILES = CIRCUMFERENCE_MILES / (2 * math.pi)  # ≈ 1.27 miles
   BASE_RADIUS_KM = BASE_RADIUS_MILES * 1.60934  # ≈ 2.05 km
   height_factor = math.sqrt(antenna.height / 30)
   power_factor = math.sqrt(antenna.power / 1000)
   ```

2. Elevation Data Structure:
   - Uses a grid-based system with interpolation
   - Current grid size: 100x100 points
   - Elevation range: ~200m base with ±50m variation

3. Visualization System:
   - Uses GeoPandas for geographic data handling
   - Matplotlib for plotting
   - OpenStreetMap for base maps
   - Coverage circles use Shapely for geometry

### Testing Requirements
1. Add unit tests for:
   - Coverage calculations
   - Elevation data handling
   - Antenna parameter validation
   - Data import/export functions
2. Include integration tests for:
   - End-to-end coverage analysis
   - Map generation
   - Data processing workflows

### Known Limitations
1. Current elevation data is simulated
2. Coverage calculation is simplified
3. No consideration of obstacles
4. Weather effects not implemented
5. Limited antenna pattern support

### Future Integration Points
1. Real elevation data services
2. Weather data APIs
3. Antenna pattern databases
4. Coverage validation tools
5. Report generation system

### Performance Considerations
1. Cache elevation data for frequently accessed regions
2. Optimize coverage calculations for batch processing
3. Consider using numpy for intensive calculations
4. Implement proper data structure for spatial queries
5. Monitor memory usage with large datasets

Remember to maintain backward compatibility when implementing new features and document any breaking changes appropriately.

## License
[Add appropriate license information]

## Contact
[Add contact information]