from flask import render_template, redirect, url_for
from flask_login import current_user
from app.routes import main_bp
from app.models import Product, User, Order
from app import db

@main_bp.route('/')
def index():
    """Homepage"""
    # Get statistics
    vendor_count = User.query.filter_by(user_type='vendor', is_active=True).count()
    retailer_count = User.query.filter_by(user_type='retailer', is_active=True).count()
    product_count = Product.query.filter_by(is_active=True).count()
    
    # Get featured products
    featured_products = Product.query.filter_by(is_active=True).limit(6).all()
    
    # Get emergency products
    emergency_products = Product.query.filter_by(is_active=True, is_emergency=True).limit(6).all()
    
    return render_template('index.html',
                         vendor_count=vendor_count,
                         retailer_count=retailer_count,
                         product_count=product_count,
                         featured_products=featured_products,
                         emergency_products=emergency_products)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')
