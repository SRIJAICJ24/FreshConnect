import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import current_app
import uuid

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_product_image(file, vendor_id):
    """Save product image and return filename"""
    if not file or not allowed_file(file.filename):
        return None
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_code = str(uuid.uuid4())[:8]
    new_filename = f"{vendor_id}_{timestamp}_{unique_code}_{filename}"
    
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, new_filename)
    file.save(filepath)
    
    return new_filename

def delete_product_image(filename):
    """Delete product image file"""
    if not filename:
        return
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)

def generate_order_id():
    """Generate unique order ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique = str(uuid.uuid4())[:6].upper()
    return f"ORD{timestamp}{unique}"

def generate_transaction_id():
    """Generate unique transaction ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique = str(uuid.uuid4())[:8].upper()
    return f"MOCKTXN{timestamp}{unique}"

def calculate_days_to_expiry(expiry_date):
    """Calculate days until expiry"""
    if not expiry_date:
        return None
    days = (expiry_date - datetime.now().date()).days
    return max(0, days)

def format_currency(amount):
    """Format amount as Indian currency"""
    return f"₹{amount:,.2f}"

def get_discount_percentage(days_to_expiry):
    """Calculate discount based on days to expiry"""
    if days_to_expiry <= 0:
        return 0
    elif days_to_expiry == 1:
        return 50
    elif days_to_expiry == 2:
        return 40
    elif days_to_expiry == 3:
        return 30
    return 0

def validate_card_number(card_number):
    """Mock card validation - even last digit = success"""
    if not card_number or len(card_number) != 16:
        return False
    try:
        last_digit = int(card_number[-1])
        return last_digit % 2 == 0  # Even = success
    except:
        return False
