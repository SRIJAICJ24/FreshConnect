# 🔧 INSTALLATION TROUBLESHOOTING GUIDE

## ❌ **THE ERROR YOU'RE SEEING**

```
KeyError: '__version__'
Getting requirements to build wheel did not run successfully
ModuleNotFoundError: No module named 'flask'
```

---

## 🎯 **ROOT CAUSE**

**Pillow** (image library) is trying to **build from source** on Windows, which:
1. Requires C++ build tools (you don't have)
2. Fails during build
3. Stops ALL other packages from installing
4. Result: Nothing gets installed (including Flask)

---

## ✅ **SOLUTION 1: USE THE AUTOMATED SCRIPT (EASIEST)**

Just run this command:

```powershell
.\SETUP_COMPLETE.bat
```

**What it does:**
- ✅ Upgrades pip
- ✅ Installs Flask and all required packages ONE BY ONE
- ✅ Skips problematic packages (Pillow, etc.)
- ✅ Verifies everything works
- ✅ Shows you next steps

**Time:** 2-3 minutes

---

## ✅ **SOLUTION 2: MANUAL INSTALLATION**

### **Step 1: Make sure you're in the virtual environment**
```powershell
# You should see (venv) at the start of your prompt
# If not, run:
venv\Scripts\activate
```

### **Step 2: Upgrade pip**
```powershell
python -m pip install --upgrade pip
```

### **Step 3: Install packages ONE BY ONE**
```powershell
pip install Flask==3.0.0
pip install Flask-SQLAlchemy==3.1.1
pip install Flask-Login==0.6.3
pip install Flask-WTF==1.2.1
pip install Werkzeug==3.0.0
pip install WTForms==3.1.1
pip install python-dotenv==1.0.0
```

### **Step 4: Verify Flask is installed**
```powershell
python -c "import flask; print('Flask version:', flask.__version__)"
```

**Expected output:**
```
Flask version: 3.0.0
```

If you see this, you're good! Skip to "Next Steps" below.

---

## ✅ **SOLUTION 3: USE SIMPLIFIED REQUIREMENTS**

```powershell
pip install -r requirements.txt
```

The requirements.txt is now simplified and won't try to install problematic packages.

---

## 🚫 **WHAT NOT TO DO**

❌ Don't try to install the original requirements.txt with Pillow  
❌ Don't install Visual Studio Build Tools (not necessary)  
❌ Don't use `pip install -r requirements.txt` if it includes Pillow

---

## 📝 **EXPLANATION: WHY PILLOW FAILS**

Pillow is an **image processing library** that:
- Needs to be **compiled from C code** on Windows
- Requires **Visual Studio C++ Build Tools** (1.5GB download)
- Often fails even with build tools installed
- Is **NOT REQUIRED** for your marketplace to work!

**Good news:** Your app works perfectly without Pillow! It's only used for:
- Image resizing (optional)
- Image validation (can be done other ways)

---

## ✅ **NEXT STEPS AFTER SUCCESSFUL INSTALLATION**

### **1. Verify Installation**
```powershell
python -c "import flask; print('✓ Flask works!')"
python -c "import flask_sqlalchemy; print('✓ SQLAlchemy works!')"
python -c "import flask_login; print('✓ Login works!')"
```

### **2. Seed Database**
```powershell
python seed_data.py
```

**Expected output:**
```
======================================================================
  SEEDING DATABASE WITH TEST DATA
======================================================================

[1/7] Clearing existing data...
[2/7] Creating admin users...
[3/7] Creating vendors...
[4/7] Creating retailers...
[5/7] Creating companies...
[6/7] Creating products...
[7/7] Creating drivers...

✓ DATABASE SEEDED SUCCESSFULLY!

TEST CREDENTIALS:
----------------------------------------------------------------------
  Admin:    admin@freshconnect.com / admin123
  Vendor:   vendor1@freshconnect.com / vendor123
  Retailer: retailer1@freshconnect.com / retailer123
  Driver:   driver1@freshconnect.com / driver123
======================================================================
```

### **3. Start Server**
```powershell
python run.py
```

**Expected output:**
```
==================================================
  FreshConnect Marketplace
==================================================
  Server: http://127.0.0.1:5000
==================================================
 * Running on http://127.0.0.1:5000
```

### **4. Open Browser**
```
http://127.0.0.1:5000
```

### **5. Test Login**
```
Email: retailer1@freshconnect.com
Password: retailer123
```

---

## 🆘 **STILL HAVING ISSUES?**

### **Issue: "python: command not found"**
**Solution:**
```powershell
# Try:
py -m pip install Flask
py seed_data.py
py run.py
```

### **Issue: "venv not activated"**
**Solution:**
```powershell
# You should see (venv) at the start
# If not:
venv\Scripts\activate
```

### **Issue: "Permission denied"**
**Solution:**
```powershell
# Run PowerShell as Administrator
# Or run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Issue: "Flask still not found after installation"**
**Solution:**
```powershell
# Deactivate and reactivate venv
deactivate
venv\Scripts\activate

# Try installing again
pip install Flask==3.0.0
```

### **Issue: "Database error"**
**Solution:**
```powershell
# Delete existing database and recreate
del instance\marketplace.db
python seed_data.py
```

---

## 📚 **WHAT PACKAGES ARE ACTUALLY REQUIRED?**

### **✅ REQUIRED (Must Install):**
- Flask - Web framework
- Flask-SQLAlchemy - Database ORM
- Flask-Login - User authentication
- Flask-WTF - Forms
- Werkzeug - Security utilities
- WTForms - Form validation
- python-dotenv - Environment variables

### **❌ OPTIONAL (Can Skip for Local Development):**
- Pillow - Image processing (causes build errors)
- gunicorn - Production server (only for deployment)
- psycopg2 - PostgreSQL driver (only for deployment)
- google-generativeai - AI chatbot (optional feature)

---

## 🎉 **QUICK SUCCESS PATH**

```powershell
# 1. Run the automated script
.\SETUP_COMPLETE.bat

# 2. Seed database
python seed_data.py

# 3. Start server
python run.py

# 4. Open browser
# http://127.0.0.1:5000

# 5. Login
# retailer1@freshconnect.com / retailer123
```

**That's it! Your marketplace is running!** 🚀

---

## 📊 **FILE STRUCTURE EXPLANATION**

```
requirements.txt               - Core packages only (USE THIS)
requirements-minimal.txt       - Same as requirements.txt
requirements-deployment.txt    - Deployment packages (gunicorn, psycopg2)
SETUP_COMPLETE.bat            - Automated installation script
INSTALLATION_TROUBLESHOOTING.md - This file
```

---

## ✅ **SUCCESS INDICATORS**

You know it's working when:
- ✅ `python -c "import flask"` runs without errors
- ✅ `python seed_data.py` shows "DATABASE SEEDED SUCCESSFULLY"
- ✅ `python run.py` starts server on port 5000
- ✅ Browser shows FreshConnect homepage
- ✅ You can login with test credentials

---

**🌿 Your FreshConnect marketplace will work perfectly without Pillow!** 🎉
