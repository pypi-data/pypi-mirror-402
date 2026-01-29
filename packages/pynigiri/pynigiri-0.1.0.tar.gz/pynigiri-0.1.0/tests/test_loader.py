"""
Unit tests for pynigiri loader functionality.
"""
import pytest
import pynigiri as ng


def test_loader_config():
    """Test LoaderConfig creation."""
    config = ng.LoaderConfig()
    assert config is not None
    
    # Test with custom settings
    config.link_stop_distance = 100
    assert config.link_stop_distance == 100


def test_footpath_settings():
    """Test FootpathSettings creation - skipped as not available."""
    # FootpathSettings is not exposed in the current API
    pass


def test_finalize_options():
    """Test FinalizeOptions creation."""
    options = ng.FinalizeOptions()
    assert options is not None
    # FinalizeOptions attributes are not currently exposed


def test_timetable_source():
    """Test TimetableSource creation."""
    source = ng.TimetableSource()
    assert source is not None
    
    source.tag = "test_gtfs"
    source.path = "/path/to/gtfs"
    
    assert source.tag == "test_gtfs"
    assert source.path == "/path/to/gtfs"
    
    # Test with constructor
    source2 = ng.TimetableSource("tag2", "/path2", ng.LoaderConfig())
    assert source2.tag == "tag2"
    assert source2.path == "/path2"


# Note: Full integration test would require actual GTFS data
# The following test is commented out as it requires real data

# def test_load_timetable():
#     """Test loading a timetable (requires actual GTFS data)."""
#     sources = [
#         ng.TimetableSource("test", "test_data/gtfs")
#     ]
#     
#     timetable = ng.load_timetable(
#         sources=sources,
#         start_date="2024-01-01",
#         end_date="2024-01-31"
#     )
#     
#     assert timetable is not None
#     assert timetable.n_locations() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
