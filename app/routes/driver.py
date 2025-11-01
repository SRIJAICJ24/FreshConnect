from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.routes import driver_bp
from app.models import Driver, DriverAssignment, Order
from app.decorators import driver_required
from app import db
from datetime import datetime

@driver_bp.route('/dashboard')
@login_required
@driver_required
def dashboard():
    """Driver dashboard"""
    # Get driver profile
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Get assignments
    pending_assignments = DriverAssignment.query.filter_by(
        driver_id=driver.id,
        status='assigned'
    ).count()
    
    active_assignments = DriverAssignment.query.filter_by(
        driver_id=driver.id
    ).filter(
        DriverAssignment.status.in_(['picked_up', 'in_transit'])
    ).all()
    
    completed_today = DriverAssignment.query.filter_by(
        driver_id=driver.id,
        status='delivered'
    ).filter(
        db.func.date(DriverAssignment.delivery_time) == datetime.now().date()
    ).count()
    
    return render_template('driver/dashboard.html',
                         driver=driver,
                         pending_count=pending_assignments,
                         active_assignments=active_assignments,
                         completed_today=completed_today)

@driver_bp.route('/assignments')
@login_required
@driver_required
def assignments():
    """View all assignments"""
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    assignments = DriverAssignment.query.filter_by(driver_id=driver.id).order_by(
        DriverAssignment.assigned_at.desc()
    ).all()
    
    return render_template('driver/assignments.html', assignments=assignments, driver=driver)

@driver_bp.route('/assignment/<int:assignment_id>')
@login_required
@driver_required
def assignment_detail(assignment_id):
    """View assignment details"""
    assignment = DriverAssignment.query.get_or_404(assignment_id)
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    
    # Check ownership
    if assignment.driver_id != driver.id:
        flash('Access denied', 'danger')
        return redirect(url_for('driver.assignments'))
    
    return render_template('driver/assignment_detail.html', assignment=assignment, driver=driver)

@driver_bp.route('/assignment/<int:assignment_id>/pickup', methods=['POST'])
@login_required
@driver_required
def mark_pickup(assignment_id):
    """Mark order as picked up"""
    assignment = DriverAssignment.query.get_or_404(assignment_id)
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    
    if assignment.driver_id != driver.id:
        flash('Access denied', 'danger')
        return redirect(url_for('driver.assignments'))
    
    assignment.status = 'picked_up'
    assignment.pickup_time = datetime.utcnow()
    assignment.order.status = 'in_transit'
    
    # Update driver status
    driver.status = 'on_delivery'
    
    db.session.commit()
    flash('Order marked as picked up', 'success')
    return redirect(url_for('driver.assignment_detail', assignment_id=assignment_id))

@driver_bp.route('/assignment/<int:assignment_id>/deliver', methods=['POST'])
@login_required
@driver_required
def mark_delivered(assignment_id):
    """Mark order as delivered"""
    assignment = DriverAssignment.query.get_or_404(assignment_id)
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    
    if assignment.driver_id != driver.id:
        flash('Access denied', 'danger')
        return redirect(url_for('driver.assignments'))
    
    assignment.status = 'delivered'
    assignment.delivery_time = datetime.utcnow()
    assignment.order.status = 'delivered'
    assignment.order.delivered_at = datetime.utcnow()
    
    # Calculate earnings (₹10 per kg)
    total_weight = sum(item.weight or item.quantity for item in assignment.order.items)
    earnings = total_weight * 10  # ₹10 per kg/unit
    assignment.earnings = earnings
    
    # Update driver stats
    driver.status = 'available'
    driver.total_deliveries += 1
    driver.successful_deliveries += 1
    driver.total_earnings += earnings
    driver.current_load_kg = 0
    
    db.session.commit()
    flash(f'Order delivered successfully! You earned ₹{earnings:.2f}', 'success')
    return redirect(url_for('driver.assignments'))

@driver_bp.route('/earnings')
@login_required
@driver_required
def earnings():
    """View earnings"""
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all completed assignments
    completed_assignments = DriverAssignment.query.filter_by(
        driver_id=driver.id,
        status='delivered'
    ).order_by(DriverAssignment.delivery_time.desc()).all()
    
    return render_template('driver/earnings.html',
                         driver=driver,
                         assignments=completed_assignments)

@driver_bp.route('/status/toggle', methods=['POST'])
@login_required
@driver_required
def toggle_status():
    """Toggle driver availability"""
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    
    if not driver:
        flash('Driver profile not found', 'danger')
        return redirect(url_for('main.index'))
    
    if driver.status == 'available':
        driver.status = 'off_duty'
        flash('You are now OFF DUTY', 'info')
    elif driver.status == 'off_duty':
        driver.status = 'available'
        flash('You are now AVAILABLE for deliveries', 'success')
    else:
        flash('Cannot change status while on delivery', 'warning')
    
    db.session.commit()
    return redirect(url_for('driver.dashboard'))
