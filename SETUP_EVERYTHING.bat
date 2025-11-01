@echo off
REM ========================================================================
REM   COMPLETE LOGISTICS SYSTEM SETUP - ONE-CLICK DEPLOYMENT
REM   This does EVERYTHING automatically!
REM ========================================================================

echo.
echo ========================================================================
echo   FRESHCONNECT LOGISTICS SYSTEM - AUTOMATED SETUP
echo ========================================================================
echo.
echo This will:
echo   1. Create all 7 logistics tables
echo   2. Seed logistics data (10 areas + 8 drivers)
echo   3. Run system tests (7 tests)
echo   4. Verify driver login access
echo   5. Show complete summary
echo.
echo Press any key to start, or Ctrl+C to cancel...
pause >nul

REM Activate virtual environment
echo.
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo Please make sure venv exists: python -m venv venv
    pause
    exit /b 1
)

REM Run the complete setup
echo.
echo [*] Running complete setup...
echo.
python COMPLETE_SETUP.py

if errorlevel 1 (
    echo.
    echo ========================================================================
    echo   SETUP FAILED!
    echo ========================================================================
    echo.
    echo Check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   SETUP COMPLETED!
echo ========================================================================
echo.
echo You can now start the server:
echo   python run.py
echo.
echo Then login as driver:
echo   Email: driver1@freshconnect.com
echo   Password: driver123
echo.
pause
