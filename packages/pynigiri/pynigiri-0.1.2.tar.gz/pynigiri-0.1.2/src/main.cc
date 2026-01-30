#include "pybind_common.h"

#include <pybind11/pybind11.h>

namespace py = pybind11;

PYBIND11_MODULE(pynigiri, m) {
  m.doc() = "Python bindings for the nigiri transit routing library";

  // Initialize submodules
  init_types(m);
  init_timetable(m);
  init_loader(m);
  init_routing(m);
  init_rt(m);
}
