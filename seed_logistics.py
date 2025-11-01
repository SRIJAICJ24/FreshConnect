"""
Seed Data for Delivery & Logistics System
Run this after creating logistics tables
"""

from app import create_app, db
from app.models import User, Driver
from app.models_logistics import (
    LogisticsCost, DriverEnhanced, DriverPerformanceMetrics
)
from datetime import datetime
import random


def seed_logistics():
    """Seed logistics configuration and enhanced drivers"""
    
    app = create_app()
    with app.app_context():
        print("="*70)
        print("  SEEDING LOGISTICS & DELIVERY SYSTEM")
        print("="*70)
        print()
        
        # 1. Create Logistics Cost Configuration
        print("[1/3] Creating logistics cost configuration...")
        
        areas_data = [
            ('North Koyambedu', 10.0, 1.1, 50.0, 45),
            ('South Koyambedu', 10.0, 1.15, 50.0, 50),
            ('Central Koyambedu', 10.0, 1.0, 50.0, 30),
            ('East Koyambedu', 10.0, 1.2, 50.0, 60),
            ('West Koyambedu', 10.0, 1.05, 50.0, 40),
            ('Anna Nagar', 10.0, 1.25, 50.0, 55),
            ('T Nagar', 10.0, 1.3, 50.0, 60),
            ('Porur', 10.0, 1.15, 50.0, 50),
            ('Vadapalani', 10.0, 1.2, 50.0, 55),
            ('Ambattur', 10.0, 1.35, 50.0, 70),
        ]
        
        for area_name, rate, multiplier, min_charge, time in areas_data:
            existing = LogisticsCost.query.filter_by(area_name=area_name).first()
            if not existing:
                logistics = LogisticsCost(
                    area_name=area_name,
                    base_rate_per_kg=rate,
                    area_multiplier=multiplier,
                    minimum_charge=min_charge,
                    delivery_time_minutes=time,
                    is_active=True
                )
                db.session.add(logistics)
                print(f"      + {area_name}: ₹{rate}/kg × {multiplier}, Min: ₹{min_charge}, Time: {time}min")
        
        db.session.commit()
        print()
        
        # 2. Upgrade Existing Drivers to Enhanced Drivers
        print("[2/3] Creating enhanced driver profiles...")
        
        existing_drivers = Driver.query.all()
        
        for driver in existing_drivers:
            # Check if already enhanced
            existing_enhanced = DriverEnhanced.query.filter_by(user_id=driver.user_id).first()
            if existing_enhanced:
                continue
            
            enhanced = DriverEnhanced(
                user_id=driver.user_id,
                name=driver.user.name,
                phone=driver.user.phone or '9876543210',
                email=driver.user.email,
                vehicle_type=driver.vehicle_type,
                vehicle_registration=driver.vehicle_registration,
                vehicle_capacity_kg=int(driver.vehicle_capacity_kg),
                vehicle_insured=True,
                parking_location=driver.parking_location,
                current_location=driver.current_location,
                current_load_kg=0,
                status='available',
                license_number=f'DL{random.randint(1000, 9999)}',
                is_verified=True,
                verification_date=datetime.utcnow(),
                documents_verified=True,
                rating=driver.rating,
                total_deliveries=0,
                successful_deliveries=0,
                cancelled_deliveries=0,
                total_earnings=0,
                is_active=True,
                joined_date=datetime.utcnow()
            )
            
            db.session.add(enhanced)
            db.session.flush()  # Get enhanced.id
            
            # Create performance metrics
            metrics = DriverPerformanceMetrics(
                driver_id=enhanced.id,
                total_orders=0,
                completed_orders=0,
                cancelled_orders=0,
                late_deliveries=0,
                on_time_percentage=100.0,
                average_rating=enhanced.rating,
                five_star_count=0,
                four_star_count=0,
                three_star_count=0,
                two_star_count=0,
                one_star_count=0,
                acceptance_rate=100.0,
                completion_rate=100.0,
                issue_rate=0.0,
                current_month_orders=0,
                current_month_earnings=0,
                current_month_on_time_percentage=100.0
            )
            db.session.add(metrics)
            
            print(f"      + Enhanced driver: {enhanced.name} ({enhanced.vehicle_type}, {enhanced.vehicle_capacity_kg}kg)")
        
        db.session.commit()
        print()
        
        # 3. Summary
        print("[3/3] Summary")
        print("="*70)
        print(f"  Logistics Areas: {LogisticsCost.query.count()}")
        print(f"  Enhanced Drivers: {DriverEnhanced.query.count()}")
        print(f"  Performance Metrics: {DriverPerformanceMetrics.query.count()}")
        print("="*70)
        print()
        print("+ LOGISTICS SYSTEM SEEDED SUCCESSFULLY!")
        print()
        print("AVAILABLE DELIVERY AREAS:")
        print("-"*70)
        for area in LogisticsCost.query.all():
            print(f"  {area.area_name}: ₹{area.base_rate_per_kg}/kg × {area.area_multiplier} = ₹{area.calculate_cost(1):.2f}/kg")
        print("="*70)
        print()
        print("ENHANCED DRIVERS:")
        print("-"*70)
        for driver in DriverEnhanced.query.all():
            print(f"  {driver.name}: {driver.vehicle_type.title()} ({driver.vehicle_capacity_kg}kg) - Status: {driver.status}")
        print("="*70)
        print()


if __name__ == '__main__':
    seed_logistics()
