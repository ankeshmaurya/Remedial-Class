"""
Make-Up Class & Remedial Code Module
Main Application Entry Point
Modern 2026 Edition
"""

import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Import configuration
from makeup_module.config import config

# Import db from models (single instance)
from makeup_module.models import db

# Initialize extensions
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
scheduler = BackgroundScheduler()


def create_app(config_name='development'):
    """Application factory for creating Flask app instance."""
    
    app = Flask(__name__,
                template_folder='makeup_module/templates',
                static_folder='makeup_module/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from makeup_module.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from makeup_module.routes.auth import auth_bp
    from makeup_module.routes.faculty import faculty_bp
    from makeup_module.routes.student import student_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(student_bp)
    
    # Root redirect
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'faculty':
                return redirect(url_for('faculty.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.index'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_error_page(404, 'Page Not Found', 
                                 'The page you are looking for does not exist.'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_error_page(500, 'Internal Server Error',
                                 'Something went wrong on our end.'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_error_page(403, 'Access Forbidden',
                                 'You do not have permission to access this resource.'), 403
    
    def render_error_page(code, title, message):
        from flask import render_template_string
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Make-Up Class Module</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .error-container {
            text-align: center;
            padding: 40px;
        }
        .error-code {
            font-family: 'Poppins', sans-serif;
            font-size: 8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #4F46E5 0%, #10B981 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
            margin-bottom: 16px;
        }
        .error-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #111827;
            margin-bottom: 8px;
        }
        .error-message {
            color: #6B7280;
            margin-bottom: 24px;
        }
        .back-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            background: #4F46E5;
            color: white;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: background 0.2s;
        }
        .back-btn:hover {
            background: #4338CA;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-code">{{ code }}</div>
        <h1 class="error-title">{{ title }}</h1>
        <p class="error-message">{{ message }}</p>
        <a href="/" class="back-btn">
            <i class="fas fa-arrow-left"></i> Back to Home
        </a>
    </div>
</body>
</html>
        ''', code=code, title=title, message=message)
    
    # Context processors
    @app.context_processor
    def inject_globals():
        from makeup_module.models import Notification
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()
        return dict(
            current_year=datetime.now().year,
            unread_notifications=unread_count
        )
    
    # Template filters
    @app.template_filter('datetime')
    def format_datetime(value, format='%B %d, %Y %I:%M %p'):
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('date')
    def format_date(value, format='%B %d, %Y'):
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('time')
    def format_time(value, format='%I:%M %p'):
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('relative_time')
    def relative_time(value):
        if value is None:
            return ''
        now = datetime.utcnow()
        diff = now - value
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return 'Just now'
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f'{days} day{"s" if days > 1 else ""} ago'
        else:
            return value.strftime('%B %d, %Y')
    
    # Initialize database and scheduler
    with app.app_context():
        # Import models to ensure they're registered
        from makeup_module import models
        
        # Create tables
        db.create_all()
        
        # Create upload directories if they don't exist
        upload_folder = os.path.join(app.static_folder, 'uploads')
        qr_folder = os.path.join(upload_folder, 'qr_codes')
        os.makedirs(qr_folder, exist_ok=True)
        
        # Start scheduler for background tasks
        if not scheduler.running:
            # Import notification service for scheduled tasks
            from makeup_module.services.notification_service import (
                send_class_reminders,
                cleanup_old_notifications
            )
            
            # Schedule class reminders (every 30 minutes)
            scheduler.add_job(
                func=lambda: send_class_reminders(app),
                trigger='interval',
                minutes=30,
                id='send_class_reminders',
                replace_existing=True
            )
            
            # Schedule notification cleanup (daily at 2 AM)
            scheduler.add_job(
                func=lambda: cleanup_old_notifications(app),
                trigger='cron',
                hour=2,
                id='cleanup_notifications',
                replace_existing=True
            )
            
            scheduler.start()
    
    return app


# Helper functions for scheduler tasks
def send_class_reminders(app):
    """Send reminders for upcoming classes."""
    with app.app_context():
        from makeup_module.models import MakeUpClass, User
        from makeup_module.services.notification_service import send_class_notification
        
        # Get classes starting in the next hour
        now = datetime.utcnow()
        upcoming_classes = MakeUpClass.query.filter(
            MakeUpClass.status == 'scheduled',
            MakeUpClass.class_date == now.date(),
            MakeUpClass.start_time >= now.time()
        ).all()
        
        for makeup_class in upcoming_classes:
            send_class_notification(makeup_class, 'reminder')


def cleanup_old_notifications(app):
    """Remove old read notifications."""
    with app.app_context():
        from makeup_module.models import Notification
        from datetime import timedelta
        
        # Delete read notifications older than 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        Notification.query.filter(
            Notification.is_read == True,
            Notification.created_at < cutoff
        ).delete()
        db.session.commit()


# Create the application instance
app = create_app(os.environ.get('FLASK_ENV', 'development'))


if __name__ == '__main__':
    # Run in development mode
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
