from flask import render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import current_user, login_required
from app.routes import retailer_bp
from app.models import Product, Order, OrderItem, Payment, RetailerCredit
from app.decorators import retailer_required
from app.utils import generate_order_id, generate_transaction_id, validate_card_number
from app import db
from datetime import datetime

@retailer_bp.route('/dashboard')
@login_required
@retailer_required
def dashboard():
    """Retailer dashboard"""
    # Get credit info
    credit = RetailerCredit.query.filter_by(retailer_id=current_user.id).first()
    if not credit:
        credit = RetailerCredit(retailer_id=current_user.id)
        db.session.add(credit)
        db.session.commit()
    
    # Get orders
    orders = Order.query.filter_by(retailer_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    
    # Get product counts by category
    categories = db.session.query(Product.category, db.func.count(Product.id)).filter_by(is_active=True).group_by(Product.category).all()
    
    return render_template('retailer/dashboard.html',
                         credit=credit,
                         orders=orders,
                         categories=categories)

@retailer_bp.route('/browse')
@login_required
@retailer_required
def browse():
    """Browse products"""
    category = request.args.get('category')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Product.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.product_name.like(f'%{search}%'))
    
    products = query.paginate(page=page, per_page=20, error_out=False)
    categories = db.session.query(Product.category).distinct().all()
    
    return render_template('retailer/browse.html',
                         products=products,
                         categories=[c[0] for c in categories],
                         current_category=category,
                         search=search)

@retailer_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
@retailer_required
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    weight = float(request.form.get('weight', 0)) if request.form.get('weight') else None
    
    # Validate MOQ
    if product.moq_enabled:
        is_valid, message = product.validate_moq(quantity, weight)
        if not is_valid:
            return jsonify({'success': False, 'message': message}), 400
    
    # Get or create cart in session
    cart = session.get('cart', {})
    
    product_key = str(product_id)
    if product_key in cart:
        cart[product_key]['quantity'] += quantity
        if weight:
            cart[product_key]['weight'] = cart[product_key].get('weight', 0) + weight
    else:
        cart[product_key] = {
            'product_id': product_id,
            'quantity': quantity,
            'weight': weight,
            'price': product.price
        }
    
    session['cart'] = cart
    session.modified = True
    
    return jsonify({'success': True, 'message': 'Added to cart', 'cart_count': len(cart)})

@retailer_bp.route('/cart')
@login_required
@retailer_required
def cart():
    """View cart"""
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for item in cart.values():
        product = Product.query.get(item['product_id'])
        if product and product.is_active:
            subtotal = product.price * item['quantity']
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'weight': item.get('weight'),
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('retailer/cart.html', cart_items=cart_items, total=total)

@retailer_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
@retailer_required
def remove_from_cart(product_id):
    """Remove item from cart"""
    cart = session.get('cart', {})
    product_key = str(product_id)
    
    if product_key in cart:
        del cart[product_key]
        session['cart'] = cart
        session.modified = True
        flash('Item removed from cart', 'success')
    
    return redirect(url_for('retailer.cart'))

@retailer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
@retailer_required
def checkout():
    """Checkout and create order"""
    cart = session.get('cart', {})
    
    if not cart:
        flash('Cart is empty', 'warning')
        return redirect(url_for('retailer.browse'))
    
    if request.method == 'POST':
        try:
            # Create order
            order_id = generate_order_id()
            delivery_address = request.form.get('delivery_address')
            delivery_city = request.form.get('delivery_city')
            delivery_pincode = request.form.get('delivery_pincode')
            
            # Calculate total
            total = 0
            for item in cart.values():
                product = Product.query.get(item['product_id'])
                total += product.price * item['quantity']
            
            order = Order(
                order_id=order_id,
                retailer_id=current_user.id,
                total_amount=total,
                delivery_address=delivery_address,
                delivery_city=delivery_city,
                delivery_pincode=delivery_pincode,
                status='pending',
                payment_status='pending'
            )
            db.session.add(order)
            db.session.flush()  # Get order.id
            
            # Create order items
            for item in cart.values():
                product = Product.query.get(item['product_id'])
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item['quantity'],
                    weight=item.get('weight'),
                    price_at_purchase=product.price,
                    subtotal=product.price * item['quantity']
                )
                db.session.add(order_item)
            
            db.session.commit()
            
            # Clear cart
            session.pop('cart', None)
            
            # Redirect to payment
            return redirect(url_for('retailer.payment', order_id=order.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating order: {str(e)}', 'danger')
            return redirect(url_for('retailer.cart'))
    
    # Calculate cart total
    total = 0
    for item in cart.values():
        product = Product.query.get(item['product_id'])
        total += product.price * item['quantity']
    
    return render_template('retailer/checkout.html', cart=cart, total=total)

@retailer_bp.route('/payment/<int:order_id>', methods=['GET', 'POST'])
@login_required
@retailer_required
def payment(order_id):
    """Process payment"""
    order = Order.query.get_or_404(order_id)
    
    # Check ownership
    if order.retailer_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('retailer.dashboard'))
    
    if request.method == 'POST':
        try:
            card_number = request.form.get('card_number')
            card_expiry = request.form.get('card_expiry')
            card_cvv = request.form.get('card_cvv')
            
            # Generate transaction ID
            transaction_id = generate_transaction_id()
            
            # Mock payment validation
            payment_success = validate_card_number(card_number)
            
            # Create payment record
            payment = Payment(
                order_id=order.id,
                transaction_id=transaction_id,
                amount=order.total_amount,
                payment_method='mock_card',
                card_last_four=card_number[-4:] if card_number else '0000',
                payment_status='success' if payment_success else 'failed'
            )
            
            if payment_success:
                payment.completed_at = datetime.utcnow()
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.confirmed_at = datetime.utcnow()
                
                # Deduct inventory
                for item in order.items:
                    product = item.product
                    product.quantity -= item.quantity
                
                # Update credit score
                credit = RetailerCredit.query.filter_by(retailer_id=current_user.id).first()
                if credit:
                    credit.update_score(order.total_amount, payment_on_time=True)
                
                flash('Payment successful! Order confirmed.', 'success')
            else:
                flash('Payment failed. Please try again.', 'danger')
            
            db.session.add(payment)
            db.session.commit()
            
            if payment_success:
                return redirect(url_for('retailer.order_detail', order_id=order.id))
            else:
                return redirect(url_for('retailer.payment', order_id=order.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Payment error: {str(e)}', 'danger')
    
    return render_template('retailer/payment.html', order=order)

@retailer_bp.route('/orders')
@login_required
@retailer_required
def orders():
    """View order history"""
    orders = Order.query.filter_by(retailer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('retailer/orders.html', orders=orders)

@retailer_bp.route('/orders/<int:order_id>')
@login_required
@retailer_required
def order_detail(order_id):
    """View order details"""
    order = Order.query.get_or_404(order_id)
    
    # Check ownership
    if order.retailer_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('retailer.orders'))
    
    return render_template('retailer/order_detail.html', order=order)

@retailer_bp.route('/credit')
@login_required
@retailer_required
def credit_dashboard():
    """View credit dashboard"""
    credit = RetailerCredit.query.filter_by(retailer_id=current_user.id).first()
    if not credit:
        credit = RetailerCredit(retailer_id=current_user.id)
        db.session.add(credit)
        db.session.commit()
    
    # Get tier benefits
    from config import Config
    benefits = Config.TIER_BENEFITS.get(credit.credit_tier, [])
    
    return render_template('retailer/credit_dashboard.html', credit=credit, benefits=benefits)
