@echo off
REM Quick build script for PyNigiri (Windows)

echo ===================================
echo PyNigiri Build Script (Windows)
echo ===================================
echo.

REM Check Python
python --version
if errorlevel 1 (
    echo Error: Python not found
    exit /b 1
)

REM Check directory
if not exist pyproject.toml (
    echo Error: This script must be run from the python\ directory
    exit /b 1
)

REM Parse arguments
set MODE=install
if "%1"=="dev" set MODE=develop
if "%1"=="develop" set MODE=develop
if "%1"=="clean" (
    echo Cleaning build artifacts...
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
    for /d /r %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
    del /s /q *.pyc 2>nul
    echo Clean complete!
    exit /b 0
)

echo.
echo Build mode: %MODE%
echo.

REM Install dependencies
echo Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install scikit-build-core pybind11 numpy

REM Build and install
if "%MODE%"=="develop" (
    echo.
    echo Installing in development mode...
    python -m pip install -e . --verbose
) else (
    echo.
    echo Installing...
    python -m pip install . --verbose
)

REM Test import
echo.
echo Testing import...
python -c "import pynigiri; print('✓ PyNigiri imported successfully'); print(f'  Version: {pynigiri.__version__}')"

echo.
echo ===================================
echo Build complete!
echo ===================================
echo.
echo Usage:
echo   import pynigiri as ng
echo.
echo Next steps:
echo   - Run examples: python examples\basic_routing.py
echo   - Run tests: pytest tests\
echo   - Read docs: type README.md
echo.
