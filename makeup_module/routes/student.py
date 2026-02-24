"""
Student Routes
Handles all student-related functionality including attendance marking
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from ..models import db, User, MakeUpClass, MakeUpAttendance, Notification, StudentEnrollment
from .auth import student_required

student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Student dashboard"""
    # Get upcoming make-up classes for enrolled courses
    # For simplicity, showing all upcoming classes - can be filtered by enrollment
    upcoming_classes = MakeUpClass.query.filter(
        MakeUpClass.status.in_(['upcoming', 'ongoing']),
        MakeUpClass.date >= date.today()
    ).order_by(MakeUpClass.date, MakeUpClass.start_time).limit(6).all()
    
    # Get attendance history
    attended_classes = MakeUpAttendance.query.filter_by(
        student_id=current_user.id
    ).count()
    
    # Calculate attendance percentage
    total_available = MakeUpClass.query.filter(
        MakeUpClass.status == 'completed'
    ).count()
    
    attendance_pct = round(attended_classes / total_available * 100, 1) if total_available > 0 else 0
    
    # Get recent notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Get unread notification count
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template('student/dashboard.html',
                         upcoming_classes=upcoming_classes,
                         attended_classes=attended_classes,
                         total_available=total_available,
                         attendance_pct=attendance_pct,
                         notifications=notifications,
                         unread_count=unread_count)


@student_bp.route('/classes')
@login_required
@student_required
def view_classes():
    """View all upcoming make-up classes"""
    # Filter parameters
    course_filter = request.args.get('course', '')
    date_filter = request.args.get('date', '')
    
    # Base query for upcoming/ongoing classes
    query = MakeUpClass.query.filter(
        MakeUpClass.status.in_(['upcoming', 'ongoing']),
        MakeUpClass.date >= date.today()
    )
    
    # Apply filters
    if course_filter:
        query = query.filter(MakeUpClass.course_name.ilike(f'%{course_filter}%'))
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(date=filter_date)
        except ValueError:
            pass
    
    classes = query.order_by(MakeUpClass.date, MakeUpClass.start_time).all()
    
    # Check which classes student has already marked attendance
    attended_ids = [a.class_id for a in MakeUpAttendance.query.filter_by(
        student_id=current_user.id
    ).all()]
    
    return render_template('student/view_classes.html',
                         classes=classes,
                         attended_ids=attended_ids,
                         course_filter=course_filter,
                         date_filter=date_filter)


@student_bp.route('/class/<int:class_id>')
@login_required
@student_required
def class_detail(class_id):
    """View details of a specific make-up class"""
    makeup_class = MakeUpClass.query.get_or_404(class_id)
    
    # Check if already attended
    attendance = MakeUpAttendance.query.filter_by(
        class_id=class_id,
        student_id=current_user.id
    ).first()
    
    # Get faculty info
    faculty = User.query.get(makeup_class.faculty_id)
    
    return render_template('student/class_detail.html',
                         makeup_class=makeup_class,
                         faculty=faculty,
                         attendance=attendance)


@student_bp.route('/mark-attendance', methods=['GET', 'POST'])
@login_required
@student_required
def mark_attendance():
    """Mark attendance using remedial code"""
    if request.method == 'POST':
        code = request.form.get('remedial_code', '').strip().upper()
        
        if not code:
            flash('Please enter the remedial code.', 'error')
            return render_template('student/mark_attendance.html')
        
        # Find class with this code
        makeup_class = MakeUpClass.query.filter_by(remedial_code=code).first()
        
        if not makeup_class:
            flash('Invalid remedial code. Please check and try again.', 'error')
            return render_template('student/mark_attendance.html')
        
        # Check if code is still valid
        if not makeup_class.is_code_valid():
            flash('This remedial code has expired.', 'error')
            return render_template('student/mark_attendance.html')
        
        # Check if class is ongoing or within time window
        now = datetime.now()
        class_start = datetime.combine(makeup_class.date, makeup_class.start_time)
        class_end = datetime.combine(makeup_class.date, makeup_class.end_time)
        
        if now < class_start:
            flash('Class has not started yet. Please try again when the class begins.', 'error')
            return render_template('student/mark_attendance.html')
        
        # Check if already marked
        existing = MakeUpAttendance.query.filter_by(
            class_id=makeup_class.id,
            student_id=current_user.id
        ).first()
        
        if existing:
            flash('You have already marked attendance for this class.', 'warning')
            return render_template('student/mark_attendance.html')
        
        # Determine attendance status based on 15 min grace period
        late_threshold = class_start + timedelta(minutes=15)
        
        if now <= late_threshold:
            # Within 15 minutes of class start = present
            status = 'present'
        else:
            # After 15 minutes - check late entry policy
            if makeup_class.allow_late_entry:
                status = 'late'
            else:
                status = 'absent'
        
        # Create attendance record
        attendance = MakeUpAttendance(
            class_id=makeup_class.id,
            student_id=current_user.id,
            attendance_status=status,
            ip_address=request.remote_addr,
            device_info=request.user_agent.string[:200] if request.user_agent.string else None
        )
        
        try:
            db.session.add(attendance)
            db.session.commit()
            
            if status == 'present':
                flash('Attendance marked successfully!', 'success')
            elif status == 'late':
                flash('Attendance marked as LATE.', 'warning')
            else:
                flash('Attendance marked as ABSENT (late entry not allowed).', 'error')
            
            return redirect(url_for('student.attendance_success', class_id=makeup_class.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('student/mark_attendance.html')


@student_bp.route('/api/mark-attendance', methods=['POST'])
@login_required
@student_required
def api_mark_attendance():
    """API endpoint for marking attendance (for AJAX requests)"""
    data = request.get_json()
    code = data.get('remedial_code', '').strip().upper()
    
    if not code:
        return jsonify({'success': False, 'message': 'Please enter the remedial code.'}), 400
    
    # Find class with this code
    makeup_class = MakeUpClass.query.filter_by(remedial_code=code).first()
    
    if not makeup_class:
        return jsonify({'success': False, 'message': 'Invalid remedial code.'}), 404
    
    # Check if code is still valid
    if not makeup_class.is_code_valid():
        return jsonify({'success': False, 'message': 'This remedial code has expired.'}), 400
    
    # Check if class is ongoing
    now = datetime.now()
    class_start = datetime.combine(makeup_class.date, makeup_class.start_time)
    class_end = datetime.combine(makeup_class.date, makeup_class.end_time)
    
    if now < class_start:
        return jsonify({'success': False, 'message': 'Class has not started yet.'}), 400
    
    # Check if already marked
    existing = MakeUpAttendance.query.filter_by(
        class_id=makeup_class.id,
        student_id=current_user.id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'Already marked attendance.'}), 400
    
    # Determine attendance status based on 15 min grace period
    late_threshold = class_start + timedelta(minutes=15)
    
    if now <= late_threshold:
        # Within 15 minutes of class start = present
        status = 'present'
    else:
        # After 15 minutes - check late entry policy
        if makeup_class.allow_late_entry:
            status = 'late'
        else:
            status = 'absent'
    
    # Create attendance record
    attendance = MakeUpAttendance(
        class_id=makeup_class.id,
        student_id=current_user.id,
        attendance_status=status,
        ip_address=request.remote_addr
    )
    
    try:
        db.session.add(attendance)
        db.session.commit()
        
        # Set appropriate message based on status
        if status == 'present':
            message = 'Attendance marked successfully!'
        elif status == 'late':
            message = 'Attendance marked as LATE.'
        else:
            message = 'Attendance marked as ABSENT (late entry not allowed).'
        
        return jsonify({
            'success': True,
            'message': message,
            'status': status,
            'class_info': {
                'course': makeup_class.course_name,
                'date': makeup_class.date.isoformat(),
                'time': f'{makeup_class.start_time} - {makeup_class.end_time}'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred.'}), 500


@student_bp.route('/qr-attendance/<code>')
@login_required
@student_required
def qr_attendance(code):
    """
    Handle QR code scan attendance - auto marks attendance when student scans QR
    This route requires student to be logged in (authenticated from their profile)
    """
    code = code.strip().upper()
    
    # Find class with this code
    makeup_class = MakeUpClass.query.filter_by(remedial_code=code).first()
    
    if not makeup_class:
        flash('Invalid QR code. The remedial code does not exist.', 'error')
        return redirect(url_for('student.mark_attendance'))
    
    # Check if code is still valid
    if not makeup_class.is_code_valid():
        flash('This QR code has expired. The class attendance window has closed.', 'error')
        return redirect(url_for('student.mark_attendance'))
    
    # Check if class is ongoing or within time window
    now = datetime.now()
    class_start = datetime.combine(makeup_class.date, makeup_class.start_time)
    class_end = datetime.combine(makeup_class.date, makeup_class.end_time)
    
    if now < class_start:
        flash('Class has not started yet. Please scan the QR code when the class begins.', 'error')
        return redirect(url_for('student.mark_attendance'))
    
    # Check if already marked
    existing = MakeUpAttendance.query.filter_by(
        class_id=makeup_class.id,
        student_id=current_user.id
    ).first()
    
    if existing:
        flash('You have already marked attendance for this class.', 'warning')
        return redirect(url_for('student.attendance_success', class_id=makeup_class.id))
    
    # Determine attendance status based on 15 min grace period
    late_threshold = class_start + timedelta(minutes=15)
    
    if now <= late_threshold:
        # Within 15 minutes of class start = present
        status = 'present'
    else:
        # After 15 minutes - check late entry policy
        if makeup_class.allow_late_entry:
            status = 'late'
        else:
            status = 'absent'
    
    # Create attendance record with QR scan info
    attendance = MakeUpAttendance(
        class_id=makeup_class.id,
        student_id=current_user.id,
        attendance_status=status,
        ip_address=request.remote_addr,
        device_info=f"QR_SCAN: {request.user_agent.string[:150]}" if request.user_agent.string else "QR_SCAN"
    )
    
    try:
        db.session.add(attendance)
        db.session.commit()
        
        if status == 'present':
            flash('Attendance marked successfully via QR scan!', 'success')
        elif status == 'late':
            flash('Attendance marked as LATE via QR scan.', 'warning')
        else:
            flash('Attendance marked as ABSENT via QR scan (late entry not allowed).', 'error')
        
        return redirect(url_for('student.attendance_success', class_id=makeup_class.id))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while marking attendance. Please try again.', 'error')
        return redirect(url_for('student.mark_attendance'))


@student_bp.route('/attendance-success/<int:class_id>')
@login_required
@student_required
def attendance_success(class_id):
    """Attendance success page"""
    makeup_class = MakeUpClass.query.get_or_404(class_id)
    attendance = MakeUpAttendance.query.filter_by(
        class_id=class_id,
        student_id=current_user.id
    ).first_or_404()
    
    return render_template('student/attendance_success.html',
                         makeup_class=makeup_class,
                         attendance=attendance)


@student_bp.route('/history')
@login_required
@student_required
def attendance_history():
    """View attendance history"""
    # Get all attendance records for this student
    attendances = MakeUpAttendance.query.filter_by(
        student_id=current_user.id
    ).join(MakeUpClass).order_by(MakeUpClass.date.desc()).all()
    
    # Calculate statistics
    total = len(attendances)
    present = sum(1 for a in attendances if a.attendance_status == 'present')
    late = sum(1 for a in attendances if a.attendance_status == 'late')
    
    attendance_pct = round((present + late) / total * 100, 1) if total > 0 else 0
    
    return render_template('student/attendance_history.html',
                         attendances=attendances,
                         total=total,
                         present=present,
                         late=late,
                         attendance_pct=attendance_pct)


@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    """View all notifications"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('student/notifications.html', notifications=notifications)


@student_bp.route('/notification/<int:notif_id>/read', methods=['POST'])
@login_required
@student_required
def mark_notification_read(notif_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(
        id=notif_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({'success': True})


@student_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@student_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True, 'read_at': datetime.utcnow()})
    
    db.session.commit()
    
    return jsonify({'success': True})


@student_bp.route('/api/upcoming-classes')
@login_required
@student_required
def api_upcoming_classes():
    """API endpoint to get upcoming classes"""
    classes = MakeUpClass.query.filter(
        MakeUpClass.status.in_(['upcoming', 'ongoing']),
        MakeUpClass.date >= date.today()
    ).order_by(MakeUpClass.date, MakeUpClass.start_time).limit(10).all()
    
    result = []
    for cls in classes:
        faculty = User.query.get(cls.faculty_id)
        
        # Check if already attended
        attended = MakeUpAttendance.query.filter_by(
            class_id=cls.id,
            student_id=current_user.id
        ).first() is not None
        
        result.append({
            'id': cls.id,
            'course_name': cls.course_name,
            'course_code': cls.course_code,
            'section': cls.section,
            'date': cls.date.isoformat(),
            'start_time': cls.start_time.strftime('%H:%M'),
            'end_time': cls.end_time.strftime('%H:%M'),
            'room': cls.room,
            'faculty_name': faculty.name if faculty else 'Unknown',
            'status': cls.status,
            'attended': attended
        })
    
    return jsonify(result)


@student_bp.route('/api/attendance-stats')
@login_required
@student_required
def api_attendance_stats():
    """API endpoint to get attendance statistics"""
    attendances = MakeUpAttendance.query.filter_by(
        student_id=current_user.id
    ).all()
    
    total = len(attendances)
    present = sum(1 for a in attendances if a.attendance_status == 'present')
    late = sum(1 for a in attendances if a.attendance_status == 'late')
    
    return jsonify({
        'total': total,
        'present': present,
        'late': late,
        'attendance_pct': round((present + late) / total * 100, 1) if total > 0 else 0
    })
