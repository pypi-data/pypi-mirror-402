#include "pybind_common.h"

#include "nigiri/loader/load.h"
#include "nigiri/loader/loader_interface.h"
#include "nigiri/loader/build_footpaths.h"
#include "nigiri/timetable.h"

#include "date/date.h"
#include "utl/progress_tracker.h"

#include <chrono>
#include <string>
#include <vector>

namespace py = pybind11;
using namespace nigiri;
using namespace nigiri::loader;

void init_loader(py::module_& m) {
  // Loader config
  py::class_<loader_config>(m, "LoaderConfig")
      .def(py::init<>())
      .def_readwrite("link_stop_distance", &loader_config::link_stop_distance_)
      .def_readwrite("default_tz", &loader_config::default_tz_)
      .def_readwrite("extend_calendar", &loader_config::extend_calendar_)
      .def("__repr__", [](loader_config const&) {
        return "LoaderConfig()";
      });

  // Finalize options
  py::class_<finalize_options>(m, "FinalizeOptions")
      .def(py::init<>())
      .def_readwrite("adjust_footpaths", &finalize_options::adjust_footpaths_)
      .def_readwrite("merge_dupes_intra_src", &finalize_options::merge_dupes_intra_src_)
      .def_readwrite("merge_dupes_inter_src", &finalize_options::merge_dupes_inter_src_)
      .def_readwrite("max_footpath_length", &finalize_options::max_footpath_length_)
      .def("__repr__", [](finalize_options const&) {
        return "FinalizeOptions()";
      });

  // Timetable source
  py::class_<timetable_source>(m, "TimetableSource")
      .def(py::init<>())
      .def(py::init<std::string, std::string, loader_config>(),
           py::arg("tag"),
           py::arg("path"),
           py::arg("config") = loader_config{})
      .def_readwrite("tag", &timetable_source::tag_)
      .def_readwrite("path", &timetable_source::path_)
      .def_readwrite("loader_config", &timetable_source::loader_config_)
      .def("__repr__", [](timetable_source const& ts) {
        return "TimetableSource(tag='" + ts.tag_ + "', path='" + ts.path_ + "')";
      });

  // Load timetable function
  m.def("load_timetable",
        [](std::vector<timetable_source> const& sources,
           std::string const& start_date,
           std::string const& end_date,
           finalize_options const& options) -> timetable {
          // Activate progress tracker
          auto tracker = utl::activate_progress_tracker("pynigiri");
          
          // Parse dates (format: YYYY-MM-DD)
          std::istringstream start_ss{start_date};
          std::istringstream end_ss{end_date};
          date::sys_days start, end;
          start_ss >> date::parse("%Y-%m-%d", start);
          end_ss >> date::parse("%Y-%m-%d", end);
          
          auto const interval = ::nigiri::interval<date::sys_days>{start, end};
          return load(sources, options, interval);
        },
        py::arg("sources"),
        py::arg("start_date"),
        py::arg("end_date"),
        py::arg("options") = finalize_options{},
        "Load timetable from sources");

  // Convenience overload with datetime objects
  m.def("load_timetable_dt",
        [](std::vector<timetable_source> const& sources,
           std::chrono::system_clock::time_point const& start,
           std::chrono::system_clock::time_point const& end,
           finalize_options const& options) -> timetable {
          // Activate progress tracker
          auto tracker = utl::activate_progress_tracker("pynigiri");
          
          auto const start_days = date::floor<date::days>(start);
          auto const end_days = date::floor<date::days>(end);
          auto const interval = ::nigiri::interval<date::sys_days>{start_days, end_days};
          return load(sources, options, interval);
        },
        py::arg("sources"),
        py::arg("start"),
        py::arg("end"),
        py::arg("options") = finalize_options{},
        "Load timetable from sources using datetime objects");
}
