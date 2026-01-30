# PyNigiri - Python Bindings for Nigiri Transit Routing Library

Complete Python bindings for the [nigiri](https://github.com/motis-project/nigiri) C++ transit routing library.

## Status

✅ **Production Ready** - All core functionality is available and tested.
- ✅ 23 unit tests passing
- ✅ Clean integer-based time API
- ✅ Routing verified working with test GTFS data

## Features

- **Data Loading**: Load GTFS, GTFS-RT, HRD, and NeTEx transit data
- **Routing**: Fast RAPTOR-based public transit routing
- **Real-time Updates**: Apply GTFS-RT trip updates and alerts
- **All Transport Types**: Support for all public transit modes (bus, train, tram, ferry, etc.)

## Building

The bindings are built as part of the main nigiri build system:

```bash
cd nigiri
cmake -B build -DPYTHON_BINDING=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON
cmake --build build --target pynigiri -j8
```

The compiled module will be at: `build/python/pynigiri.cpython-*.so`

## Usage

```python
import sys
sys.path.insert(0, 'build/python')
import pynigiri as ng
from datetime import datetime, date

# Load GTFS data (use current year for your data)
current_year = date.today().year
sources = [ng.TimetableSource("gtfs", "/path/to/gtfs")]
timetable = ng.load_timetable(sources, f"{current_year}-01-01", f"{current_year}-12-31")

# Find locations
start_loc = timetable.find_location("STATION_A_ID")
dest_loc = timetable.find_location("STATION_B_ID")

# Create routing query
query = ng.Query()

# Convert datetime to minutes since epoch
query_time = datetime(current_year, 1, 15, 10, 0, 0)
query.start_time = int(query_time.timestamp()) // 60

# Set start/destination with integer offsets (0 minutes offset)
query.start = [ng.Offset(start_loc, 0, 0)]
query.destination = [ng.Offset(dest_loc, 0, 0)]
query.max_transfers = 6
query.max_travel_time = 600  # 10 hours in minutes
query.start_match_mode = ng.LocationMatchMode.EQUIVALENT
query.dest_match_mode = ng.LocationMatchMode.EQUIVALENT

# Run routing
journeys = ng.route(timetable, query)

# Process results
for journey in journeys:
    print(f"Transfers: {journey.transfers}")
    print(f"Travel time: {journey.travel_time()} minutes")
    for leg in journey.legs:
        # Use getattr for 'from' (Python keyword)
        from_loc = getattr(leg, 'from')
        from_name = timetable.get_location_name(from_loc)
        to_name = timetable.get_location_name(leg.to)
        
        # Convert minute timestamps to datetime for display
        dep_time = datetime.fromtimestamp(leg.dep_time * 60)
        arr_time = datetime.fromtimestamp(leg.arr_time * 60)
        print(f"  {from_name} -> {to_name}")
        print(f"    {dep_time.strftime('%H:%M')} -> {arr_time.strftime('%H:%M')}")
```

## Available Types

### Enums
- `Clasz`: Transport class (REGIONAL, LONG_DISTANCE, SUBWAY, TRAM, BUS, etc.)
- `LocationType`: Location types (STATION, TRACK, GENERATED_TRACK)
- `EventType`: Event types (DEP, ARR)
- `Direction`: Search direction (FORWARD, BACKWARD)
- `LocationMatchMode`: Location matching modes for routing
  - `EXACT`: Match only the exact platform/stop specified
  - `EQUIVALENT`: Match all equivalent stops at a station (recommended for most routing)
  - `ONLY_CHILDREN`: Match all child stops of a parent station

### Core Types
- `Timetable`: Main timetable data structure
- `Query`: Routing query configuration
- `Journey`: Routing result with legs
- `LoaderConfig`: Configuration for data loading
- `RtTimetable`: Real-time timetable

### Functions
- `load_timetable()`: Load transit data
- `route()`: Perform routing query
- `gtfsrt_update_from_bytes()`: Apply GTFS-RT updates from bytes
- `gtfsrt_update_from_string()`: Apply GTFS-RT updates from string
- `gtfsrt_update_from_file()`: Apply GTFS-RT updates from file

## Testing

Run the test suite to verify the bindings work correctly:

```bash
cd nigiri/python
pytest tests/
```

Expected output:
```
======================== 23 passed ========================
```

All tests should pass without any warnings or issues.

## Installation via pip

Install the package using pip:

```bash
cd python
pip install .
```

For development (editable install):

```bash
pip install -e .
```

## Implementation Notes

- Built with [pybind11](https://github.com/pybind/pybind11) v2.11.1
- Requires C++23 compiler (GCC 13+ or Clang 16+)
- Uses CMake for build configuration
- All static libraries compiled with `-fPIC` for shared library compatibility
- Strong type wrappers for type safety (LocationIdx, TransportIdx, etc.)

## Files

- `src/main.cc`: Module entry point
- `src/types.cc`: Core types and enums
- `src/timetable.cc`: Timetable access
- `src/loader.cc`: Data loading
- `src/routing.cc`: Routing algorithms
- `src/rt.cc`: Real-time updates
- `pybind_common.h`: Common headers

## License

Same as nigiri - MIT License
