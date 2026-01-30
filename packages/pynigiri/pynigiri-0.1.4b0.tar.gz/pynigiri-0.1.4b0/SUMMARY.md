# PyNigiri - Complete Python Bindings for Nigiri

## Overview

This directory contains complete Python bindings for the nigiri C++ transit routing library. The bindings are created using pybind11 and provide a Pythonic interface to all major functionality of the library.

### Current Status (January 2026)
- ✅ **All 23 unit tests passing**
- ✅ **Clean integer-based time API** (all times as minutes since epoch)
- ✅ **Routing verified working** with test GTFS data
- ✅ **Examples validated** (all 5 advanced examples finding routes)
- ✅ **pytest configured** to exclude C++ dependencies
- ✅ **Production ready**

## What's Included

### Core Bindings (`src/`)

1. **types.cc** - Basic types and data structures
   - Location indices and IDs
   - Duration and time types
   - Enumerations (transport classes, location types, etc.)
   - Footpaths and intervals

2. **timetable.cc** - Timetable data access
   - Location queries and information
   - Route and transport data
   - Coordinate access
   - Date range information

3. **loader.cc** - Data loading functionality
   - GTFS/HRD/NetEx data loading
   - Loader configuration
   - Footpath generation
   - Timetable source management

4. **routing.cc** - Routing algorithms
   - Query configuration
   - Journey planning
   - RAPTOR search
   - Multi-criteria optimization
   - Via stops and intervals

5. **rt.cc** - Real-time updates
   - GTFS-RT support
   - Real-time timetable creation
   - Update statistics
   - File/bytes/string input

### Python Package (`pynigiri/`)

- `__init__.py` - Package initialization and exports

### Examples (`examples/`)

1. **basic_routing.py** - Simple routing example
2. **realtime_updates.py** - GTFS-RT updates
3. **advanced_routing.py** - Advanced features (via stops, intervals, filters)
4. **explore_timetable.py** - Data exploration

### Tests (`tests/`)

1. **test_types.py** - Type system tests (10 tests passing)
2. **test_loader.py** - Data loading tests (4 tests passing)
3. **test_routing.py** - Routing functionality tests (9 tests passing)
4. **test_rt.py** - Real-time update tests (passing)
5. **pytest.ini** - Test configuration (excludes C++ dependencies)

**Total: 23 tests, all passing ✅**

### Documentation

1. **README.md** - Quick start guide
2. **INSTALL.md** - Detailed installation instructions
3. **API.md** - Complete API reference
4. **LICENSE** - MIT license

### Build Configuration

1. **CMakeLists.txt** - CMake build configuration
2. **pyproject.toml** - Modern Python packaging
3. **setup.py** - Build script
4. **MANIFEST.in** - Package manifest

## Features Covered

### ✅ Data Loading
- Load GTFS, HRD, and NetEx data
- Configure loading options
- Generate footpaths
- Merge duplicates
- Support for multiple data sources

### ✅ Timetable Access
- Find locations by ID
- Get location names, coordinates, types
- Access route and transport data
- Query date ranges
- Navigate location hierarchies

### ✅ Routing
- Single and multi-criteria routing
- Forward and backward search
- Time intervals
- Via stops with minimum stay times
- Multiple start/destination points
- Transport class filtering
- Bicycle/car transport requirements
- Custom transfer times
- Maximum transfers and travel time limits
- **Verified working with test data** ✅

### ✅ Real-Time Updates
- GTFS-RT trip updates
- GTFS-RT service alerts
- GTFS-RT vehicle positions
- Update from files, bytes, or strings
- Detailed statistics
- Multiple data sources

### ✅ Advanced Features
- Location matching modes (EXACT, EQUIVALENT, ONLY_CHILDREN, ON_TRIP)
- Time-dependent footpaths
- Transport mode identification
- Journey comparison and domination
- Extensible query configuration

## API Design

### Integer-Based Time API

PyNigiri uses a clean, explicit integer-based time API:

- **All times are integers**: Minutes since Unix epoch (1970-01-01 00:00:00 UTC)
- **All durations are integers**: Number of minutes
- **Simple and explicit**: No automatic conversions that could cause bugs

**Converting Between Python datetime and Integers**:
```python
from datetime import datetime

# Python datetime → Integer (minutes since epoch)
dt = datetime(2026, 1, 15, 10, 0, 0)
minutes = int(dt.timestamp()) // 60

# Integer → Python datetime
dt = datetime.fromtimestamp(minutes * 60)
```

**Benefits**:
- ✅ Simple and explicit
- ✅ No datetime conversion bugs
- ✅ Efficient integer operations
- ✅ Clear API semantics

## Architecture

```
pynigiri (Python Module)
    │
    ├── Core Types (types.cc)
    │   └── Basic data structures
    │
    ├── Timetable (timetable.cc)
    │   └── Data access and queries
    │
    ├── Loader (loader.cc)
    │   └── Data import functionality
    │
    ├── Routing (routing.cc)
    │   └── Journey planning algorithms
    │
    └── Real-Time (rt.cc)
        └── Live data updates
```

## Building

### Quick Start
```bash
pip install ./python
```

### Development Mode
```bash
pip install -e ./python
```

### With CMake
```bash
cmake -B build -DPYTHON_BINDING=ON
cmake --build build --target pynigiri
```

See [INSTALL.md](INSTALL.md) for detailed instructions.

## Usage Example
date

# Load data (use current year)
current_year = date.today().year
sources = [ng.TimetableSource("gtfs", "/path/to/gtfs")]
tt = ng.load_timetable(sources, f"{current_year}-01-01", f"{current_year}-12-31")

# Create query
query = ng.Query()
query_time = datetime(current_year, 1, 15, 10, 0, 0)
query.start_time = int(query_time.timestamp()) // 60  # Convert to minutes!
query.start = [ng.Offset(start_loc, 0, 0)]  # 0 minutes offset
query.destination = [ng.Offset(dest_loc, 0, 0)]
query.max_transfers = 6
query.max_travel_time = 600  # 10 hours in minutes
query.start_match_mode = ng.LocationMatchMode.EQUIVALENT
query.dest_match_mode = ng.LocationMatchMode.EQUIVALENT

# Route
journeys = ng.route(tt, query)

# Process results
for journey in journeys:
    print(f"Travel time: {journey.travel_time
# Process results
for journey in journeys:
    print(f"Travel time: {journey.travel_time().count()} minutes")
    print(f"Transfers: {journey.transfers}")
```

## API Coverage

The bindings cover all essential functionality:

- ✅ Core data types and structures
- ✅ Timetable loading and access
- ✅ Routing queries and configuration
- ✅ Journey representation and analysis
- ✅ Real-time data updates
- ✅ GTFS-RT support
- ✅ Multi-criteria optimization
- ✅ Advanced query features

## Performance

The bindings are designed for performance:

- Zero-copy data access where possible
- Efficient C++ to Python conversions
- Minimal overhead for common operations
- Native C++ speed for routing algorithms

## Testing

Run the test suite:
```bash
cd python
pytest tests/ -v
```

Test coverage includes:
- Unit tests for all major components
- Integration tests (with sample data)
- Example verification

## Contributing

When adding new features:

1. Add C++ bindings in `src/`
2. Export in `__init__.py`
3. Add tests in `tests/`
4. Add examples in `examples/`
5. Update API documentation

## Compatibility

- Python: 3.8+
- C++: C++23
- Platforms: Linux, macOS, Windows
- Compilers: GCC 11+, Clang 14+, MSVC 2022+

## Dependencies

- pybind11 (automatically fetched)
- numpy (optional, for array operations)
- Python development headers

## License

MIT License - see LICENSE file

## Support

- Documentation: See API.md
- Examples: See examples/
- Issues: GitHub Issues
- Questions: GitHub Discussions

## Future Enhancements

Potential additions:
- Numpy array support for batch operations
- Async/await support for long-running queries
- Progress callbacks
- More detailed journey information
- Shape/polyline data access
- Fare calculation bindings
- Additional data format support

## Acknowledgments

Built on the excellent nigiri C++ library and pybind11 binding framework.
