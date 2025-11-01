import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///marketplace.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File upload
    UPLOAD_FOLDER = 'app/static/images/products'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # MOQ defaults
    DEFAULT_MOQ_RATE_PER_KG = 10.0
    
    # Payment config
    MOCK_PAYMENT_ENABLED = True
    PAYMENT_RETRY_LIMIT = 3
    
    # Driver config
    DRIVER_RATE_PER_KG = 10.0
    
    # Credit system
    CREDIT_SCORE_MAX = 1000
    CREDIT_TIERS = {
        'bronze': (0, 250),
        'silver': (251, 500),
        'gold': (501, 750),
        'platinum': (751, 1000)
    }
    
    TIER_BENEFITS = {
        'bronze': ['Basic marketplace access', 'Standard support'],
        'silver': ['Priority support', '5% bulk discount', 'Early access (5 min)'],
        'gold': ['Dedicated manager', '10% bulk discount', 'Free delivery', 'Early access (15 min)'],
        'platinum': ['24/7 support', '15% bulk discount', 'Free delivery', 'Net-60 terms', 'Early access (30 min)']
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
