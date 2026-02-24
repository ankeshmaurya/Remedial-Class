"""
Configuration settings for the Make-Up Class & Remedial Code Module
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Flask-Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@makeup-class.edu'
    
    # Remedial Code settings
    CODE_LENGTH = 8
    CODE_EXPIRY_BUFFER_MINUTES = 15  # Code expires 15 minutes after class ends
    
    # AI settings
    AI_PREDICTION_ENABLED = True
    RUSH_THRESHOLD_LOW = 30  # Below 30% = Low rush
    RUSH_THRESHOLD_MEDIUM = 60  # 30-60% = Medium rush
    RUSH_THRESHOLD_HIGH = 80  # Above 60% = High rush, Above 80% = Overcrowded
    
    # Notification settings
    NOTIFICATION_EMAIL_ENABLED = True
    NOTIFICATION_SMS_ENABLED = False


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Override with stronger secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
