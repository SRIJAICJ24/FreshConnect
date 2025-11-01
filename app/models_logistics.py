"""
Delivery & Logistics Models for FreshConnect Marketplace
Complete implementation of driver management, delivery tracking, and logistics system
"""

from app import db
from datetime import datetime, timedelta
import json


class LogisticsCost(db.Model):
    """Logistics cost configuration by delivery area"""
    __tablename__ = 'logistics_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Pricing
    base_rate_per_kg = db.Column(db.Float, nullable=False, default=10.0)
    area_multiplier = db.Column(db.Float, default=1.0)
    minimum_charge = db.Column(db.Float, default=50.0)
    
    # Capacity & Time
    max_weight_kg = db.Column(db.Integer)
    delivery_time_minutes = db.Column(db.Integer, default=45)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_cost(self, weight_kg):
        """Calculate logistics cost for given weight"""
        base_cost = self.base_rate_per_kg * weight_kg * self.area_multiplier
        return max(base_cost, self.minimum_charge)
    
    def __repr__(self):
        return f'<LogisticsCost {self.area_name}>'


class DriverEnhanced(db.Model):
    """Enhanced driver model with complete logistics features"""
    __tablename__ = 'drivers_enhanced'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Personal Info
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False, unique=True)
    email = db.Column(db.String(100))
    
    # Vehicle Details
    vehicle_type = db.Column(db.String(50), nullable=False)  # motorcycle, auto, van, truck, lorry
    vehicle_registration = db.Column(db.String(50), unique=True)
    vehicle_capacity_kg = db.Column(db.Integer, nullable=False)
    vehicle_insured = db.Column(db.Boolean, default=False)
    insurance_expiry = db.Column(db.Date)
    
    # Location
    parking_location = db.Column(db.String(200))  # Base location
    current_location = db.Column(db.String(200))
    current_load_kg = db.Column(db.Float, default=0)
    
    # Status
    status = db.Column(db.String(50), default='off_duty')  # off_duty, available, on_delivery, on_break
    last_active = db.Column(db.DateTime)
    
    # License & Verification
    license_number = db.Column(db.String(50))
    license_expiry = db.Column(db.Date)
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    documents_verified = db.Column(db.Boolean, default=False)
    
    # Performance
    rating = db.Column(db.Float, default=5.0)
    total_deliveries = db.Column(db.Integer, default=0)
    successful_deliveries = db.Column(db.Integer, default=0)
    cancelled_deliveries = db.Column(db.Integer, default=0)
    
    # Earnings
    total_earnings = db.Column(db.Float, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    joined_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='driver_enhanced', foreign_keys=[user_id])
    assignments = db.relationship('DriverAssignmentEnhanced', backref='driver', lazy='dynamic')
    earnings = db.relationship('DriverEarning', backref='driver', lazy='dynamic')
    performance = db.relationship('DriverPerformanceMetrics', backref='driver', uselist=False)
    
    @property
    def available_capacity(self):
        """Calculate available capacity"""
        return self.vehicle_capacity_kg - self.current_load_kg
    
    @property
    def completion_rate(self):
        """Calculate delivery completion rate"""
        if self.total_deliveries == 0:
            return 100.0
        return (self.successful_deliveries / self.total_deliveries) * 100
    
    def can_take_order(self, weight_kg):
        """Check if driver can take an order of given weight"""
        return (self.is_active and 
                self.status in ['available', 'on_break'] and 
                self.available_capacity >= weight_kg)
    
    def __repr__(self):
        return f'<DriverEnhanced {self.name}>'


class DriverAssignmentEnhanced(db.Model):
    """Enhanced driver assignment with complete tracking"""
    __tablename__ = 'driver_assignments_enhanced'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers_enhanced.id'), nullable=False, index=True)
    
    # Status
    assignment_status = db.Column(db.String(50), default='assigned', index=True)
    # assigned, accepted, picked_up, in_transit, out_for_delivery, delivered, cancelled
    
    # Scheduling
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    scheduled_pickup_time = db.Column(db.DateTime)
    actual_pickup_time = db.Column(db.DateTime)
    estimated_delivery_time = db.Column(db.DateTime)
    actual_delivery_time = db.Column(db.DateTime)
    
    # Locations
    pickup_location = db.Column(db.String(300), nullable=False)
    delivery_location = db.Column(db.String(300), nullable=False)
    current_location_lat = db.Column(db.Float)
    current_location_lng = db.Column(db.Float)
    delivery_location_lat = db.Column(db.Float)
    delivery_location_lng = db.Column(db.Float)
    
    # Load Information
    weight_assigned_kg = db.Column(db.Float, nullable=False)
    weight_delivered_kg = db.Column(db.Float)
    actual_distance_km = db.Column(db.Float)
    
    # Ratings & Feedback
    retailer_rating_to_driver = db.Column(db.Integer)  # 1-5
    driver_rating_to_retailer = db.Column(db.Integer)  # 1-5
    retailer_feedback = db.Column(db.Text)
    driver_feedback = db.Column(db.Text)
    
    # Proof & Documentation
    pickup_photo_url = db.Column(db.String(300))
    delivery_photo_url = db.Column(db.String(300))
    delivery_signature_url = db.Column(db.String(300))
    
    # Issues & Resolution
    issue_reported = db.Column(db.Boolean, default=False)
    issue_description = db.Column(db.Text)
    resolution_notes = db.Column(db.Text)
    
    # Payment
    logistics_cost_calculated = db.Column(db.Float)
    driver_earning = db.Column(db.Float)
    cancellation_reason = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', backref='assignment_enhanced', foreign_keys=[order_id])
    tracking_events = db.relationship('DeliveryTrackingEvent', backref='assignment', lazy='dynamic')
    earning_record = db.relationship('DriverEarning', backref='assignment', uselist=False)
    
    @property
    def is_delayed(self):
        """Check if delivery is delayed"""
        if not self.estimated_delivery_time or self.assignment_status == 'delivered':
            return False
        return datetime.utcnow() > self.estimated_delivery_time
    
    @property
    def delay_minutes(self):
        """Calculate delay in minutes"""
        if not self.is_delayed:
            return 0
        return int((datetime.utcnow() - self.estimated_delivery_time).total_seconds() / 60)
    
    @property
    def time_until_delivery(self):
        """Minutes until estimated delivery"""
        if not self.estimated_delivery_time or self.assignment_status == 'delivered':
            return 0
        diff = (self.estimated_delivery_time - datetime.utcnow()).total_seconds() / 60
        return max(0, int(diff))
    
    def __repr__(self):
        return f'<DriverAssignmentEnhanced Order:{self.order_id}>'


class DriverEarning(db.Model):
    """Driver earnings with detailed breakdown"""
    __tablename__ = 'driver_earnings'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers_enhanced.id'), nullable=False, index=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('driver_assignments_enhanced.id'), nullable=False, unique=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Earnings Breakdown
    base_rate_per_kg = db.Column(db.Float, nullable=False)
    weight_delivered_kg = db.Column(db.Float, nullable=False)
    base_earning = db.Column(db.Float)
    
    # Incentives & Deductions
    on_time_bonus = db.Column(db.Float, default=0)
    quality_bonus = db.Column(db.Float, default=0)
    cancellation_deduction = db.Column(db.Float, default=0)
    late_delivery_deduction = db.Column(db.Float, default=0)
    
    total_earning = db.Column(db.Float)
    
    # Payment Status
    earning_status = db.Column(db.String(50), default='pending')  # pending, held, released, paid
    payment_status = db.Column(db.String(50), default='unpaid')  # unpaid, paid
    hold_reason = db.Column(db.Text)
    payment_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    paid_at = db.Column(db.DateTime)
    
    # Relationships
    order = db.relationship('Order', backref='driver_earning', foreign_keys=[order_id])
    
    def calculate_total(self):
        """Calculate total earning"""
        self.total_earning = (self.base_earning + self.on_time_bonus + 
                            self.quality_bonus - self.cancellation_deduction - 
                            self.late_delivery_deduction)
        return self.total_earning
    
    def __repr__(self):
        return f'<DriverEarning ₹{self.total_earning}>'


class DeliveryTrackingEvent(db.Model):
    """Real-time delivery tracking events"""
    __tablename__ = 'delivery_tracking_events'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('driver_assignments_enhanced.id'), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers_enhanced.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    
    # Event Details
    event_type = db.Column(db.String(50), nullable=False)
    # assignment, accepted, pickup_at_vendor, left_vendor, in_transit, near_delivery, arrived_delivery, delivered, issue_reported, completed
    event_description = db.Column(db.String(300))
    
    # Location
    location = db.Column(db.String(300))
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    
    # Media
    event_photos = db.Column(db.Text)  # JSON array of URLs
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    order = db.relationship('Order', backref='tracking_events', foreign_keys=[order_id])
    
    def __repr__(self):
        return f'<TrackingEvent {self.event_type}>'


class DeliveryNotification(db.Model):
    """Notifications for retailers, vendors, and drivers"""
    __tablename__ = 'delivery_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('driver_assignments_enhanced.id'))
    
    # Recipient
    recipient_type = db.Column(db.String(50), nullable=False)  # retailer, vendor, driver
    recipient_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Notification Content
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    
    # Driver Contact (for in-transit notifications)
    driver_name = db.Column(db.String(100))
    driver_phone = db.Column(db.String(15))
    vehicle_details = db.Column(db.String(200))
    estimated_arrival = db.Column(db.Time)
    
    # Status
    is_read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime)
    action_url = db.Column(db.String(500))
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    order = db.relationship('Order', backref='notifications', foreign_keys=[order_id])
    
    def __repr__(self):
        return f'<Notification {self.notification_type}>'


class DriverPerformanceMetrics(db.Model):
    """Driver performance metrics and statistics"""
    __tablename__ = 'driver_performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers_enhanced.id'), nullable=False, unique=True)
    
    # Order Metrics
    total_orders = db.Column(db.Integer, default=0)
    completed_orders = db.Column(db.Integer, default=0)
    cancelled_orders = db.Column(db.Integer, default=0)
    late_deliveries = db.Column(db.Integer, default=0)
    on_time_percentage = db.Column(db.Float)
    
    # Rating Breakdown
    average_rating = db.Column(db.Float, default=5.0)
    five_star_count = db.Column(db.Integer, default=0)
    four_star_count = db.Column(db.Integer, default=0)
    three_star_count = db.Column(db.Integer, default=0)
    two_star_count = db.Column(db.Integer, default=0)
    one_star_count = db.Column(db.Integer, default=0)
    
    # Delivery Stats
    total_weight_delivered_kg = db.Column(db.Float)
    average_delivery_time_minutes = db.Column(db.Integer)
    
    # Reliability
    acceptance_rate = db.Column(db.Float)
    completion_rate = db.Column(db.Float)
    issue_rate = db.Column(db.Float)
    
    # Monthly Performance
    current_month_orders = db.Column(db.Integer)
    current_month_earnings = db.Column(db.Float)
    current_month_on_time_percentage = db.Column(db.Float)
    
    # Timestamp
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def update_metrics(self):
        """Recalculate all metrics"""
        driver = DriverEnhanced.query.get(self.driver_id)
        
        if driver:
            self.total_orders = driver.total_deliveries
            self.completed_orders = driver.successful_deliveries
            self.cancelled_orders = driver.cancelled_deliveries
            
            if self.total_orders > 0:
                self.completion_rate = (self.completed_orders / self.total_orders) * 100
            
            self.average_rating = driver.rating
            self.last_updated = datetime.utcnow()
    
    def __repr__(self):
        return f'<DriverMetrics Driver:{self.driver_id}>'
