@echo off
:: =============================================================================
:: AI Image Enhancer — Windows Build Script
:: Run this file on a Windows machine to build the executable locally.
:: =============================================================================

echo ===================================================
echo   🤖 AI Image Enhancer - Windows Build Script
echo ===================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.12.
    pause
    exit /b 1
)

:: Create Virtual Environment
if not exist .venv (
    echo Creating virtual environment in .venv...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Upgrading pip and build tools...
python -m pip install --upgrade pip wheel setuptools

:: Detect if NVIDIA GPU is present via dxdiag/wmic or nvcc
echo Checking for NVIDIA GPU...
wmic path win32_VideoController get name | findstr /I "NVIDIA" >nul
if %errorlevel% equ 0 (
    echo [INFO] NVIDIA GPU detected. Installing PyTorch with CUDA 12.1 support...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
) else (
    echo [INFO] No NVIDIA GPU detected. Installing CPU PyTorch...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
)

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
pip install pyinstaller

echo Cleaning up old builds...
if exist build rd /s /q build
if exist dist rd /s /q dist

echo Building executable...
pyinstaller ai_enhancer.spec

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo   BUILD SUCCESSFUL!
    echo   Output folder: dist\AIImageEnhancer\
    echo   Run: dist\AIImageEnhancer\AIImageEnhancer.exe
    echo ===================================================
) else (
    echo [ERROR] Build failed. Check the logs above.
)

pause
