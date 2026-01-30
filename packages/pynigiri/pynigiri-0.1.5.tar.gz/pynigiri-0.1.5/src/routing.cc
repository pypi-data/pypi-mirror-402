#include "pybind_common.h"

#include "nigiri/routing/query.h"
#include "nigiri/routing/journey.h"
#include "nigiri/routing/raptor_search.h"
#include "nigiri/routing/clasz_mask.h"
#include "nigiri/routing/limits.h"
#include "nigiri/routing/search.h"
#include "nigiri/timetable.h"

#include <chrono>
#include <optional>
#include <variant>
#include <vector>

namespace py = pybind11;
using namespace nigiri;
using namespace nigiri::routing;

void init_routing(py::module_& m) {
  // Transport mode ID - just return the int directly
  m.def("TransportModeId", [](std::uint32_t id) { return id; },
        py::arg("id"), "Create a transport mode ID (returns uint32)");


  // Offset
  py::class_<offset>(m, "Offset")
      .def(py::init([](location_idx_t loc, int minutes, transport_mode_id_t mode) {
        return offset{loc, duration_t{i32_minutes{minutes}}, mode};
      }),
           py::arg("target"),
           py::arg("duration"),
           py::arg("transport_mode") = transport_mode_id_t{0})
      .def("target", &offset::target)
      .def("duration", [](offset const& o) { return o.duration().count(); })
      .def("type", &offset::type)
      .def(py::self == py::self)
      .def(py::self < py::self)
      .def("__repr__", [](offset const& o) {
        return "Offset(target=" + std::to_string(o.target().v_) +
               ", duration=" + std::to_string(o.duration().count()) + ")";
      });

  // TD offset
  py::class_<td_offset>(m, "TdOffset")
      .def(py::init<>())
      .def_readwrite("valid_from", &td_offset::valid_from_)
      .def_readwrite("duration", &td_offset::duration_)
      .def_readwrite("transport_mode_id", &td_offset::transport_mode_id_)
      .def("duration_fn", &td_offset::duration)
      .def(py::self == py::self)
      .def("__repr__", [](td_offset const& o) {
        return "TdOffset(duration=" + std::to_string(o.duration_.count()) + ")";
      });

  // Via stop
  py::class_<via_stop>(m, "ViaStop")
      .def(py::init<>())
      .def_readwrite("location", &via_stop::location_)
      .def_property("stay",
          [](via_stop const& vs) { return py::int_(vs.stay_.count()); },
          [](via_stop& vs, int minutes) { vs.stay_ = duration_t{minutes}; })
      .def(py::self == py::self)
      .def("__repr__", [](via_stop const& vs) {
        return "ViaStop(location=" + std::to_string(vs.location_.v_) +
               ", stay=" + std::to_string(vs.stay_.count()) + ")";
      });

  // Location match mode
  py::enum_<location_match_mode>(m, "LocationMatchMode")
      .value("EXACT", location_match_mode::kExact)
      .value("ONLY_CHILDREN", location_match_mode::kOnlyChildren)
      .value("EQUIVALENT", location_match_mode::kEquivalent)
      .value("INTERMODAL", location_match_mode::kIntermodal)
      .export_values();

  // Clasz mask
  m.def("all_clasz_allowed", &all_clasz_allowed, "Get mask allowing all classes");

  // Transfer time settings
  py::class_<transfer_time_settings>(m, "TransferTimeSettings")
      .def(py::init<>())
      .def_readwrite("default", &transfer_time_settings::default_)
      .def_readwrite("min_transfer_time", &transfer_time_settings::min_transfer_time_)
      .def_readwrite("additional_time", &transfer_time_settings::additional_time_)
      .def_readwrite("factor", &transfer_time_settings::factor_)
      .def("__repr__", [](transfer_time_settings const&) {
        return "TransferTimeSettings()";
      });

  // Query
  py::class_<query>(m, "Query")
      .def(py::init<>())
      
      // Start time - expose as int (minutes) or tuple of ints (interval)
      .def_property("start_time",
        [](query const& q) -> py::object {
          if (std::holds_alternative<unixtime_t>(q.start_time_)) {
            auto ut = std::get<unixtime_t>(q.start_time_);
            return py::int_(ut.time_since_epoch().count());
          } else {
            auto const& iv = std::get<interval<unixtime_t>>(q.start_time_);
            return py::make_tuple(
              iv.from_.time_since_epoch().count(),
              iv.to_.time_since_epoch().count()
            );
          }
        },
        [](query& q, py::handle obj) {
          if (py::isinstance<py::tuple>(obj)) {
            auto t = obj.cast<py::tuple>();
            q.start_time_ = interval<unixtime_t>{
              unixtime_t{i32_minutes{t[0].cast<int>()}},
              unixtime_t{i32_minutes{t[1].cast<int>()}}
            };
          } else {
            q.start_time_ = unixtime_t{
              i32_minutes{obj.cast<int>()}
            };
          }
        })
      
      .def_readwrite("start_match_mode", &query::start_match_mode_)
      .def_readwrite("dest_match_mode", &query::dest_match_mode_)
      .def_readwrite("use_start_footpaths", &query::use_start_footpaths_)
      .def_readwrite("start", &query::start_)
      .def_readwrite("destination", &query::destination_)
      .def_readwrite("max_start_offset", &query::max_start_offset_)
      .def_readwrite("max_transfers", &query::max_transfers_)
      .def_property("max_travel_time",
          [](query const& q) { return py::int_(q.max_travel_time_.count()); },
          [](query& q, int minutes) { q.max_travel_time_ = duration_t{minutes}; })
      .def_readwrite("min_connection_count", &query::min_connection_count_)
      .def_readwrite("extend_interval_earlier", &query::extend_interval_earlier_)
      .def_readwrite("extend_interval_later", &query::extend_interval_later_)
      .def_readwrite("prf_idx", &query::prf_idx_)
      .def_readwrite("allowed_claszes", &query::allowed_claszes_)
      .def_readwrite("require_bike_transport", &query::require_bike_transport_)
      .def_readwrite("require_car_transport", &query::require_car_transport_)
      .def_readwrite("transfer_time_settings", &query::transfer_time_settings_)
      .def_readwrite("via_stops", &query::via_stops_)
      .def_readwrite("slow_direct", &query::slow_direct_)
      
      .def("flip_dir", &query::flip_dir, "Flip query direction")
      .def(py::self == py::self)
      
      .def("__repr__", [](query const& q) {
        return "Query(start=" + std::to_string(q.start_.size()) +
               " locations, dest=" + std::to_string(q.destination_.size()) +
               " locations, max_transfers=" + std::to_string(q.max_transfers_) + ")";
      });

  // Journey leg
  py::class_<journey::leg>(m, "Leg")
      .def_readonly("from", &journey::leg::from_)
      .def_readonly("to", &journey::leg::to_)
      // Expose times as integers (minutes since epoch)
      .def_property_readonly("dep_time",
        [](journey::leg const& l) {
          return l.dep_time_.time_since_epoch().count();
        })
      .def_property_readonly("arr_time",
        [](journey::leg const& l) {
          return l.arr_time_.time_since_epoch().count();
        })
      .def(py::self == py::self)
      .def(py::self < py::self)
      .def("__repr__", [](journey::leg const& leg) {
        return "Leg(from=" + std::to_string(leg.from_.v_) +
               ", to=" + std::to_string(leg.to_.v_) +
               ", dep=" + std::to_string(leg.dep_time_.time_since_epoch().count()) +
               ", arr=" + std::to_string(leg.arr_time_.time_since_epoch().count()) + ")";
      });

  // Journey
  py::class_<journey>(m, "Journey")
      .def(py::init<>())
      .def_readonly("legs", &journey::legs_)
      // Expose times as integers (minutes since epoch)
      .def_property_readonly("start_time",
        [](journey const& j) {
          return j.start_time_.time_since_epoch().count();
        })
      .def_property_readonly("dest_time",
        [](journey const& j) {
          return j.dest_time_.time_since_epoch().count();
        })
      .def_readonly("transfers", &journey::transfers_)
      
      // Return travel_time as int (minutes)
      .def("travel_time", [](journey const& j) {
        return j.travel_time().count();
      })
      .def("departure_time", [](journey const& j) {
        return j.departure_time().time_since_epoch().count();
      })
      .def("arrival_time", [](journey const& j) {
        return j.arrival_time().time_since_epoch().count();
      })
      .def("dominates", &journey::dominates)
      
      .def(py::self == py::self)
      .def(py::self < py::self)
      
      .def("__repr__", [](journey const& j) {
        return "Journey(legs=" + std::to_string(j.legs_.size()) +
               ", transfers=" + std::to_string(j.transfers_) +
               ", travel_time=" + std::to_string(j.travel_time().count()) + ")";
      })
      
      .def("__len__", [](journey const& j) { return j.legs_.size(); })
      .def("__getitem__", [](journey const& j, size_t i) -> journey::leg const& {
        if (i >= j.legs_.size()) throw py::index_error();
        return j.legs_[i];
      });

  // Routing functions  
  m.def("route",
        [](timetable const& tt, query q) -> std::vector<journey> {
          search_state s_state;
          raptor_state r_state;
          auto const results = raptor_search(tt, nullptr, s_state, r_state, std::move(q), direction::kForward);
          if (results.journeys_ == nullptr) {
            return {};
          }
          return std::vector<journey>{results.journeys_->begin(), results.journeys_->end()};
        },
        py::arg("timetable"),
        py::arg("query"),
        "Execute routing query");

  m.def("route_with_rt",
        [](timetable const& tt, rt_timetable const* rtt, query q) 
        -> std::vector<journey> {
          search_state s_state;
          raptor_state r_state;
          auto const results = raptor_search(tt, rtt, s_state, r_state, std::move(q), direction::kForward);
          if (results.journeys_ == nullptr) {
            return {};
          }
          return std::vector<journey>{results.journeys_->begin(), results.journeys_->end()};
        },
        py::arg("timetable"),
        py::arg("rt_timetable"),
        py::arg("query"),
        "Execute routing query with real-time data");
}
