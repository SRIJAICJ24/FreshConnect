import os
from app import create_app, db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create app
app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Create tables
with app.app_context():
    db.create_all()
    print("+ Database tables created")

if __name__ == '__main__':
    print("="*70)
    print("  FreshConnect Marketplace")
    print("="*70)
    print(f"  Server: http://127.0.0.1:5000")
    print(f"  Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print("="*70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
