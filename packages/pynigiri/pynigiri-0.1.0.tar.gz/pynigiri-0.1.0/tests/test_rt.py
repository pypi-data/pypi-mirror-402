"""
Unit tests for pynigiri real-time functionality.
"""
import pytest
import pynigiri as ng


def test_statistics_creation():
    """Test Statistics creation."""
    stats = ng.Statistics()
    assert stats is not None
    
    stats.total_entities = 100
    stats.total_entities_success = 95
    stats.total_entities_fail = 5
    
    assert stats.total_entities == 100
    assert stats.total_entities_success == 95
    assert stats.total_entities_fail == 5


def test_rt_timetable_creation():
    """Test RtTimetable creation."""
    rt_tt = ng.RtTimetable()
    assert rt_tt is not None


# Note: Full RT tests would require a loaded timetable and RT data
# The following tests are commented out as they require real data

# def test_create_rt_timetable():
#     """Test creating RT timetable (requires timetable)."""
#     # Load timetable...
#     # timetable = ...
#     
#     from datetime import date
#     today = date.today()
#     
#     rt_tt = ng.create_rt_timetable(timetable, today)
#     assert rt_tt is not None

# def test_gtfsrt_update_from_bytes():
#     """Test GTFS-RT update from bytes (requires timetable and RT data)."""
#     # Load timetable and create RT timetable...
#     # timetable = ...
#     # rt_tt = ...
#     
#     # Sample GTFS-RT protobuf data
#     rt_data = b"..."  # Real protobuf data
#     
#     stats = ng.gtfsrt_update_from_bytes(
#         timetable=timetable,
#         rt_timetable=rt_tt,
#         source=ng.SourceIdx(0),
#         tag="test_update",
#         data=rt_data
#     )
#     
#     assert stats is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
