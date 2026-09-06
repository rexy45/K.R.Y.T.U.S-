# Krytus - Setup Environment for F: drive only
# Run this once to configure uv to use F: drive cache

$env:UV_CACHE_DIR = "F:\krytus\.uv-cache"
$env:UV_PYTHON_INSTALL_DIR = "F:\krytus\.uv-python"
$env:VIRTUAL_ENV = "F:\krytus\.venv"
$env:PYTHONPATH = "F:\krytus"

Write-Host "UV_CACHE_DIR = $env:UV_CACHE_DIR"
Write-Host "UV_PYTHON_INSTALL_DIR = $env:UV_PYTHON_INSTALL_DIR"
Write-Host "VIRTUAL_ENV = $env:VIRTUAL_ENV"
Write-Host "PYTHONPATH = $env:PYTHONPATH"
Write-Host ""
Write-Host "Run this script before each session, or add to your PowerShell profile."
Write-Host "To add to profile: notepad \$PROFILE"