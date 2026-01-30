#include "pybind_common.h"

#include "nigiri/rt/create_rt_timetable.h"
#include "nigiri/rt/gtfsrt_update.h"
#include "nigiri/rt/rt_timetable.h"
#include "nigiri/rt/frun.h"
#include "nigiri/timetable.h"

#include <string>
#include <vector>

namespace py = pybind11;
using namespace nigiri;
using namespace nigiri::rt;

void init_rt(py::module_& m) {
  // Statistics
  py::class_<statistics>(m, "Statistics")
      .def(py::init<>())
      .def_readwrite("parser_error", &statistics::parser_error_)
      .def_readwrite("no_header", &statistics::no_header_)
      .def_readwrite("total_entities", &statistics::total_entities_)
      .def_readwrite("total_entities_success", &statistics::total_entities_success_)
      .def_readwrite("total_entities_fail", &statistics::total_entities_fail_)
      .def_readwrite("total_alerts", &statistics::total_alerts_)
      .def_readwrite("total_vehicles", &statistics::total_vehicles_)
      .def_readwrite("trip_update_without_trip", &statistics::trip_update_without_trip_)
      .def_readwrite("trip_resolve_error", &statistics::trip_resolve_error_)
      .def_readwrite("unsupported_schedule_relationship", 
                     &statistics::unsupported_schedule_relationship_)
      .def("__repr__", [](statistics const& s) {
        return "Statistics(total=" + std::to_string(s.total_entities_) +
               ", success=" + std::to_string(s.total_entities_success_) +
               ", fail=" + std::to_string(s.total_entities_fail_) + ")";
      });

  // RT Timetable
  py::class_<rt_timetable>(m, "RtTimetable")
      .def(py::init<>())
      .def("__repr__", [](rt_timetable const&) {
        return "RtTimetable()";
      });

  // Create RT timetable
  m.def("create_rt_timetable",
        [](timetable const& tt, date::sys_days day) -> rt_timetable {
          return create_rt_timetable(tt, day);
        },
        py::arg("timetable"),
        py::arg("day"),
        "Create real-time timetable for a specific day");

  // GTFS-RT update from string
  m.def("gtfsrt_update_from_string",
        [](timetable const& tt, 
           rt_timetable& rtt,
           source_idx_t src,
           std::string const& tag,
           std::string const& data) -> statistics {
          return gtfsrt_update_buf(tt, rtt, src, tag, data);
        },
        py::arg("timetable"),
        py::arg("rt_timetable"),
        py::arg("source"),
        py::arg("tag"),
        py::arg("data"),
        "Update real-time timetable from GTFS-RT protobuf string");

  // GTFS-RT update from bytes
  m.def("gtfsrt_update_from_bytes",
        [](timetable const& tt,
           rt_timetable& rtt,
           source_idx_t src,
           std::string const& tag,
           py::bytes const& data) -> statistics {
          std::string str = data;
          return gtfsrt_update_buf(tt, rtt, src, tag, str);
        },
        py::arg("timetable"),
        py::arg("rt_timetable"),
        py::arg("source"),
        py::arg("tag"),
        py::arg("data"),
        "Update real-time timetable from GTFS-RT protobuf bytes");

  // GTFS-RT update from file
  m.def("gtfsrt_update_from_file",
        [](timetable const& tt,
           rt_timetable& rtt,
           source_idx_t src,
           std::string const& tag,
           std::string const& file_path) -> statistics {
          // Read file
          std::ifstream file(file_path, std::ios::binary);
          if (!file) {
            throw std::runtime_error("Cannot open file: " + file_path);
          }
          std::string data((std::istreambuf_iterator<char>(file)),
                          std::istreambuf_iterator<char>());
          return gtfsrt_update_buf(tt, rtt, src, tag, data);
        },
        py::arg("timetable"),
        py::arg("rt_timetable"),
        py::arg("source"),
        py::arg("tag"),
        py::arg("file_path"),
        "Update real-time timetable from GTFS-RT protobuf file");
}
