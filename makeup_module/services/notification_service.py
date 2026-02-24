"""
Notification Service
Handles email notifications, in-app notifications, and alerts
"""
from flask import current_app, render_template_string
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from threading import Thread
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Mail instance (initialized in app.py)
mail = Mail()


def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")


def send_email_notification(subject, recipients, body, html_body=None):
    """
    Send email notification
    
    Args:
        subject: Email subject
        recipients: List of email addresses
        body: Plain text body
        html_body: HTML body (optional)
    
    Returns:
        bool: True if email queued successfully
    """
    try:
        if not current_app.config.get('NOTIFICATION_EMAIL_ENABLED', True):
            logger.info("Email notifications disabled")
            return False
        
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            body=body,
            html=html_body
        )
        
        # Send asynchronously
        Thread(
            target=send_async_email,
            args=(current_app._get_current_object(), msg)
        ).start()
        
        return True
        
    except Exception as e:
        logger.error(f"Error queueing email: {str(e)}")
        return False


def create_notification(user_id, title, message, notification_type, related_class_id=None):
    """
    Create an in-app notification
    
    Args:
        user_id: User ID to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        related_class_id: Related makeup class ID (optional)
    
    Returns:
        Notification object or None
    """
    from ..models import db, Notification
    
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_class_id=related_class_id
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        db.session.rollback()
        return None


def send_class_notification(makeup_class, notification_type):
    """
    Send notifications about a makeup class to relevant students
    
    Args:
        makeup_class: MakeUpClass object
        notification_type: Type of notification ('class_scheduled', 'class_cancelled', 
                          'schedule_changed', 'reminder', 'code_active')
    """
    from ..models import User, StudentEnrollment
    
    # Get enrolled students (for simplicity, notify all students)
    students = User.query.filter_by(role='student', is_active=True).all()
    
    # Notification templates
    templates = {
        'class_scheduled': {
            'title': f'New Make-Up Class: {makeup_class.course_name}',
            'message': f'A make-up class has been scheduled for {makeup_class.course_name} '
                      f'on {makeup_class.date.strftime("%B %d, %Y")} at {makeup_class.start_time.strftime("%I:%M %p")} '
                      f'in Room {makeup_class.room}.',
            'email_subject': f'Make-Up Class Scheduled: {makeup_class.course_name}',
        },
        'class_cancelled': {
            'title': f'Class Cancelled: {makeup_class.course_name}',
            'message': f'The make-up class for {makeup_class.course_name} scheduled on '
                      f'{makeup_class.date.strftime("%B %d, %Y")} has been cancelled.',
            'email_subject': f'Make-Up Class Cancelled: {makeup_class.course_name}',
        },
        'schedule_changed': {
            'title': f'Schedule Updated: {makeup_class.course_name}',
            'message': f'The schedule for {makeup_class.course_name} make-up class has been updated. '
                      f'New timing: {makeup_class.date.strftime("%B %d, %Y")} at {makeup_class.start_time.strftime("%I:%M %p")}. '
                      f'A new remedial code will be provided.',
            'email_subject': f'Schedule Changed: {makeup_class.course_name} Make-Up Class',
        },
        'reminder': {
            'title': f'Reminder: Make-Up Class Tomorrow',
            'message': f'Reminder: You have a make-up class for {makeup_class.course_name} '
                      f'tomorrow at {makeup_class.start_time.strftime("%I:%M %p")} in Room {makeup_class.room}.',
            'email_subject': f'Reminder: Make-Up Class Tomorrow - {makeup_class.course_name}',
        },
        'code_active': {
            'title': f'Remedial Code Active: {makeup_class.course_name}',
            'message': f'The remedial code for {makeup_class.course_name} is now active. '
                      f'Code: {makeup_class.remedial_code}. Valid until {makeup_class.code_expiry.strftime("%I:%M %p")}.',
            'email_subject': f'Remedial Code Active: {makeup_class.course_name}',
        }
    }
    
    template = templates.get(notification_type)
    if not template:
        logger.error(f"Unknown notification type: {notification_type}")
        return
    
    # Create in-app notifications for all students
    for student in students:
        create_notification(
            user_id=student.id,
            title=template['title'],
            message=template['message'],
            notification_type=notification_type,
            related_class_id=makeup_class.id
        )
        
        # Send email notification
        if current_app.config.get('NOTIFICATION_EMAIL_ENABLED', True):
            html_body = generate_email_html(
                template['title'],
                template['message'],
                makeup_class,
                notification_type
            )
            
            send_email_notification(
                subject=template['email_subject'],
                recipients=[student.email],
                body=template['message'],
                html_body=html_body
            )


def generate_email_html(title, message, makeup_class, notification_type):
    """Generate HTML email content"""
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .header {
                background: linear-gradient(135deg, #4F46E5 0%, #10B981 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 24px;
            }
            .content {
                padding: 30px;
            }
            .class-info {
                background: #F3F4F6;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            .class-info p {
                margin: 8px 0;
            }
            .class-info strong {
                color: #4F46E5;
            }
            .code-box {
                background: #4F46E5;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                text-align: center;
                font-size: 24px;
                letter-spacing: 3px;
                margin: 20px 0;
            }
            .footer {
                background: #F9FAFB;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #6B7280;
            }
            .btn {
                display: inline-block;
                background: #4F46E5;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                margin-top: 15px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{{ title }}</h1>
            </div>
            <div class="content">
                <p>{{ message }}</p>
                
                <div class="class-info">
                    <p><strong>Course:</strong> {{ course_name }}</p>
                    <p><strong>Section:</strong> {{ section }}</p>
                    <p><strong>Date:</strong> {{ date }}</p>
                    <p><strong>Time:</strong> {{ time }}</p>
                    <p><strong>Room:</strong> {{ room }}</p>
                    {% if faculty_name %}
                    <p><strong>Faculty:</strong> {{ faculty_name }}</p>
                    {% endif %}
                </div>
                
                {% if show_code %}
                <div class="code-box">
                    {{ remedial_code }}
                </div>
                <p style="text-align: center; color: #6B7280;">
                    Use this code to mark your attendance
                </p>
                {% endif %}
            </div>
            <div class="footer">
                <p>This is an automated notification from the Make-Up Class System.</p>
                <p>Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    from ..models import User
    faculty = User.query.get(makeup_class.faculty_id)
    
    return render_template_string(
        html_template,
        title=title,
        message=message,
        course_name=makeup_class.course_name,
        section=makeup_class.section,
        date=makeup_class.date.strftime("%B %d, %Y"),
        time=f"{makeup_class.start_time.strftime('%I:%M %p')} - {makeup_class.end_time.strftime('%I:%M %p')}",
        room=makeup_class.room,
        faculty_name=faculty.name if faculty else None,
        show_code=notification_type == 'code_active',
        remedial_code=makeup_class.remedial_code
    )


def send_class_reminders():
    """
    Send reminders for classes happening tomorrow
    Called by scheduler
    """
    from ..models import MakeUpClass
    from datetime import date, timedelta
    
    tomorrow = date.today() + timedelta(days=1)
    
    upcoming_classes = MakeUpClass.query.filter(
        MakeUpClass.date == tomorrow,
        MakeUpClass.status == 'upcoming'
    ).all()
    
    for makeup_class in upcoming_classes:
        send_class_notification(makeup_class, 'reminder')
        logger.info(f"Sent reminder for class {makeup_class.id}")


def activate_class_codes():
    """
    Activate remedial codes when class starts
    Called by scheduler
    """
    from ..models import MakeUpClass, db
    from datetime import datetime
    
    now = datetime.now()
    
    # Find classes starting now
    classes_starting = MakeUpClass.query.filter(
        MakeUpClass.date == now.date(),
        MakeUpClass.start_time <= now.time(),
        MakeUpClass.end_time > now.time(),
        MakeUpClass.status == 'upcoming'
    ).all()
    
    for makeup_class in classes_starting:
        makeup_class.status = 'ongoing'
        send_class_notification(makeup_class, 'code_active')
        logger.info(f"Activated code for class {makeup_class.id}")
    
    db.session.commit()


def get_user_unread_count(user_id):
    """Get count of unread notifications for a user"""
    from ..models import Notification
    
    return Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()


def cleanup_old_notifications(app):
    """
    Clean up old notifications (older than 30 days)
    Called by scheduler daily
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        from ..models import db, Notification
        
        try:
            # Delete notifications older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_notifications = Notification.query.filter(
                Notification.created_at < cutoff_date
            ).all()
            
            count = len(old_notifications)
            
            for notification in old_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            logger.info(f"Cleaned up {count} old notifications")
            
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {str(e)}")
            db.session.rollback()
