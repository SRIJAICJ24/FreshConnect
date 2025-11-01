from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
vendor_bp = Blueprint('vendor', __name__)
retailer_bp = Blueprint('retailer', __name__)
admin_bp = Blueprint('admin', __name__)
driver_bp = Blueprint('driver', __name__)

# Import routes
from app.routes import main, auth, vendor, retailer, admin, driver

# Import driver_enhanced separately (it has its own blueprint)
from app.routes.driver_enhanced import driver_enhanced_bp
