"""
Example: Exploring timetable data.
"""
import pynigiri as ng
from const import GTFS_PATH, STATION_ID_A, INVALID_LOCATION_IDX

def main():
    # Load timetable
    sources = [ng.TimetableSource("my_gtfs", str(GTFS_PATH))]
    timetable = ng.load_timetable(sources, "2026-01-01", "2026-12-31")
    
    print("=== Timetable Information ===\n")
    
    # Basic stats
    n_locations = timetable.n_locations()
    n_routes = timetable.n_routes()
    n_transports = timetable.n_transports()
    
    print(f"Total locations: {n_locations}")
    print(f"Total routes: {n_routes}")
    print(f"Total transports: {n_transports}")
    
    # Date range
    start_day, end_day = timetable.date_range()
    print(f"Date range: {start_day} to {end_day}\n")
    
    # Explore some locations
    print("=== Sample Locations ===")
    for i in range(min(10, n_locations)):
        loc_idx = ng.LocationIdx(i)
        
        name = timetable.get_location_name(loc_idx)
        coords = timetable.get_location_coords(loc_idx)
        loc_type = timetable.get_location_type(loc_idx)
        parent = timetable.get_location_parent(loc_idx)
        parent_display = "None" if int(parent) == INVALID_LOCATION_IDX else str(parent)
        
        print(f"\nLocation {i}:")
        print(f"  Name: {name}")
        print(f"  Type: {loc_type}")
        print(f"  Coordinates: ({coords.lat:.6f}, {coords.lng:.6f})")
        print(f"  Parent: {parent_display}")
    
    # Find specific location
    print("\n=== Location Lookup ===")
    # Example: Find a location by ID
    sample_id = STATION_ID_A
    found = timetable.find_location(sample_id)
    
    if found is not None:
        print(f"Found location '{sample_id}': {found}")
        print(f"  Name: {timetable.get_location_name(found)}")
        coords = timetable.get_location_coords(found)
        print(f"  Coordinates: ({coords.lat:.6f}, {coords.lng:.6f})")
        print(f"  Type: {timetable.get_location_type(found)}")
        print(f"  Parent: {timetable.get_location_parent(found)}")
    else:
        print(f"Location '{sample_id}' not found")

def explore_location_types(timetable):
    """Categorize locations by type."""
    print("\n=== Location Types Distribution ===")
    
    type_counts = {
        ng.LocationType.TRACK: 0,
        ng.LocationType.STATION: 0,
        ng.LocationType.GENERATED_TRACK: 0,
    }
    
    for i in range(timetable.n_locations()):
        loc_type = timetable.get_location_type(ng.LocationIdx(i))
        type_counts[loc_type] += 1
    
    for loc_type, count in type_counts.items():
        print(f"  {loc_type}: {count}")

if __name__ == "__main__":
    main()
