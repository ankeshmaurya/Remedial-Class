"""
Services package initialization
"""
from .code_generator import generate_remedial_code, generate_qr_code
from .ai_prediction import predict_attendance, get_smart_schedule_recommendations
from .notification_service import send_class_notification, send_email_notification

__all__ = [
    'generate_remedial_code',
    'generate_qr_code',
    'predict_attendance',
    'get_smart_schedule_recommendations',
    'send_class_notification',
    'send_email_notification'
]
