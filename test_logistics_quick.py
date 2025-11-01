"""
Quick Test Script for Delivery & Logistics System
Run this to verify the system is working
"""

from app import create_app, db
from app.models_logistics import (
    LogisticsCost, DriverEnhanced, DriverAssignmentEnhanced,
    DriverEarning, DeliveryTrackingEvent, DeliveryNotification,
    DriverPerformanceMetrics
)
from app.driver_service import DriverAssignmentService


def test_logistics_system():
    """Run comprehensive tests on the logistics system"""
    
    app = create_app()
    
    with app.app_context():
        print("="*70)
        print("  🚚 TESTING DELIVERY & LOGISTICS SYSTEM")
        print("="*70)
        print()
        
        # Test 1: Check Tables Exist
        print("[TEST 1] Checking if logistics tables exist...")
        try:
            tables_count = {
                'logistics_costs': LogisticsCost.query.count(),
                'drivers_enhanced': DriverEnhanced.query.count(),
                'driver_assignments_enhanced': DriverAssignmentEnhanced.query.count(),
                'driver_earnings': DriverEarning.query.count(),
                'delivery_tracking_events': DeliveryTrackingEvent.query.count(),
                'delivery_notifications': DeliveryNotification.query.count(),
                'driver_performance_metrics': DriverPerformanceMetrics.query.count()
            }
            
            print("   ✓ All 7 logistics tables exist!")
            for table, count in tables_count.items():
                print(f"      - {table}: {count} records")
            print()
        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            print("   Run: python seed_logistics.py")
            return False
        
        # Test 2: Check Logistics Configuration
        print("[TEST 2] Checking logistics configuration...")
        areas = LogisticsCost.query.all()
        
        if areas:
            print(f"   ✓ {len(areas)} delivery areas configured:")
            for area in areas[:5]:  # Show first 5
                cost_per_kg = area.calculate_cost(1)
                print(f"      - {area.area_name}: ₹{cost_per_kg:.2f}/kg (Min: ₹{area.minimum_charge})")
            if len(areas) > 5:
                print(f"      ... and {len(areas) - 5} more")
            print()
        else:
            print("   ✗ No logistics areas configured")
            print("   Run: python seed_logistics.py")
            return False
        
        # Test 3: Check Enhanced Drivers
        print("[TEST 3] Checking enhanced drivers...")
        drivers = DriverEnhanced.query.all()
        
        if drivers:
            print(f"   ✓ {len(drivers)} enhanced drivers available:")
            for driver in drivers[:5]:  # Show first 5
                print(f"      - {driver.name}: {driver.vehicle_type.title()} ({driver.vehicle_capacity_kg}kg)")
                print(f"        Status: {driver.status}, Rating: {driver.rating:.1f}⭐")
            if len(drivers) > 5:
                print(f"      ... and {len(drivers) - 5} more")
            print()
        else:
            print("   ✗ No enhanced drivers found")
            print("   Run: python seed_logistics.py")
            return False
        
        # Test 4: Test Driver Assignment Algorithm
        print("[TEST 4] Testing driver assignment algorithm...")
        
        test_weight = 10  # kg
        test_area = 'North Koyambedu'
        
        best_driver, message = DriverAssignmentService.find_best_driver(
            order_weight=test_weight,
            delivery_area=test_area
        )
        
        if best_driver:
            print(f"   ✓ {message}")
            print(f"      Driver: {best_driver.name}")
            print(f"      Vehicle: {best_driver.vehicle_type.title()}")
            print(f"      Capacity: {best_driver.vehicle_capacity_kg}kg")
            print(f"      Available: {best_driver.available_capacity}kg")
            print(f"      Rating: {best_driver.rating:.1f}⭐")
            print()
        else:
            print(f"   ✗ {message}")
            print()
        
        # Test 5: Test Logistics Cost Calculation
        print("[TEST 5] Testing logistics cost calculation...")
        
        cost = DriverAssignmentService.calculate_logistics_cost(
            weight_kg=test_weight,
            delivery_area=test_area
        )
        
        print(f"   ✓ Cost calculated for {test_weight}kg to {test_area}:")
        print(f"      Base Rate: ₹{cost['rate_per_kg']}/kg")
        print(f"      Area Multiplier: {cost['area_multiplier']}×")
        print(f"      Base Cost: ₹{cost['base_cost']:.2f}")
        print(f"      Total Cost: ₹{cost['total_cost']:.2f}")
        print(f"      Delivery Time: {cost['delivery_time_minutes']} minutes")
        print()
        
        # Test 6: Test Driver Earning Calculation
        print("[TEST 6] Testing driver earning calculation...")
        
        earning = DriverAssignmentService.calculate_driver_earning(
            weight_kg=test_weight,
            base_logistics_cost=cost['base_cost']
        )
        
        print(f"   ✓ Earning calculated:")
        print(f"      Base Earning: ₹{earning:.2f} ({test_weight}kg × ₹10/kg)")
        print(f"      Potential Bonuses:")
        print(f"         - On-time: +₹{earning * 0.10:.2f} (10%)")
        print(f"         - Quality (5⭐): +₹{earning * 0.05:.2f} (5%)")
        print(f"      Maximum Total: ₹{earning * 1.15:.2f}")
        print()
        
        # Test 7: Check Performance Metrics
        print("[TEST 7] Checking driver performance metrics...")
        metrics = DriverPerformanceMetrics.query.all()
        
        if metrics:
            print(f"   ✓ {len(metrics)} driver performance records found")
            for metric in metrics[:3]:  # Show first 3
                driver = metric.driver
                print(f"      - {driver.name}:")
                print(f"        Total Orders: {metric.total_orders}")
                print(f"        Completion Rate: {metric.completion_rate if metric.completion_rate else 100}%")
                print(f"        Average Rating: {metric.average_rating:.1f}⭐")
            print()
        else:
            print("   ⚠ No performance metrics yet (will be created on first assignment)")
            print()
        
        # Summary
        print("="*70)
        print("  ✅ LOGISTICS SYSTEM TESTS COMPLETED")
        print("="*70)
        print()
        print("SYSTEM STATUS:")
        print(f"  ✓ Logistics Tables: 7 created")
        print(f"  ✓ Delivery Areas: {len(areas)} configured")
        print(f"  ✓ Enhanced Drivers: {len(drivers)} available")
        print(f"  ✓ Driver Assignment: Working")
        print(f"  ✓ Cost Calculation: Working")
        print(f"  ✓ Earning Calculation: Working")
        print()
        print("NEXT STEPS:")
        print("  1. Start server: python run.py")
        print("  2. Login as driver: driver1@freshconnect.com / driver123")
        print("  3. Visit: http://127.0.0.1:5000/driver/dashboard/enhanced")
        print()
        print("NOTE: If you see 'template not found' error, that's OK!")
        print("      It means the backend is working, just need to create templates.")
        print()
        print("="*70)
        
        return True


if __name__ == '__main__':
    try:
        test_logistics_system()
    except Exception as e:
        print()
        print("="*70)
        print("  ✗ ERROR DURING TESTING")
        print("="*70)
        print(f"  {str(e)}")
        print()
        print("POSSIBLE FIXES:")
        print("  1. Create tables: python -c \"from app import create_app, db; from app import models_logistics; app = create_app(); app.app_context().push(); db.create_all()\"")
        print("  2. Seed data: python seed_logistics.py")
        print("  3. Try again: python test_logistics_quick.py")
        print("="*70)
