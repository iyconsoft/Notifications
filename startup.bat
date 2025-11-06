@echo off
REM run.bat - FastAPI production setup script with Hypercorn for Windows

setlocal enabledelayedexpansion

REM Configuration
set "APP_MODULE=src.main:app"
set "PORT=8000"
set "WORKERS=1"
set "MAX_REQUESTS=10000"
set "GRACEFUL_TIMEOUT=60"
set "VENV_DIR=venv"
set "REQUIREMENTS_FILE=requirements.txt"

REM Colors (Windows 10+ with virtual terminal support)
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "DEL=%%a"
)

echo.
echo ========================================
echo    FastAPI Production Server Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.7+ and ensure it's in your system PATH.
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo [INFO] Creating Python virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Virtual environment already exists.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing anyway...
)

REM Install requirements if the file exists
if exist "%REQUIREMENTS_FILE%" (
    echo [INFO] Installing requirements from %REQUIREMENTS_FILE%...
    pip install -r "%REQUIREMENTS_FILE%"
    if errorlevel 1 (
        echo [WARNING] Some requirements failed to install, continuing anyway...
    )
) else (
    echo [INFO] No requirements.txt found. Installing basic dependencies...
    pip install hypercorn uvloop fastapi
    if errorlevel 1 (
        echo [ERROR] Failed to install basic dependencies.
        call "%VENV_DIR%\Scripts\deactivate.bat"
        pause
        exit /b 1
    )
)

REM Validate the app module exists
echo [INFO] Validating application module...
python -c "import sys; sys.path.insert(0, '.'); from src.main import app" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Could not validate %APP_MODULE% using standard import.
    echo [INFO] Continuing anyway - Hypercorn will validate during startup...
)

REM Display startup information
echo.
echo ========================================
echo    Starting Production Server
echo ========================================
echo [INFO] Application: %APP_MODULE%
echo [INFO] Port: %PORT%
echo [INFO] Workers: %WORKERS%
echo [INFO] Server: Hypercorn with uvloop
echo.
echo [INFO] Starting Hypercorn server...
echo.

REM Run the application with Hypercorn
hypercorn %APP_MODULE% ^
    --workers %WORKERS% ^
    --bind 0.0.0.0:%PORT% ^
    --worker-class uvloop ^
    --max-requests %MAX_REQUESTS% ^
    --graceful-timeout %GRACEFUL_TIMEOUT% ^
    --access-logfile - ^
    --error-logfile -

REM Check if Hypercorn exited with error
if errorlevel 1 (
    echo.
    echo [ERROR] Hypercorn server exited with error code %errorlevel%
    echo [INFO] Check the error messages above for details.
)

REM Deactivate virtual environment
call "%VENV_DIR%\Scripts\deactivate.bat"

echo.
echo [INFO] Server has been stopped.
pause

endlocal