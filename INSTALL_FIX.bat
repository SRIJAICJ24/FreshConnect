@echo off
echo ========================================
echo   FIXING INSTALLATION - FRESHCONNECT
echo ========================================
echo.

echo [1/4] Upgrading pip...
python -m pip install --upgrade pip
echo.

echo [2/4] Installing dependencies (this may take 2-3 minutes)...
pip install Flask==3.0.0
pip install Flask-SQLAlchemy==3.1.1
pip install Flask-Login==0.6.3
pip install Flask-WTF==1.2.1
pip install python-dotenv==1.0.0
pip install Pillow==10.4.0
pip install Werkzeug==3.0.0
pip install WTForms==3.1.1
pip install gunicorn==21.2.0
echo.

echo [3/4] Installing optional dependencies...
pip install google-generativeai==0.8.0
pip install psycopg2-binary==2.9.9
echo.

echo [4/4] Verifying installation...
python -c "import flask; print('✓ Flask installed:', flask.__version__)"
python -c "import flask_sqlalchemy; print('✓ Flask-SQLAlchemy installed')"
python -c "import flask_login; print('✓ Flask-Login installed')"
python -c "from PIL import Image; print('✓ Pillow installed')"
echo.

echo ========================================
echo   ✓ INSTALLATION COMPLETE!
echo ========================================
echo.
echo Now run: python seed_data.py
echo Then run: python run.py
echo.
pause
