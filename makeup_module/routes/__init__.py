"""
Routes package initialization
"""
from .auth import auth_bp
from .faculty import faculty_bp
from .student import student_bp

__all__ = ['auth_bp', 'faculty_bp', 'student_bp']
