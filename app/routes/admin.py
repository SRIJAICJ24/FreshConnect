from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.routes import admin_bp
from app.models import User, Product, Order, Payment
from app.decorators import admin_required
from app import db

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    vendors = User.query.filter_by(user_type='vendor').count()
    retailers = User.query.filter_by(user_type='retailer').count()
    companies = User.query.filter_by(user_type='company').count()
    
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    emergency_products = Product.query.filter_by(is_emergency=True).count()
    
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    completed_orders = Order.query.filter_by(status='delivered').count()
    
    # Revenue
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter_by(payment_status='paid').scalar() or 0
    
    # Products by category
    categories = db.session.query(
        Product.category,
        db.func.count(Product.id)
    ).group_by(Product.category).all()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         vendors=vendors,
                         retailers=retailers,
                         companies=companies,
                         total_products=total_products,
                         active_products=active_products,
                         emergency_products=emergency_products,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         completed_orders=completed_orders,
                         total_revenue=total_revenue,
                         categories=categories,
                         recent_orders=recent_orders)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    user_type = request.args.get('type', 'all')
    
    if user_type == 'all':
        users = User.query.all()
    else:
        users = User.query.filter_by(user_type=user_type).all()
    
    return render_template('admin/users.html', users=users, user_type=user_type)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {status} successfully', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    """Manage products"""
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """Manage orders"""
    status = request.args.get('status', 'all')
    
    if status == 'all':
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter_by(status=status).order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, status_filter=status)

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """View analytics"""
    # Revenue over time (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_revenue = db.session.query(
        db.func.date(Order.created_at).label('date'),
        db.func.sum(Order.total_amount).label('revenue')
    ).filter(
        Order.payment_status == 'paid',
        Order.created_at >= thirty_days_ago
    ).group_by(db.func.date(Order.created_at)).all()
    
    # Top vendors by revenue
    top_vendors = db.session.query(
        User.name,
        db.func.sum(OrderItem.subtotal).label('revenue')
    ).join(Product, User.id == Product.vendor_id)\
     .join(OrderItem, Product.id == OrderItem.product_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.payment_status == 'paid')\
     .group_by(User.id)\
     .order_by(db.desc('revenue'))\
     .limit(10).all()
    
    return render_template('admin/analytics.html',
                         daily_revenue=daily_revenue,
                         top_vendors=top_vendors)
