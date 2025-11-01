from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.routes import auth_bp
from app.models import User, RetailerCredit
from app import db

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        business_name = request.form.get('business_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        city = request.form.get('city')
        
        # Validation
        if not all([name, email, password, user_type]):
            flash('All fields are required', 'danger')
            return render_template('auth/register.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = User(
            name=name,
            email=email,
            user_type=user_type,
            business_name=business_name,
            phone=phone,
            address=address,
            city=city,
            is_active=True,
            is_verified=True  # Auto-verify for demo
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create credit profile for retailers
            if user_type == 'retailer':
                credit = RetailerCredit(retailer_id=user.id)
                db.session.add(credit)
                db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        # Redirect based on user type
        if current_user.user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.user_type == 'vendor':
            return redirect(url_for('vendor.dashboard'))
        elif current_user.user_type == 'retailer':
            return redirect(url_for('retailer.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Email and password are required', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'danger')
            return render_template('auth/login.html')
        
        if not user.is_active:
            flash('Account is deactivated. Please contact admin.', 'danger')
            return render_template('auth/login.html')
        
        login_user(user, remember=remember)
        
        # Redirect to dashboard based on user type
        if user.user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.user_type == 'vendor':
            return redirect(url_for('vendor.dashboard'))
        elif user.user_type == 'retailer':
            return redirect(url_for('retailer.dashboard'))
        else:
            return redirect(url_for('main.index'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile"""
    return render_template('auth/profile.html')
