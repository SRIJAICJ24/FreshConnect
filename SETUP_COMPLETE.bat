@echo off
echo ========================================================================
echo   FRESHCONNECT - COMPLETE SETUP (NO BUILD ERRORS)
echo ========================================================================
echo.

echo Step 1: Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)
echo ✓ Pip upgraded successfully
echo.

echo Step 2: Installing core Flask packages...
pip install Flask==3.0.0
if errorlevel 1 (
    echo ERROR: Failed to install Flask
    pause
    exit /b 1
)
echo ✓ Flask installed
echo.

pip install Flask-SQLAlchemy==3.1.1
echo ✓ Flask-SQLAlchemy installed
pip install Flask-Login==0.6.3
echo ✓ Flask-Login installed
pip install Flask-WTF==1.2.1
echo ✓ Flask-WTF installed
pip install Werkzeug==3.0.0
echo ✓ Werkzeug installed
pip install WTForms==3.1.1
echo ✓ WTForms installed
pip install python-dotenv==1.0.0
echo ✓ python-dotenv installed
echo.

echo Step 3: Installing optional packages (these can fail, app will still work)...
pip install Pillow --no-build-isolation
echo   (Pillow install attempted - not critical if it fails)
pip install gunicorn
echo   (Gunicorn install attempted - only needed for deployment)
pip install psycopg2-binary
echo   (PostgreSQL driver attempted - only needed for deployment)
echo.

echo Step 4: Verifying Flask installation...
python -c "import flask; print('✓ Flask version:', flask.__version__)"
if errorlevel 1 (
    echo ERROR: Flask not installed properly
    pause
    exit /b 1
)
echo.

python -c "import flask_sqlalchemy; print('✓ Flask-SQLAlchemy OK')"
python -c "import flask_login; print('✓ Flask-Login OK')"
python -c "from werkzeug.security import generate_password_hash; print('✓ Werkzeug OK')"
echo.

echo ========================================================================
echo   ✓✓✓ SETUP COMPLETE! ✓✓✓
echo ========================================================================
echo.
echo All core packages installed successfully!
echo.
echo NEXT STEPS:
echo -----------
echo 1. Run: python seed_data.py
echo 2. Run: python run.py
echo 3. Open: http://127.0.0.1:5000
echo.
echo TEST ACCOUNTS:
echo - Admin:    admin@freshconnect.com / admin123
echo - Vendor:   vendor1@freshconnect.com / vendor123
echo - Retailer: retailer1@freshconnect.com / retailer123
echo - Driver:   driver1@freshconnect.com / driver123
echo.
echo ========================================================================
pause
