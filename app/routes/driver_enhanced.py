"""
Driver Routes - Complete Delivery & Logistics System
All endpoints for driver dashboard, assignments, tracking, and earnings
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required

# Create separate blueprint for enhanced driver routes
driver_enhanced_bp = Blueprint('driver_enhanced', __name__)
from app.models_logistics import (
    DriverEnhanced, DriverAssignmentEnhanced, DriverEarning,
    DeliveryTrackingEvent, DeliveryNotification, DriverPerformanceMetrics
)
from app.driver_service import DriverAssignmentService
from app import db
from datetime import datetime, timedelta


def driver_required(f):
    """Decorator to require driver role"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'driver':
            flash('Access denied. Driver access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# ============================================================================
# 1. DRIVER DASHBOARD
# ============================================================================

@driver_enhanced_bp.route('/dashboard/enhanced')
@login_required
@driver_required
def dashboard_enhanced():
    """Enhanced driver dashboard with complete metrics"""
    
    # Get driver profile
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Pending assignments (awaiting acceptance)
    pending_assignments = DriverAssignmentService.get_driver_assignments(
        current_user.id, status='assigned'
    )
    
    # Active deliveries (accepted, picked_up, in_transit)
    active_assignments = DriverAssignmentEnhanced.query.filter(
        DriverAssignmentEnhanced.driver_id == driver.id,
        DriverAssignmentEnhanced.assignment_status.in_(['accepted', 'picked_up', 'in_transit'])
    ).all()
    
    # Today's completed deliveries
    today_completed = DriverAssignmentEnhanced.query.filter(
        DriverAssignmentEnhanced.driver_id == driver.id,
        DriverAssignmentEnhanced.assignment_status == 'delivered',
        db.func.date(DriverAssignmentEnhanced.actual_delivery_time) == datetime.utcnow().date()
    ).count()
    
    # Today's earnings
    today_earnings = db.session.query(db.func.sum(DriverEarning.total_earning)).filter(
        DriverEarning.driver_id == driver.id,
        db.func.date(DriverEarning.created_at) == datetime.utcnow().date()
    ).scalar() or 0
    
    # Week's earnings
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_earnings = db.session.query(db.func.sum(DriverEarning.total_earning)).filter(
        DriverEarning.driver_id == driver.id,
        DriverEarning.created_at >= week_ago
    ).scalar() or 0
    
    # Unread notifications
    unread_notifications = DeliveryNotification.query.filter_by(
        recipient_type='driver',
        recipient_id=current_user.id,
        is_read=False
    ).count()
    
    # Performance metrics
    performance = DriverPerformanceMetrics.query.filter_by(driver_id=driver.id).first()
    
    return render_template('driver/dashboard_enhanced.html',
                         driver=driver,
                         pending_count=len(pending_assignments),
                         pending_assignments=pending_assignments[:5],  # Show top 5
                         active_assignments=active_assignments,
                         today_completed=today_completed,
                         today_earnings=today_earnings,
                         week_earnings=week_earnings,
                         unread_notifications=unread_notifications,
                         performance=performance)


# ============================================================================
# 2. ASSIGNMENT MANAGEMENT
# ============================================================================

@driver_enhanced_bp.route('/assignments/enhanced')
@login_required
@driver_required
def assignments_enhanced():
    """List all driver assignments"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Get filter from query params
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        assignments = DriverAssignmentService.get_driver_assignments(current_user.id)
    else:
        assignments = DriverAssignmentService.get_driver_assignments(current_user.id, status=status_filter)
    
    return render_template('driver/assignments_enhanced.html',
                         driver=driver,
                         assignments=assignments,
                         status_filter=status_filter)


@driver_enhanced_bp.route('/assignments/<int:assignment_id>/details')
@login_required
@driver_required
def assignment_details(assignment_id):
    """View full assignment details"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    assignment = DriverAssignmentEnhanced.query.get_or_404(assignment_id)
    
    # Verify ownership
    if assignment.driver_id != driver.id:
        flash('Access denied', 'danger')
        return redirect(url_for('driver_enhanced.assignments_enhanced'))
    
    # Get tracking events
    tracking_events = DeliveryTrackingEvent.query.filter_by(
        assignment_id=assignment_id
    ).order_by(DeliveryTrackingEvent.timestamp.desc()).all()
    
    return render_template('driver/assignment_details.html',
                         driver=driver,
                         assignment=assignment,
                         tracking_events=tracking_events)


@driver_enhanced_bp.route('/assignments/<int:assignment_id>/accept', methods=['POST'])
@login_required
@driver_required
def accept_assignment(assignment_id):
    """Accept a delivery assignment"""
    
    success, message = DriverAssignmentService.accept_assignment(assignment_id, current_user.id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('driver_enhanced.assignment_details', assignment_id=assignment_id))


@driver_enhanced_bp.route('/assignments/<int:assignment_id>/reject', methods=['POST'])
@login_required
@driver_required
def reject_assignment(assignment_id):
    """Reject a delivery assignment"""
    
    reason = request.form.get('reason', 'Driver not available')
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    assignment = DriverAssignmentEnhanced.query.get_or_404(assignment_id)
    
    if assignment.driver_id != driver.id:
        flash('Access denied', 'danger')
        return redirect(url_for('driver_enhanced.assignments_enhanced'))
    
    # Reject assignment
    assignment.assignment_status = 'cancelled'
    assignment.cancellation_reason = reason
    
    # Release driver load
    driver.current_load_kg -= assignment.weight_assigned_kg
    
    db.session.commit()
    
    flash(f'Assignment rejected: {reason}', 'info')
    return redirect(url_for('driver_enhanced.assignments_enhanced'))


# ============================================================================
# 3. DELIVERY TRACKING
# ============================================================================

@driver_enhanced_bp.route('/assignments/<int:assignment_id>/pickup', methods=['POST'])
@login_required
@driver_required
def mark_pickup(assignment_id):
    """Mark order as picked up from vendor"""
    
    photos = request.form.get('photos')  # In production, handle file upload
    
    success, message = DriverAssignmentService.mark_pickup(
        assignment_id, current_user.id, photos
    )
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('driver_enhanced.assignment_details', assignment_id=assignment_id))


@driver_enhanced_bp.route('/assignments/<int:assignment_id>/in-transit', methods=['POST'])
@login_required
@driver_required
def mark_in_transit(assignment_id):
    """Mark order as in transit"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    assignment = DriverAssignmentEnhanced.query.get_or_404(assignment_id)
    
    if assignment.driver_id != driver.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    assignment.assignment_status = 'in_transit'
    db.session.commit()
    
    # Create tracking event
    DriverAssignmentService.create_tracking_event(
        assignment_id=assignment.id,
        driver_id=driver.id,
        order_id=assignment.order_id,
        event_type='in_transit',
        event_description='Order is in transit'
    )
    
    return jsonify({'success': True, 'message': 'Status updated to in transit'})


@driver_enhanced_bp.route('/assignments/<int:assignment_id>/near-delivery', methods=['POST'])
@login_required
@driver_required
def mark_near_delivery(assignment_id):
    """Notify retailer driver is near delivery location"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    assignment = DriverAssignmentEnhanced.query.get_or_404(assignment_id)
    
    if assignment.driver_id != driver.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Create tracking event
    DriverAssignmentService.create_tracking_event(
        assignment_id=assignment.id,
        driver_id=driver.id,
        order_id=assignment.order_id,
        event_type='near_delivery',
        event_description='Driver is near delivery location'
    )
    
    # Create notification for retailer
    DriverAssignmentService.create_notification(
        order_id=assignment.order_id,
        assignment_id=assignment.id,
        recipient_type='retailer',
        recipient_id=assignment.order.retailer_id,
        notification_type='driver_arriving',
        title='Driver Arriving Soon!',
        message=f'{driver.name} is near your location and will arrive in 5-10 minutes'
    )
    
    return jsonify({'success': True, 'message': 'Retailer notified'})


@driver_enhanced_bp.route('/assignments/<int:assignment_id>/deliver', methods=['POST'])
@login_required
@driver_required
def mark_delivered(assignment_id):
    """Mark order as delivered to retailer"""
    
    photos = request.form.get('photos')
    signature_url = request.form.get('signature_url')
    
    success, message = DriverAssignmentService.mark_delivery(
        assignment_id, current_user.id, photos, signature_url
    )
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('driver_enhanced.earnings_enhanced'))


# ============================================================================
# 4. DRIVER PROFILE & EARNINGS
# ============================================================================

@driver_enhanced_bp.route('/profile/enhanced')
@login_required
@driver_required
def profile_enhanced():
    """Driver profile with complete details"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Performance metrics
    performance = DriverPerformanceMetrics.query.filter_by(driver_id=driver.id).first()
    
    return render_template('driver/profile_enhanced.html',
                         driver=driver,
                         performance=performance)


@driver_enhanced_bp.route('/earnings/enhanced')
@login_required
@driver_required
def earnings_enhanced():
    """Driver earnings dashboard"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Get period from query params
    period = request.args.get('period', 'all')
    
    earnings = DriverAssignmentService.get_driver_earnings(current_user.id, period)
    
    # Calculate totals
    total_earnings = sum(e.total_earning for e in earnings)
    total_bonuses = sum(e.on_time_bonus + e.quality_bonus for e in earnings)
    total_deductions = sum(e.late_delivery_deduction + e.cancellation_deduction for e in earnings)
    
    # Pending vs paid
    pending_earnings = sum(e.total_earning for e in earnings if e.payment_status == 'unpaid')
    paid_earnings = sum(e.total_earning for e in earnings if e.payment_status == 'paid')
    
    return render_template('driver/earnings_enhanced.html',
                         driver=driver,
                         earnings=earnings,
                         period=period,
                         total_earnings=total_earnings,
                         total_bonuses=total_bonuses,
                         total_deductions=total_deductions,
                         pending_earnings=pending_earnings,
                         paid_earnings=paid_earnings)


@driver_enhanced_bp.route('/earnings/today')
@login_required
@driver_required
def earnings_today():
    """Today's earnings"""
    return redirect(url_for('driver_enhanced.earnings_enhanced', period='today'))


@driver_enhanced_bp.route('/earnings/week')
@login_required
@driver_required
def earnings_week():
    """This week's earnings"""
    return redirect(url_for('driver_enhanced.earnings_enhanced', period='week'))


@driver_enhanced_bp.route('/earnings/month')
@login_required
@driver_required
def earnings_month():
    """This month's earnings"""
    return redirect(url_for('driver_enhanced.earnings_enhanced', period='month'))


# ============================================================================
# 5. DRIVER PERFORMANCE
# ============================================================================

@driver_enhanced_bp.route('/performance')
@login_required
@driver_required
def performance():
    """Driver performance metrics and ratings"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Get or create performance metrics
    performance = DriverPerformanceMetrics.query.filter_by(driver_id=driver.id).first()
    
    if not performance:
        performance = DriverPerformanceMetrics(driver_id=driver.id)
        db.session.add(performance)
        db.session.commit()
    
    # Update metrics
    performance.update_metrics()
    db.session.commit()
    
    # Get recent feedback
    recent_assignments = DriverAssignmentEnhanced.query.filter(
        DriverAssignmentEnhanced.driver_id == driver.id,
        DriverAssignmentEnhanced.retailer_rating_to_driver.isnot(None)
    ).order_by(DriverAssignmentEnhanced.actual_delivery_time.desc()).limit(10).all()
    
    return render_template('driver/performance.html',
                         driver=driver,
                         performance=performance,
                         recent_assignments=recent_assignments)


# ============================================================================
# 6. DRIVER NOTIFICATIONS
# ============================================================================

@driver_enhanced_bp.route('/notifications/enhanced')
@login_required
@driver_required
def notifications_enhanced():
    """Driver notifications"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    
    notifications = DriverAssignmentService.get_driver_notifications(current_user.id)
    
    return render_template('driver/notifications_enhanced.html',
                         driver=driver,
                         notifications=notifications)


@driver_enhanced_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
@driver_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    
    notification = DeliveryNotification.query.get_or_404(notification_id)
    
    if notification.recipient_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})


# ============================================================================
# 7. DRIVER STATUS MANAGEMENT
# ============================================================================

@driver_enhanced_bp.route('/status/toggle', methods=['POST'])
@login_required
@driver_required
def toggle_status():
    """Toggle driver availability status"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    if driver.status == 'available':
        driver.status = 'off_duty'
        flash('You are now OFF DUTY', 'info')
    elif driver.status == 'off_duty':
        driver.status = 'available'
        flash('You are now AVAILABLE for deliveries', 'success')
    elif driver.status == 'on_break':
        driver.status = 'available'
        flash('Break ended. You are now AVAILABLE', 'success')
    else:
        flash('Cannot change status while on delivery', 'warning')
        return redirect(url_for('driver_enhanced.dashboard_enhanced'))
    
    driver.last_active = datetime.utcnow()
    db.session.commit()
    
    return redirect(url_for('driver_enhanced.dashboard_enhanced'))


@driver_enhanced_bp.route('/status/break', methods=['POST'])
@login_required
@driver_required
def take_break():
    """Driver takes a break"""
    
    driver = DriverEnhanced.query.filter_by(user_id=current_user.id).first()
    
    if driver.status not in ['available', 'off_duty']:
        flash('Cannot take break while on delivery', 'warning')
        return redirect(url_for('driver_enhanced.dashboard_enhanced'))
    
    driver.status = 'on_break'
    driver.last_active = datetime.utcnow()
    db.session.commit()
    
    flash('You are now ON BREAK', 'info')
    return redirect(url_for('driver_enhanced.dashboard_enhanced'))
