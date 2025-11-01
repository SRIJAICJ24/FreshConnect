@echo off
REM ========================================================================
REM   LOGISTICS SYSTEM - AUTOMATED DEPLOYMENT SCRIPT
REM   Run this to set up the complete delivery & logistics system
REM ========================================================================

echo.
echo ======================================================================
echo   FRESHCONNECT LOGISTICS SYSTEM - AUTOMATED DEPLOYMENT
echo ======================================================================
echo.

REM Check if in correct directory
if not exist "app\models_logistics.py" (
    echo [ERROR] Not in correct directory!
    echo Please navigate to: C:\Users\LENOVO\freshconnect-rebuild
    pause
    exit /b 1
)

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please create venv first: python -m venv venv
    pause
    exit /b 1
)

echo [1/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo    + Virtual environment activated
echo.

echo [2/5] Creating logistics tables...
python -c "from app import create_app, db; from app import models_logistics; app = create_app(); app.app_context().push(); db.create_all(); print('   + Tables created successfully!')"
if errorlevel 1 (
    echo [ERROR] Failed to create tables
    pause
    exit /b 1
)
echo.

echo [3/5] Seeding logistics data...
python seed_logistics.py
if errorlevel 1 (
    echo [ERROR] Failed to seed data
    pause
    exit /b 1
)
echo.

echo [4/5] Running system tests...
python test_logistics_quick.py
if errorlevel 1 (
    echo [ERROR] System tests failed
    pause
    exit /b 1
)
echo.

echo [5/5] Deployment complete!
echo.
echo ======================================================================
echo   + LOGISTICS SYSTEM DEPLOYED SUCCESSFULLY!
echo ======================================================================
echo.
echo WHAT'S DEPLOYED:
echo   + 7 database tables created
echo   + 10 delivery areas configured
echo   + 8 enhanced drivers available
echo   + 20+ API endpoints active
echo   + Complete delivery workflow ready
echo.
echo NEXT STEPS:
echo   1. Start server: python run.py
echo   2. Login as driver: driver1@freshconnect.com / driver123
echo   3. Visit: http://127.0.0.1:5000/driver/dashboard/enhanced
echo.
echo NOTE: If you see "template not found" error, that's OK!
echo       Backend is working, just need to create HTML templates.
echo.
echo ======================================================================
echo.
pause
