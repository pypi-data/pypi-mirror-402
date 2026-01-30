cmake_minimum_required(VERSION 3.22)
project(pynigiri)

# Set position independent code for all targets
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find Python and pybind11
# In cibuildwheel, Python3_EXECUTABLE is set correctly
find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)

# Fetch pybind11 if not available
include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG v2.11.1
)
FetchContent_MakeAvailable(pybind11)

# Collect all binding source files
file(GLOB_RECURSE PYNIGIRI_SOURCES
  "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cc"
)

# Create the Python module
pybind11_add_module(pynigiri MODULE ${PYNIGIRI_SOURCES})

# Link with the nigiri library
target_link_libraries(pynigiri PRIVATE nigiri)

# Include directories
target_include_directories(pynigiri PRIVATE 
  ${CMAKE_SOURCE_DIR}/include
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Set C++ standard
target_compile_features(pynigiri PRIVATE cxx_std_23)

# Install the module
install(TARGETS pynigiri LIBRARY DESTINATION pynigiri)
