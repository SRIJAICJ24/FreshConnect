from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # admin, vendor, retailer, company, driver
    
    # Business details
    business_name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    
    # Company specific
    company_name = db.Column(db.String(200))
    gst_number = db.Column(db.String(50))
    brand_name = db.Column(db.String(100))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='vendor', lazy='dynamic', foreign_keys='Product.vendor_id')
    orders_as_retailer = db.relationship('Order', backref='retailer', lazy='dynamic', foreign_keys='Order.retailer_id')
    credit = db.relationship('RetailerCredit', backref='retailer', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(50), nullable=False)  # kg, liter, piece, etc.
    
    # MOQ fields
    moq_enabled = db.Column(db.Boolean, default=False)
    moq_type = db.Column(db.String(20))  # quantity, weight, both
    minimum_quantity = db.Column(db.Integer)
    minimum_weight = db.Column(db.Float)
    
    # Product details
    expiry_date = db.Column(db.Date)
    image_filename = db.Column(db.String(255))
    is_emergency = db.Column(db.Boolean, default=False)
    discount_percentage = db.Column(db.Float, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    
    def validate_moq(self, quantity, weight=None):
        """Validate if order meets MOQ requirements"""
        if not self.moq_enabled:
            return True, "MOQ not enabled"
        
        if self.moq_type == 'quantity':
            if quantity < self.minimum_quantity:
                return False, f"Minimum {self.minimum_quantity} units required"
        elif self.moq_type == 'weight':
            if weight and weight < self.minimum_weight:
                return False, f"Minimum {self.minimum_weight}kg required"
        elif self.moq_type == 'both':
            if quantity < self.minimum_quantity or (weight and weight < self.minimum_weight):
                return False, f"Minimum {self.minimum_quantity} units and {self.minimum_weight}kg required"
        
        return True, "Valid"
    
    def __repr__(self):
        return f'<Product {self.product_name}>'


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Order details
    total_amount = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_city = db.Column(db.String(100))
    delivery_pincode = db.Column(db.String(10))
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, processing, shipped, delivered
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', uselist=False, cascade='all, delete-orphan')
    driver_assignment = db.relationship('DriverAssignment', backref='order', uselist=False)
    
    def __repr__(self):
        return f'<Order {self.order_id}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float)  # for weight-based MOQ
    price_at_purchase = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='mock_card')
    payment_status = db.Column(db.String(50), default='pending')  # pending, success, failed
    
    # Card details (mock)
    card_last_four = db.Column(db.String(4))
    
    # Retry tracking
    retry_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    initiated_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}>'


class DriverAssignment(db.Model):
    __tablename__ = 'driver_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    
    # Assignment details
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    pickup_time = db.Column(db.DateTime)
    delivery_time = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(50), default='assigned')  # assigned, picked_up, in_transit, delivered
    
    # Earnings
    distance_km = db.Column(db.Float)
    earnings = db.Column(db.Float, default=0)
    
    def __repr__(self):
        return f'<DriverAssignment {self.id}>'


class RetailerCredit(db.Model):
    __tablename__ = 'retailer_credits'
    
    id = db.Column(db.Integer, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Credit score
    credit_score = db.Column(db.Integer, default=500)
    credit_tier = db.Column(db.String(20), default='bronze')  # bronze, silver, gold, platinum
    
    # Purchase history
    total_purchases = db.Column(db.Float, default=0)
    total_orders = db.Column(db.Integer, default=0)
    successful_orders = db.Column(db.Integer, default=0)
    
    # Status
    priority_level = db.Column(db.Integer, default=1)
    
    # Timestamps
    last_purchase_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_tier(self):
        """Calculate credit tier based on score"""
        if self.credit_score >= 751:
            return 'platinum'
        elif self.credit_score >= 501:
            return 'gold'
        elif self.credit_score >= 251:
            return 'silver'
        else:
            return 'bronze'
    
    def update_score(self, order_value, payment_on_time=True):
        """Update credit score after purchase"""
        # Simple scoring logic
        points = 0
        
        # Purchase value component (up to 50 points)
        points += min(50, order_value / 100)
        
        # Payment punctuality (50 points if on time)
        if payment_on_time:
            points += 50
        
        # Add to existing score (max 1000)
        self.credit_score = min(1000, self.credit_score + int(points))
        self.credit_tier = self.calculate_tier()
        self.total_purchases += order_value
        self.total_orders += 1
        self.successful_orders += 1
        self.last_purchase_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<RetailerCredit {self.credit_tier}:{self.credit_score}>'


class Driver(db.Model):
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Vehicle details
    vehicle_type = db.Column(db.String(50), nullable=False)  # motorcycle, auto, van, truck, lorry
    vehicle_registration = db.Column(db.String(50))
    vehicle_capacity_kg = db.Column(db.Float, nullable=False)
    
    # Location
    parking_location = db.Column(db.String(200))
    current_location = db.Column(db.String(200))
    
    # Status
    status = db.Column(db.String(20), default='available')  # available, on_delivery, off_duty
    current_load_kg = db.Column(db.Float, default=0)
    
    # Performance
    rating = db.Column(db.Float, default=4.5)
    total_deliveries = db.Column(db.Integer, default=0)
    successful_deliveries = db.Column(db.Integer, default=0)
    
    # Earnings
    total_earnings = db.Column(db.Float, default=0)
    
    # Timestamps
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='driver_profile', foreign_keys=[user_id])
    assignments = db.relationship('DriverAssignment', backref='driver', lazy='dynamic')
    
    def __repr__(self):
        return f'<Driver {self.id}>'
