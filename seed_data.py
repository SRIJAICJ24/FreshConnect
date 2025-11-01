from app import create_app, db
from app.models import User, Product, RetailerCredit, Driver, DriverAssignment
from datetime import datetime, timedelta
import random

def seed_database():
    app = create_app()
    with app.app_context():
        print("="*70)
        print("  SEEDING DATABASE WITH TEST DATA")
        print("="*70)
        print()
        
        # Clear existing data
        print("[1/6] Clearing existing data...")
        db.drop_all()
        db.create_all()
        print("      Done")
        print()
        
        # Create Admin
        print("[2/6] Creating admin users...")
        admin = User(
            name='Admin User',
            email='admin@freshconnect.com',
            user_type='admin',
            is_active=True,
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("      + admin@freshconnect.com / admin123")
        print()
        
        # Create Vendors
        print("[3/6] Creating vendors...")
        vendors = []
        vendor_data = [
            ('Rajesh Kumar', 'Kumar Vegetables', 'Chennai'),
            ('Suresh Patel', 'Patel Fruits', 'Chennai'),
            ('Mahesh Reddy', 'Reddy Produce', 'Chennai'),
            ('Vikram Singh', 'Singh Organics', 'Chennai'),
            ('Anil Sharma', 'Sharma Dairy', 'Chennai')
        ]
        
        for i, (name, business, city) in enumerate(vendor_data, 1):
            vendor = User(
                name=name,
                email=f'vendor{i}@freshconnect.com',
                user_type='vendor',
                business_name=business,
                phone='9876543210',
                address=f'{i}00 Market Street',
                city=city,
                is_active=True,
                is_verified=True
            )
            vendor.set_password('vendor123')
            vendors.append(vendor)
            db.session.add(vendor)
            print(f"      + vendor{i}@freshconnect.com / vendor123")
        print()
        
        # Create Retailers
        print("[4/6] Creating retailers...")
        retailer_data = [
            ('Ramesh Iyer', 'Iyer Store', 'Chennai'),
            ('Priya Desai', 'Desai Market', 'Chennai'),
            ('Karthik Menon', 'Menon Provisions', 'Chennai'),
            ('Lakshmi Nair', 'Nair Mart', 'Chennai'),
            ('Arjun Pillai', 'Pillai Groceries', 'Chennai'),
            ('Sanjay Reddy', 'Reddy Retail', 'Chennai'),
            ('Divya Sharma', 'Sharma Store', 'Chennai')
        ]
        
        for i, (name, business, city) in enumerate(retailer_data, 1):
            retailer = User(
                name=name,
                email=f'retailer{i}@freshconnect.com',
                user_type='retailer',
                business_name=business,
                phone='9876543210',
                address=f'{i}00 Retail Street',
                city=city,
                is_active=True,
                is_verified=True
            )
            retailer.set_password('retailer123')
            db.session.add(retailer)
            db.session.flush()  # Flush to get retailer.id
            
            # Create credit profile
            credit_score = random.choice([300, 450, 550, 700, 850])
            credit = RetailerCredit(retailer_id=retailer.id, credit_score=credit_score)
            credit.credit_tier = credit.calculate_tier()
            db.session.add(credit)
            
            print(f"      + retailer{i}@freshconnect.com / retailer123 (Credit: {credit_score})")
        print()
        
        db.session.commit()
        
        # Create Products
        print("[5/6] Creating products...")
        product_data = [
            # Vegetables
            ('Tomatoes', 'Vegetables', 'Fresh red tomatoes', 40.0, 100, 'kg'),
            ('Onions', 'Vegetables', 'Premium onions', 30.0, 200, 'kg'),
            ('Potatoes', 'Vegetables', 'Farm fresh potatoes', 25.0, 300, 'kg'),
            ('Cabbage', 'Vegetables', 'Green cabbage', 20.0, 80, 'kg'),
            ('Carrots', 'Vegetables', 'Organic carrots', 35.0, 120, 'kg'),
            ('Cauliflower', 'Vegetables', 'Fresh cauliflower', 30.0, 90, 'kg'),
            ('Brinjal', 'Vegetables', 'Purple brinjal', 35.0, 70, 'kg'),
            ('Beans', 'Vegetables', 'Green beans', 45.0, 50, 'kg'),
            # Fruits
            ('Apples', 'Fruits', 'Kashmiri apples', 120.0, 150, 'kg'),
            ('Bananas', 'Fruits', 'Ripe bananas', 40.0, 200, 'dozen'),
            ('Oranges', 'Fruits', 'Juicy oranges', 60.0, 120, 'kg'),
            ('Grapes', 'Fruits', 'Seedless grapes', 80.0, 80, 'kg'),
            ('Mangoes', 'Fruits', 'Alphonso mangoes', 100.0, 100, 'kg'),
            ('Watermelon', 'Fruits', 'Sweet watermelon', 25.0, 150, 'kg'),
            ('Papaya', 'Fruits', 'Ripe papaya', 35.0, 90, 'kg'),
            ('Pomegranate', 'Fruits', 'Fresh pomegranate', 150.0, 50, 'kg'),
            # Grains
            ('Rice (Basmati)', 'Grains', 'Premium basmati', 65.0, 500, 'kg'),
            ('Rice (Sona Masoori)', 'Grains', 'Sona masoori rice', 45.0, 600, 'kg'),
            ('Wheat', 'Grains', 'Whole wheat', 35.0, 400, 'kg'),
            ('Dal (Toor)', 'Grains', 'Toor dal', 85.0, 200, 'kg'),
        ]
        
        product_count = 0
        for vendor in vendors:
            for name, category, desc, price, qty, unit in product_data[:10]:  # 10 products per vendor
                # Random expiry date (some near expiry for emergency marketplace)
                days_ahead = random.choice([2, 3, 5, 10, 15, 20, 25, 30])
                expiry = datetime.now().date() + timedelta(days=days_ahead)
                
                is_emergency = days_ahead <= 3
                discount = 0
                if days_ahead == 1:
                    discount = 50
                elif days_ahead == 2:
                    discount = 40
                elif days_ahead == 3:
                    discount = 30
                
                product = Product(
                    vendor_id=vendor.id,
                    product_name=name,
                    category=category,
                    description=desc,
                    price=price,
                    quantity=qty,
                    unit=unit,
                    expiry_date=expiry,
                    is_emergency=is_emergency,
                    discount_percentage=discount,
                    is_active=True,
                    moq_enabled=False
                )
                db.session.add(product)
                product_count += 1
        
        db.session.commit()
        print(f"      + {product_count} products created")
        print()
        
        # Create Drivers
        print("[6/7] Creating drivers...")
        drivers = []
        driver_data = [
            ('Ravi Kumar', '9876543210', 'van', 500, 'TN01AB1234', 'Koyambedu Market'),
            ('Vijay Sharma', '9876543211', 'truck', 1000, 'TN01CD5678', 'Koyambedu Market'),
            ('Murugan S', '9876543212', 'auto', 200, 'TN01EF9012', 'Koyambedu Market'),
            ('Kumar Raja', '9876543213', 'van', 550, 'TN02GH3456', 'Anna Nagar'),
            ('Selvam M', '9876543214', 'truck', 1200, 'TN02IJ7890', 'T Nagar'),
            ('Prakash R', '9876543215', 'motorcycle', 50, 'TN03KL1234', 'Vadapalani'),
            ('Ganesh K', '9876543216', 'van', 600, 'TN03MN5678', 'Porur'),
            ('Dinesh P', '9876543217', 'lorry', 2000, 'TN04OP9012', 'Ambattur')
        ]
        
        for i, (name, phone, vehicle_type, capacity, registration, location) in enumerate(driver_data, 1):
            # Create driver user account
            driver_user = User(
                name=name,
                email=f'driver{i}@freshconnect.com',
                user_type='driver',
                phone=phone,
                is_active=True,
                is_verified=True
            )
            driver_user.set_password('driver123')
            db.session.add(driver_user)
            db.session.flush()  # Get driver_user.id
            
            # Create driver profile
            driver_profile = Driver(
                user_id=driver_user.id,
                vehicle_type=vehicle_type,
                vehicle_registration=registration,
                vehicle_capacity_kg=capacity,
                parking_location=location,
                current_location=location,
                status='available',
                rating=random.uniform(4.0, 5.0),
                is_active=True
            )
            db.session.add(driver_profile)
            drivers.append(driver_profile)
            print(f"      + driver{i}@freshconnect.com / driver123 ({vehicle_type}, {capacity}kg)")
        
        db.session.commit()
        print()
        
        # Summary
        print("[7/7] Summary")
        print("="*70)
        print(f"  Admins: 1")
        print(f"  Vendors: {len(vendors)}")
        print(f"  Retailers: {len(retailer_data)}")
        print(f"  Drivers: {len(drivers)}")
        print(f"  Products: {product_count}")
        print("="*70)
        print()
        print("+ DATABASE SEEDED SUCCESSFULLY!")
        print()
        print("TEST CREDENTIALS:")
        print("-"*70)
        print("  Admin:    admin@freshconnect.com / admin123")
        print("  Vendor:   vendor1@freshconnect.com / vendor123")
        print("  Retailer: retailer1@freshconnect.com / retailer123")
        print("  Driver:   driver1@freshconnect.com / driver123")
        print("="*70)
        print()

if __name__ == '__main__':
    seed_database()
