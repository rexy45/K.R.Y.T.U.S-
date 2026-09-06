@echo off
REM Krytus - Setup Environment for F: drive only
REM Run this once to configure uv to use F: drive cache

set UV_CACHE_DIR=F:\krytus\.uv-cache
set UV_PYTHON_INSTALL_DIR=F:\krytus\.uv-python
set VIRTUAL_ENV=F:\krytus\.venv
set PYTHONPATH=F:\krytus

echo UV_CACHE_DIR=F:\krytus\.uv-cache
echo UV_PYTHON_INSTALL_DIR=F:\krytus\.uv-python
echo VIRTUAL_ENV=F:\krytus\.venv
echo PYTHONPATH=F:\krytus
echo.
echo Add these to your system environment variables permanently, or run this script before each use.
echo.
pause