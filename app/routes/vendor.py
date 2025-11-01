from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.routes import vendor_bp
from app.models import Product, Order, OrderItem
from app.decorators import vendor_required
from app.utils import save_product_image, delete_product_image, calculate_days_to_expiry, get_discount_percentage
from app import db
from datetime import datetime

@vendor_bp.route('/dashboard')
@login_required
@vendor_required
def dashboard():
    """Vendor dashboard"""
    # Get vendor's products
    products = Product.query.filter_by(vendor_id=current_user.id).all()
    active_products = [p for p in products if p.is_active]
    
    # Get orders for vendor's products
    orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        Product.vendor_id == current_user.id
    ).distinct().all()
    
    pending_orders = [o for o in orders if o.status == 'pending']
    
    # Calculate revenue
    total_revenue = sum(item.subtotal for order in orders if order.payment_status == 'paid' 
                       for item in order.items if item.product.vendor_id == current_user.id)
    
    return render_template('vendor/dashboard.html',
                         products=products,
                         active_product_count=len(active_products),
                         pending_order_count=len(pending_orders),
                         total_revenue=total_revenue)

@vendor_bp.route('/products')
@login_required
@vendor_required
def products():
    """List vendor's products"""
    products = Product.query.filter_by(vendor_id=current_user.id).all()
    return render_template('vendor/products.html', products=products)

@vendor_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@vendor_required
def add_product():
    """Add new product"""
    if request.method == 'POST':
        try:
            product_name = request.form.get('product_name')
            category = request.form.get('category')
            description = request.form.get('description')
            price = float(request.form.get('price'))
            quantity = int(request.form.get('quantity'))
            unit = request.form.get('unit')
            expiry_date_str = request.form.get('expiry_date')
            
            # MOQ fields
            moq_enabled = request.form.get('moq_enabled') == 'on'
            moq_type = request.form.get('moq_type') if moq_enabled else None
            minimum_quantity = int(request.form.get('minimum_quantity', 0)) if moq_enabled else None
            minimum_weight = float(request.form.get('minimum_weight', 0)) if moq_enabled else None
            
            # Handle image upload
            image = request.files.get('image')
            image_filename = save_product_image(image, current_user.id) if image else None
            
            # Parse expiry date
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
            
            # Create product
            product = Product(
                vendor_id=current_user.id,
                product_name=product_name,
                category=category,
                description=description,
                price=price,
                quantity=quantity,
                unit=unit,
                expiry_date=expiry_date,
                image_filename=image_filename,
                moq_enabled=moq_enabled,
                moq_type=moq_type,
                minimum_quantity=minimum_quantity,
                minimum_weight=minimum_weight,
                is_active=True
            )
            
            # Check if product should be marked as emergency
            if expiry_date:
                days_to_expiry = calculate_days_to_expiry(expiry_date)
                if days_to_expiry <= 3:
                    product.is_emergency = True
                    product.discount_percentage = get_discount_percentage(days_to_expiry)
            
            db.session.add(product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('vendor.products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
            return render_template('vendor/add_product.html')
    
    return render_template('vendor/add_product.html')

@vendor_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_required
def edit_product(product_id):
    """Edit product"""
    product = Product.query.get_or_404(product_id)
    
    # Check ownership
    if product.vendor_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('vendor.products'))
    
    if request.method == 'POST':
        try:
            product.product_name = request.form.get('product_name')
            product.category = request.form.get('category')
            product.description = request.form.get('description')
            product.price = float(request.form.get('price'))
            product.quantity = int(request.form.get('quantity'))
            product.unit = request.form.get('unit')
            
            expiry_date_str = request.form.get('expiry_date')
            product.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
            
            # MOQ fields
            product.moq_enabled = request.form.get('moq_enabled') == 'on'
            product.moq_type = request.form.get('moq_type') if product.moq_enabled else None
            product.minimum_quantity = int(request.form.get('minimum_quantity', 0)) if product.moq_enabled else None
            product.minimum_weight = float(request.form.get('minimum_weight', 0)) if product.moq_enabled else None
            
            # Handle image update
            image = request.files.get('image')
            if image:
                # Delete old image
                if product.image_filename:
                    delete_product_image(product.image_filename)
                # Save new image
                product.image_filename = save_product_image(image, current_user.id)
            
            # Update emergency status
            if product.expiry_date:
                days_to_expiry = calculate_days_to_expiry(product.expiry_date)
                if days_to_expiry <= 3:
                    product.is_emergency = True
                    product.discount_percentage = get_discount_percentage(days_to_expiry)
                else:
                    product.is_emergency = False
                    product.discount_percentage = 0
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('vendor.products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    
    return render_template('vendor/edit_product.html', product=product)

@vendor_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@vendor_required
def delete_product(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)
    
    # Check ownership
    if product.vendor_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('vendor.products'))
    
    try:
        # Delete image
        if product.image_filename:
            delete_product_image(product.image_filename)
        
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')
    
    return redirect(url_for('vendor.products'))

@vendor_bp.route('/orders')
@login_required
@vendor_required
def orders():
    """View vendor's orders"""
    # Get orders containing vendor's products
    orders = db.session.query(Order).join(OrderItem).join(Product).filter(
        Product.vendor_id == current_user.id
    ).distinct().all()
    
    return render_template('vendor/orders.html', orders=orders)
