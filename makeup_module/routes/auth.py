"""
Authentication Routes
Handles login, logout, registration, and password reset
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from ..models import db, User
from functools import wraps
import secrets
import string

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def faculty_required(f):
    """Decorator to require faculty role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_faculty():
            flash('Access denied. Faculty only.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator to require student role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student():
            flash('Access denied. Students only.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        if current_user.is_faculty():
            return redirect(url_for('faculty.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    return render_template('auth/landing.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        if current_user.is_faculty():
            return redirect(url_for('faculty.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact admin.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            session.permanent = True
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_faculty():
                return redirect(url_for('faculty.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        department = request.form.get('department', '').strip()
        
        # Validation
        errors = []
        
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters.')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if role not in ['faculty', 'student']:
            errors.append('Invalid role selected.')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            name=name,
            email=email,
            role=role,
            department=department
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token (in production, send via email)
            reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            # Store token in session (in production, store in database with expiry)
            session['reset_token'] = reset_token
            session['reset_email'] = email
            
            # TODO: Send email with reset link
            flash('If an account exists with this email, you will receive a password reset link.', 'info')
        else:
            # Same message for security (don't reveal if email exists)
            flash('If an account exists with this email, you will receive a password reset link.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    # Verify token
    stored_token = session.get('reset_token')
    reset_email = session.get('reset_email')
    
    if not stored_token or stored_token != token:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        user = User.query.filter_by(email=reset_email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            
            # Clear session
            session.pop('reset_token', None)
            session.pop('reset_email', None)
            
            flash('Your password has been reset successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and edit user profile"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Update name and department
        if name:
            current_user.name = name
        current_user.department = department
        
        # Update password if provided
        if new_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('auth/profile.html')
            
            if len(new_password) < 8:
                flash('New password must be at least 8 characters.', 'error')
                return render_template('auth/profile.html')
            
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('auth/profile.html')
            
            current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Profile updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('auth/profile.html')
