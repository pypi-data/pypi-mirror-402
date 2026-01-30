# PyNigiri Installation Guide

This guide covers different methods to install PyNigiri.

## Prerequisites

- Python 3.8 or higher
- C++23 compatible compiler (GCC 11+, Clang 14+, or MSVC 2022+)
- CMake 3.22 or higher
- Git

## Method 1: Install from Source (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/motis-project/nigiri.git
cd nigiri
```

### 2. Install Python Dependencies

```bash
pip install scikit-build-core pybind11 numpy
```

### 3. Build and Install

#### Standard Installation
```bash
pip install ./python
```

#### Development Installation (Editable)
```bash
pip install -e ./python
```

This allows you to modify the Python code without reinstalling.

### 4. Verify Installation

```bash
python -c "import pynigiri; print(pynigiri.__version__)"
```

### 5. Run Tests (Optional)

```bash
cd nigiri/python
pip install pytest
pytest tests/  # Should show 23 tests passing
```

### 6. Try an Example

```bash
cd nigiri/python/examples
python basic_routing.py  # Should successfully find routes
```

## Method 2: Build with CMake Directly

If you need more control over the build process:

### 1. Create Build Directory

```bash
cd nigiri
mkdir build
cd build
```

### 2. Configure CMake

```bash
cmake .. -DCMAKE_BUILD_TYPE=Release
```

### 3. Build

```bash
cmake --build . --target pynigiri -j$(nproc)
```

### 4. Install

```bash
cmake --install . --prefix /path/to/install
```

Or add the build directory to your Python path:
```bash
export PYTHONPATH=$PYTHONPATH:/path/to/nigiri/build/python
```

## Platform-Specific Instructions

### Linux (Ubuntu/Debian)

Install build dependencies:
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-dev \
    python3-pip
```

Then follow Method 1 above.

### macOS

Install Xcode Command Line Tools:
```bash
xcode-select --install
```

Install CMake (using Homebrew):
```bash
brew install cmake
```

Then follow Method 1 above.

### Windows

1. Install Visual Studio 2022 with C++ support
2. Install CMake from https://cmake.org/download/
3. Install Python from https://www.python.org/downloads/
4. Open "x64 Native Tools Command Prompt for VS 2022"
5. Follow Method 1 above

## Troubleshooting

### Compiler Not Found

If you get compiler errors, ensure you have a C++23 compatible compiler:

**GCC:**
```bash
gcc --version  # Should be 11 or higher
```

**Clang:**
```bash
clang --version  # Should be 14 or higher
```

### CMake Version Too Old

Update CMake:
```bash
pip install --upgrade cmake
```

Or download the latest from https://cmake.org/download/

### pybind11 Not Found

Install pybind11:
```bash
pip install pybind11
```

Or let CMake fetch it automatically (already configured in CMakeLists.txt).

### Linking Errors

If you encounter linking errors with the nigiri library, make sure to build the main nigiri library first:

```bash
cd nigiri
mkdir build
cd build
cmake ..
cmake --build . -j$(nproc)
```

Then build the Python bindings.

### Import Errors

If you get import errors when trying to use pynigiri:

1. Check that the module is installed:
   ```bash
   pip list | grep pynigiri
   ```

2. Check Python path:
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```

3. Verify the .so/.pyd file exists in the installation directory

## Development Setup

For development with hot-reloading:

```bash
# Install in development mode
pip install -e ./python

# Make changes to C++ code
# Rebuild
pip install -e ./python --force-reinstall --no-deps

# Or use cmake directly
cd build
cmake --build . --target pynigiri
```

## Testing the Installation

Run the test suite:
```bash
cd python
pytest tests/
```

Run a simple example:
```bash
python examples/explore_timetable.py
```

## Uninstalling

```bash
pip uninstall pynigiri
```

## Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/motis-project/nigiri/issues)
2. Review the examples in `python/examples/`
3. Read the API documentation
4. Ask questions in the project discussions

## Next Steps

- See [README.md](README.md) for usage examples
- Explore [examples/](examples/) directory
- Read the API documentation
- Try the test suite to see more usage patterns
