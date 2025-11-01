"""
Driver Assignment Service - Intelligent Matching Algorithm
Complete implementation of driver assignment, tracking, and earnings
"""

from app import db
from app.models import Order, User
from app.models_logistics import (
    DriverEnhanced, DriverAssignmentEnhanced, DriverEarning,
    DeliveryTrackingEvent, DeliveryNotification, LogisticsCost,
    DriverPerformanceMetrics
)
from datetime import datetime, timedelta
import random


class DriverAssignmentService:
    """Intelligent driver matching and assignment with location awareness"""
    
    VEHICLE_CAPACITY = {
        'motorcycle': 25,
        'auto': 50,
        'van': 100,
        'truck': 250,
        'lorry': 500
    }
    
    @staticmethod
    def calculate_fitness_score(driver, order_weight, delivery_area):
        """
        Calculate driver fitness score (0-100)
        Components:
        - Vehicle capacity match: 30%
        - Location proximity: 25%
        - Driver rating: 25%
        - Current load optimization: 20%
        """
        
        # Component 1: Capacity Check (30 points max)
        available_capacity = driver.vehicle_capacity_kg - driver.current_load_kg
        
        if available_capacity < order_weight:
            return -1  # Cannot take this order
        
        capacity_utilization = ((driver.vehicle_capacity_kg - available_capacity + order_weight) 
                               / driver.vehicle_capacity_kg)
        capacity_score = capacity_utilization * 30
        
        # Component 2: Location Proximity (25 points max)
        if driver.parking_location == delivery_area:
            location_score = 25  # Same area
        elif driver.parking_location and delivery_area and driver.parking_location[:5] == delivery_area[:5]:
            location_score = 20  # Same zone
        else:
            location_score = 10  # Different zone
        
        # Component 3: Driver Rating (25 points max)
        rating_score = (driver.rating / 5.0) * 25 if driver.rating > 0 else 15
        
        # Component 4: Load Optimization (20 points max)
        if 0.7 <= capacity_utilization <= 0.9:
            load_score = 20
        elif 0.5 <= capacity_utilization < 0.7 or 0.9 < capacity_utilization <= 1.0:
            load_score = 15
        else:
            load_score = 10
        
        total_score = capacity_score + location_score + rating_score + load_score
        
        return min(100, total_score)
    
    @staticmethod
    def find_best_driver(order_weight, delivery_area, max_wait_minutes=15):
        """
        Find the best available driver for the order
        
        Selection criteria:
        1. Status = 'available' or 'on_break'
        2. Has sufficient capacity
        3. Highest fitness score
        """
        
        available_drivers = DriverEnhanced.query.filter(
            DriverEnhanced.is_active == True,
            DriverEnhanced.status.in_(['available', 'on_break'])
        ).all()
        
        if not available_drivers:
            return None, "No drivers available at this time"
        
        # Calculate fitness for each driver
        candidates = []
        for driver in available_drivers:
            fitness_score = DriverAssignmentService.calculate_fitness_score(
                driver, order_weight, delivery_area
            )
            
            if fitness_score >= 0:  # Can take this order
                candidates.append({
                    'driver': driver,
                    'fitness_score': fitness_score
                })
        
        if not candidates:
            return None, "No drivers with sufficient capacity"
        
        # Sort by fitness score (highest first)
        candidates.sort(key=lambda x: x['fitness_score'], reverse=True)
        
        best_driver = candidates[0]['driver']
        
        return best_driver, f"Driver {best_driver.name} selected (Score: {candidates[0]['fitness_score']:.1f}/100)"
    
    @staticmethod
    def assign_driver_to_order(order_id, order_weight, delivery_area, pickup_location):
        """
        Assign best driver to order and create assignment record
        """
        
        try:
            order = Order.query.get_or_404(order_id)
            
            # Find best driver
            best_driver, message = DriverAssignmentService.find_best_driver(
                order_weight, delivery_area
            )
            
            if not best_driver:
                return False, message
            
            # Get logistics cost
            logistics_cost = DriverAssignmentService.calculate_logistics_cost(
                order_weight, delivery_area
            )
            
            # Create assignment
            assignment = DriverAssignmentEnhanced(
                order_id=order_id,
                driver_id=best_driver.id,
                assignment_status='assigned',
                assigned_at=datetime.utcnow(),
                
                pickup_location=pickup_location,
                delivery_location=order.delivery_address,
                weight_assigned_kg=order_weight,
                
                logistics_cost_calculated=logistics_cost['total_cost'],
                driver_earning=DriverAssignmentService.calculate_driver_earning(
                    order_weight, logistics_cost['base_cost']
                )
            )
            
            # Calculate estimated times
            assignment.scheduled_pickup_time = datetime.utcnow() + timedelta(minutes=15)
            assignment.estimated_delivery_time = assignment.scheduled_pickup_time + timedelta(
                minutes=logistics_cost['delivery_time_minutes']
            )
            
            # Update driver status
            best_driver.current_load_kg += order_weight
            if best_driver.status == 'available':
                best_driver.status = 'on_delivery'
            
            db.session.add(assignment)
            db.session.commit()
            
            # Create tracking event
            DriverAssignmentService.create_tracking_event(
                assignment_id=assignment.id,
                driver_id=best_driver.id,
                order_id=order_id,
                event_type='assignment',
                event_description=f'Order assigned to driver {best_driver.name}'
            )
            
            # Create notifications
            DriverAssignmentService.create_notification(
                order_id=order_id,
                assignment_id=assignment.id,
                recipient_type='driver',
                recipient_id=best_driver.user_id,
                notification_type='new_delivery_assignment',
                title='New Delivery Assignment',
                message=f'New order to deliver {order_weight}kg to {delivery_area}'
            )
            
            return True, f"Driver {best_driver.name} assigned successfully"
        
        except Exception as e:
            db.session.rollback()
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def calculate_logistics_cost(weight_kg, delivery_area):
        """Calculate logistics cost based on weight and area"""
        
        logistics = LogisticsCost.query.filter_by(area_name=delivery_area, is_active=True).first()
        
        if not logistics:
            # Fallback to default
            logistics = LogisticsCost.query.filter_by(area_name='Central Koyambedu').first()
            if not logistics:
                # Use defaults
                return {
                    'base_cost': weight_kg * 10.0,
                    'total_cost': max(weight_kg * 10.0, 50.0),
                    'weight_kg': weight_kg,
                    'rate_per_kg': 10.0,
                    'area_multiplier': 1.0,
                    'delivery_time_minutes': 45
                }
        
        base_cost = logistics.base_rate_per_kg * weight_kg * logistics.area_multiplier
        total_cost = max(base_cost, logistics.minimum_charge)
        
        return {
            'base_cost': base_cost,
            'total_cost': total_cost,
            'weight_kg': weight_kg,
            'rate_per_kg': logistics.base_rate_per_kg,
            'area_multiplier': logistics.area_multiplier,
            'delivery_time_minutes': logistics.delivery_time_minutes
        }
    
    @staticmethod
    def calculate_driver_earning(weight_kg, base_logistics_cost):
        """Calculate base driver earning from delivery"""
        rate_per_kg = 10.0  # ₹10 per kg
        base_earning = weight_kg * rate_per_kg
        return base_earning
    
    @staticmethod
    def accept_assignment(assignment_id, driver_user_id):
        """Driver accepts delivery assignment"""
        try:
            # Get driver by user_id
            driver = DriverEnhanced.query.filter_by(user_id=driver_user_id).first()
            if not driver:
                return False, "Driver profile not found"
            
            assignment = DriverAssignmentEnhanced.query.get_or_404(assignment_id)
            
            if assignment.driver_id != driver.id:
                return False, "Unauthorized"
            
            if assignment.assignment_status != 'assigned':
                return False, "Assignment already processed"
            
            assignment.assignment_status = 'accepted'
            assignment.accepted_at = datetime.utcnow()
            
            driver.status = 'on_delivery'
            driver.last_active = datetime.utcnow()
            
            db.session.commit()
            
            # Create tracking event
            DriverAssignmentService.create_tracking_event(
                assignment_id=assignment.id,
                driver_id=driver.id,
                order_id=assignment.order_id,
                event_type='accepted',
                event_description='Driver accepted the delivery'
            )
            
            return True, "Assignment accepted successfully"
        
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def mark_pickup(assignment_id, driver_user_id, photos=None):
        """Mark order as picked up from vendor"""
        try:
            driver = DriverEnhanced.query.filter_by(user_id=driver_user_id).first()
            if not driver:
                return False, "Driver profile not found"
            
            assignment = DriverAssignmentEnhanced.query.get_or_404(assignment_id)
            
            if assignment.driver_id != driver.id:
                return False, "Unauthorized"
            
            assignment.assignment_status = 'picked_up'
            assignment.actual_pickup_time = datetime.utcnow()
            if photos:
                assignment.pickup_photo_url = photos
            
            db.session.commit()
            
            # Create tracking event
            DriverAssignmentService.create_tracking_event(
                assignment_id=assignment.id,
                driver_id=driver.id,
                order_id=assignment.order_id,
                event_type='pickup_at_vendor',
                event_description='Order picked up from vendor'
            )
            
            return True, "Pickup marked successfully"
        
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def mark_delivery(assignment_id, driver_user_id, photos=None, signature_url=None):
        """Mark order as delivered to retailer"""
        try:
            driver = DriverEnhanced.query.filter_by(user_id=driver_user_id).first()
            if not driver:
                return False, "Driver profile not found"
            
            assignment = DriverAssignmentEnhanced.query.get_or_404(assignment_id)
            
            if assignment.driver_id != driver.id:
                return False, "Unauthorized"
            
            assignment.assignment_status = 'delivered'
            assignment.actual_delivery_time = datetime.utcnow()
            if photos:
                assignment.delivery_photo_url = photos
            if signature_url:
                assignment.delivery_signature_url = signature_url
            
            # Calculate delay
            delay_minutes = 0
            if assignment.estimated_delivery_time:
                delay_minutes = (assignment.actual_delivery_time - assignment.estimated_delivery_time).total_seconds() / 60
            
            # Update driver
            driver.current_load_kg -= assignment.weight_assigned_kg
            driver.status = 'available'
            driver.total_deliveries += 1
            driver.successful_deliveries += 1
            driver.last_active = datetime.utcnow()
            
            # Calculate earnings
            earnings = DriverEarning()
            earnings.driver_id = driver.id
            earnings.assignment_id = assignment.id
            earnings.order_id = assignment.order_id
            
            # Base earning
            earnings.base_rate_per_kg = 10.0
            earnings.weight_delivered_kg = assignment.weight_assigned_kg
            earnings.base_earning = earnings.weight_delivered_kg * earnings.base_rate_per_kg
            
            # On-time bonus
            if delay_minutes <= 0:
                earnings.on_time_bonus = earnings.base_earning * 0.10  # 10% bonus
            
            # Late delivery deduction
            if delay_minutes > 15:
                late_fee = (delay_minutes / 60) * 20  # ₹20 per hour late
                earnings.late_delivery_deduction = min(late_fee, earnings.base_earning * 0.20)
            
            earnings.calculate_total()
            earnings.earning_status = 'pending'
            
            driver.total_earnings += earnings.total_earning
            
            db.session.add(earnings)
            db.session.commit()
            
            # Create tracking event
            DriverAssignmentService.create_tracking_event(
                assignment_id=assignment.id,
                driver_id=driver.id,
                order_id=assignment.order_id,
                event_type='delivered',
                event_description='Order successfully delivered'
            )
            
            # Create notification
            DriverAssignmentService.create_notification(
                order_id=assignment.order_id,
                assignment_id=assignment.id,
                recipient_type='driver',
                recipient_id=driver.user_id,
                notification_type='delivery_completed_earnings',
                title=f'Delivery Complete! Earned ₹{earnings.total_earning:.2f}',
                message=f'Base: ₹{earnings.base_earning:.2f}, Bonus: ₹{earnings.on_time_bonus:.2f}'
            )
            
            return True, f"Delivery marked successfully. Earned ₹{earnings.total_earning:.2f}"
        
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def create_tracking_event(assignment_id, driver_id, order_id, event_type, event_description, location=None):
        """Create a delivery tracking event"""
        try:
            event = DeliveryTrackingEvent(
                assignment_id=assignment_id,
                driver_id=driver_id,
                order_id=order_id,
                event_type=event_type,
                event_description=event_description,
                location=location
            )
            db.session.add(event)
            db.session.commit()
            return True
        except:
            return False
    
    @staticmethod
    def create_notification(order_id, assignment_id, recipient_type, recipient_id, 
                          notification_type, title, message, **kwargs):
        """Create notification for retailer, vendor, or driver"""
        try:
            notification = DeliveryNotification(
                order_id=order_id,
                assignment_id=assignment_id,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                notification_type=notification_type,
                title=title,
                message=message,
                driver_name=kwargs.get('driver_name'),
                driver_phone=kwargs.get('driver_phone'),
                vehicle_details=kwargs.get('vehicle_details'),
                estimated_arrival=kwargs.get('estimated_arrival')
            )
            db.session.add(notification)
            db.session.commit()
            return True
        except:
            return False
    
    @staticmethod
    def get_driver_assignments(driver_user_id, status=None):
        """Get driver's assignments"""
        driver = DriverEnhanced.query.filter_by(user_id=driver_user_id).first()
        if not driver:
            return []
        
        query = DriverAssignmentEnhanced.query.filter_by(driver_id=driver.id)
        
        if status:
            query = query.filter_by(assignment_status=status)
        
        return query.order_by(DriverAssignmentEnhanced.created_at.desc()).all()
    
    @staticmethod
    def get_driver_earnings(driver_user_id, period='all'):
        """Get driver earnings"""
        driver = DriverEnhanced.query.filter_by(user_id=driver_user_id).first()
        if not driver:
            return []
        
        query = DriverEarning.query.filter_by(driver_id=driver.id)
        
        if period == 'today':
            query = query.filter(db.func.date(DriverEarning.created_at) == datetime.utcnow().date())
        elif period == 'week':
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(DriverEarning.created_at >= week_ago)
        elif period == 'month':
            month_ago = datetime.utcnow() - timedelta(days=30)
            query = query.filter(DriverEarning.created_at >= month_ago)
        
        return query.order_by(DriverEarning.created_at.desc()).all()
    
    @staticmethod
    def get_driver_notifications(driver_user_id, unread_only=False):
        """Get driver notifications"""
        driver = DriverEnhanced.query.filter_by(user_id=driver_user_id).first()
        if not driver:
            return []
        
        query = DeliveryNotification.query.filter_by(
            recipient_type='driver',
            recipient_id=driver.user_id
        )
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(DeliveryNotification.created_at.desc()).all()
