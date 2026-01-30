#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>

namespace py = pybind11;

// Forward declarations
void init_types(py::module_&);
void init_timetable(py::module_&);
void init_loader(py::module_&);
void init_routing(py::module_&);
void init_rt(py::module_&);
