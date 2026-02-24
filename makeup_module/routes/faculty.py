"""
Faculty Routes
Handles all faculty-related functionality including scheduling and attendance management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from ..models import db, User, MakeUpClass, MakeUpAttendance, Notification, Course, StudentEnrollment
from ..services.code_generator import generate_remedial_code, generate_qr_code
from ..services.ai_prediction import predict_attendance, get_smart_schedule_recommendations
from ..services.notification_service import send_class_notification
from .auth import faculty_required
import csv
import io

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')


@faculty_bp.route('/dashboard')
@login_required
@faculty_required
def dashboard():
    """Faculty dashboard with stats and overview"""
    # Get statistics
    total_classes = MakeUpClass.query.filter_by(faculty_id=current_user.id).count()
    upcoming_classes = MakeUpClass.query.filter_by(
        faculty_id=current_user.id, 
        status='upcoming'
    ).filter(MakeUpClass.date >= date.today()).count()
    
    # Calculate average attendance
    completed_classes = MakeUpClass.query.filter_by(
        faculty_id=current_user.id,
        status='completed'
    ).all()
    
    avg_attendance = 0
    if completed_classes:
        total_pct = sum([c.get_attendance_stats()['attendance_pct'] for c in completed_classes])
        avg_attendance = round(total_pct / len(completed_classes), 1)
    
    # Get upcoming classes for display
    upcoming = MakeUpClass.query.filter_by(
        faculty_id=current_user.id,
        status='upcoming'
    ).filter(MakeUpClass.date >= date.today()).order_by(MakeUpClass.date, MakeUpClass.start_time).limit(5).all()
    
    # Get recent notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Get predicted rush for upcoming classes
    rush_predictions = []
    for cls in upcoming:
        if cls.rush_level:
            rush_predictions.append({
                'class': cls,
                'rush_level': cls.rush_level,
                'predicted_pct': cls.predicted_attendance_pct
            })
    
    return render_template('faculty/dashboard.html',
                         total_classes=total_classes,
                         upcoming_classes=upcoming_classes,
                         avg_attendance=avg_attendance,
                         upcoming=upcoming,
                         notifications=notifications,
                         rush_predictions=rush_predictions)


@faculty_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
@faculty_required
def schedule_class():
    """Schedule a new make-up class"""
    if request.method == 'POST':
        # Get form data
        course_name = request.form.get('course_name', '').strip()
        course_code = request.form.get('course_code', '').strip()
        section = request.form.get('section', '').strip()
        class_date = request.form.get('date', '')
        start_time = request.form.get('start_time', '')
        end_time = request.form.get('end_time', '')
        room = request.form.get('room', '').strip()
        reason = request.form.get('reason', '').strip()
        allow_late_entry = request.form.get('allow_late_entry') == 'on'
        enable_face_recognition = request.form.get('enable_face_recognition') == 'on'
        max_students = request.form.get('max_students', 50)
        
        # Validation
        errors = []
        
        if not course_name:
            errors.append('Course name is required.')
        if not section:
            errors.append('Section is required.')
        if not class_date:
            errors.append('Date is required.')
        if not start_time:
            errors.append('Start time is required.')
        if not end_time:
            errors.append('End time is required.')
        if not room:
            errors.append('Room is required.')
        
        # Parse date and time
        try:
            class_date_obj = datetime.strptime(class_date, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            if class_date_obj < date.today():
                errors.append('Cannot schedule a class in the past.')
            
            if start_time_obj >= end_time_obj:
                errors.append('End time must be after start time.')
                
        except ValueError:
            errors.append('Invalid date or time format.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('faculty/schedule_class.html')
        
        # Generate remedial code
        remedial_code = generate_remedial_code()
        
        # Calculate code expiry (end time + buffer)
        code_expiry = datetime.combine(class_date_obj, end_time_obj) + timedelta(minutes=15)
        
        # Create make-up class
        makeup_class = MakeUpClass(
            faculty_id=current_user.id,
            course_name=course_name,
            course_code=course_code,
            section=section,
            date=class_date_obj,
            start_time=start_time_obj,
            end_time=end_time_obj,
            room=room,
            reason=reason,
            remedial_code=remedial_code,
            code_expiry=code_expiry,
            allow_late_entry=allow_late_entry,
            enable_face_recognition=enable_face_recognition,
            max_students=int(max_students) if max_students else 50
        )
        
        # AI: Predict attendance
        try:
            prediction = predict_attendance(
                course_code=course_code,
                section=section,
                day_of_week=class_date_obj.weekday(),
                time_slot=start_time_obj.hour
            )
            makeup_class.predicted_attendance_pct = prediction['attendance_pct']
            makeup_class.rush_level = prediction['rush_level']
        except Exception as e:
            pass  # AI prediction optional
        
        # Generate QR code with URL for direct scanning
        try:
            # Get base URL for QR code
            base_url = request.host_url.rstrip('/')
            qr_path = generate_qr_code(remedial_code, 0, base_url=base_url)  # Use 0 as temp ID
            makeup_class.qr_code_path = qr_path
        except Exception as e:
            pass  # QR code optional
        
        try:
            db.session.add(makeup_class)
            db.session.commit()
            
            # Regenerate QR code with actual class ID
            try:
                base_url = request.host_url.rstrip('/')
                qr_path = generate_qr_code(remedial_code, makeup_class.id, base_url=base_url)
                makeup_class.qr_code_path = qr_path
                db.session.commit()
            except Exception as e:
                pass
            
            # Send notifications to enrolled students
            try:
                send_class_notification(makeup_class, 'class_scheduled')
            except Exception as e:
                pass  # Notification optional
            
            flash(f'Make-up class scheduled successfully! Remedial Code: {remedial_code}', 'success')
            return redirect(url_for('faculty.view_classes'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while scheduling the class.', 'error')
    
    # Get AI schedule recommendations
    recommendations = []
    try:
        recommendations = get_smart_schedule_recommendations(current_user.id)
    except Exception as e:
        pass
    
    courses = Course.query.all()
    
    return render_template('faculty/schedule_class.html', 
                         courses=courses,
                         recommendations=recommendations)


@faculty_bp.route('/classes')
@login_required
@faculty_required
def view_classes():
    """View all scheduled make-up classes"""
    # Filter parameters
    status_filter = request.args.get('status', 'all')
    course_filter = request.args.get('course', '')
    date_filter = request.args.get('date', '')
    
    # Base query
    query = MakeUpClass.query.filter_by(faculty_id=current_user.id)
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if course_filter:
        query = query.filter(MakeUpClass.course_name.ilike(f'%{course_filter}%'))
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(date=filter_date)
        except ValueError:
            pass
    
    # Order by date descending
    classes = query.order_by(MakeUpClass.date.desc(), MakeUpClass.start_time.desc()).all()
    
    # Update status for classes
    now = datetime.now()
    for cls in classes:
        class_start = datetime.combine(cls.date, cls.start_time)
        class_end = datetime.combine(cls.date, cls.end_time)
        
        if cls.status not in ['completed', 'cancelled']:
            if now > class_end:
                cls.status = 'completed'
            elif class_start <= now <= class_end:
                cls.status = 'ongoing'
            else:
                cls.status = 'upcoming'
    
    db.session.commit()
    
    return render_template('faculty/view_classes.html', 
                         classes=classes,
                         status_filter=status_filter,
                         course_filter=course_filter,
                         date_filter=date_filter)


@faculty_bp.route('/class/<int:class_id>')
@login_required
@faculty_required
def class_detail(class_id):
    """View details of a specific class"""
    makeup_class = MakeUpClass.query.filter_by(
        id=class_id, 
        faculty_id=current_user.id
    ).first_or_404()
    
    # Get attendance records
    attendances = MakeUpAttendance.query.filter_by(class_id=class_id).all()
    stats = makeup_class.get_attendance_stats()
    
    return render_template('faculty/class_detail.html',
                         makeup_class=makeup_class,
                         attendances=attendances,
                         stats=stats)


@faculty_bp.route('/class/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
@faculty_required
def edit_class(class_id):
    """Edit a scheduled class"""
    makeup_class = MakeUpClass.query.filter_by(
        id=class_id,
        faculty_id=current_user.id
    ).first_or_404()
    
    if makeup_class.status in ['completed', 'cancelled']:
        flash('Cannot edit a completed or cancelled class.', 'error')
        return redirect(url_for('faculty.view_classes'))
    
    if request.method == 'POST':
        makeup_class.course_name = request.form.get('course_name', '').strip()
        makeup_class.course_code = request.form.get('course_code', '').strip()
        makeup_class.section = request.form.get('section', '').strip()
        makeup_class.room = request.form.get('room', '').strip()
        makeup_class.reason = request.form.get('reason', '').strip()
        makeup_class.allow_late_entry = request.form.get('allow_late_entry') == 'on'
        makeup_class.max_students = int(request.form.get('max_students', 50))
        
        # Update date/time if provided
        new_date = request.form.get('date', '')
        new_start = request.form.get('start_time', '')
        new_end = request.form.get('end_time', '')
        
        time_changed = False
        
        if new_date:
            new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
            if new_date_obj != makeup_class.date:
                makeup_class.date = new_date_obj
                time_changed = True
        
        if new_start:
            new_start_obj = datetime.strptime(new_start, '%H:%M').time()
            if new_start_obj != makeup_class.start_time:
                makeup_class.start_time = new_start_obj
                time_changed = True
        
        if new_end:
            new_end_obj = datetime.strptime(new_end, '%H:%M').time()
            if new_end_obj != makeup_class.end_time:
                makeup_class.end_time = new_end_obj
                time_changed = True
        
        # Regenerate code if time changed
        if time_changed:
            makeup_class.remedial_code = generate_remedial_code()
            makeup_class.code_expiry = datetime.combine(
                makeup_class.date, 
                makeup_class.end_time
            ) + timedelta(minutes=15)
            
            # Regenerate QR code with URL
            try:
                base_url = request.host_url.rstrip('/')
                qr_path = generate_qr_code(makeup_class.remedial_code, makeup_class.id, base_url=base_url)
                makeup_class.qr_code_path = qr_path
            except Exception as e:
                pass
            
            # Send notification about schedule change
            try:
                send_class_notification(makeup_class, 'schedule_changed')
            except Exception as e:
                pass
        
        try:
            db.session.commit()
            flash('Class updated successfully.', 'success')
            return redirect(url_for('faculty.class_detail', class_id=class_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred.', 'error')
    
    return render_template('faculty/edit_class.html', makeup_class=makeup_class)


@faculty_bp.route('/class/<int:class_id>/cancel', methods=['POST'])
@login_required
@faculty_required
def cancel_class(class_id):
    """Cancel a scheduled class"""
    makeup_class = MakeUpClass.query.filter_by(
        id=class_id,
        faculty_id=current_user.id
    ).first_or_404()
    
    if makeup_class.status in ['completed', 'cancelled']:
        flash('Cannot cancel this class.', 'error')
        return redirect(url_for('faculty.view_classes'))
    
    makeup_class.status = 'cancelled'
    
    try:
        db.session.commit()
        
        # Send cancellation notification
        try:
            send_class_notification(makeup_class, 'class_cancelled')
        except Exception as e:
            pass
        
        flash('Class cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'error')
    
    return redirect(url_for('faculty.view_classes'))


@faculty_bp.route('/attendance')
@login_required
@faculty_required
def attendance():
    """View attendance records for all classes"""
    # Get completed classes
    classes = MakeUpClass.query.filter_by(
        faculty_id=current_user.id
    ).filter(MakeUpClass.status.in_(['completed', 'ongoing'])).order_by(
        MakeUpClass.date.desc()
    ).all()
    
    # Calculate overall stats
    total_students = 0
    total_present = 0
    total_late = 0
    
    for cls in classes:
        stats = cls.get_attendance_stats()
        total_students += stats['total']
        total_present += stats['present']
        total_late += stats['late']
    
    overall_pct = round((total_present + total_late) / total_students * 100, 1) if total_students > 0 else 0
    
    return render_template('faculty/attendance.html',
                         classes=classes,
                         total_students=total_students,
                         total_present=total_present,
                         total_late=total_late,
                         overall_pct=overall_pct)


@faculty_bp.route('/class/<int:class_id>/attendance')
@login_required
@faculty_required
def class_attendance(class_id):
    """View attendance for a specific class"""
    makeup_class = MakeUpClass.query.filter_by(
        id=class_id,
        faculty_id=current_user.id
    ).first_or_404()
    
    attendances = MakeUpAttendance.query.filter_by(class_id=class_id).join(
        User, MakeUpAttendance.student_id == User.id
    ).add_columns(
        User.name, User.email
    ).all()
    
    stats = makeup_class.get_attendance_stats()
    
    return render_template('faculty/class_attendance.html',
                         makeup_class=makeup_class,
                         attendances=attendances,
                         stats=stats)


@faculty_bp.route('/class/<int:class_id>/export')
@login_required
@faculty_required
def export_attendance(class_id):
    """Export attendance as CSV"""
    makeup_class = MakeUpClass.query.filter_by(
        id=class_id,
        faculty_id=current_user.id
    ).first_or_404()
    
    attendances = MakeUpAttendance.query.filter_by(class_id=class_id).join(
        User, MakeUpAttendance.student_id == User.id
    ).add_columns(
        User.name, User.email
    ).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Make-Up Class Attendance Report'])
    writer.writerow([f'Course: {makeup_class.course_name}'])
    writer.writerow([f'Section: {makeup_class.section}'])
    writer.writerow([f'Date: {makeup_class.date}'])
    writer.writerow([f'Time: {makeup_class.start_time} - {makeup_class.end_time}'])
    writer.writerow([f'Room: {makeup_class.room}'])
    writer.writerow([])
    writer.writerow(['Student Name', 'Email', 'Status', 'Timestamp'])
    
    # Data
    for attendance, name, email in attendances:
        writer.writerow([
            name,
            email,
            attendance.attendance_status.capitalize(),
            attendance.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Stats
    stats = makeup_class.get_attendance_stats()
    writer.writerow([])
    writer.writerow(['Statistics'])
    writer.writerow([f'Total: {stats["total"]}'])
    writer.writerow([f'Present: {stats["present"]}'])
    writer.writerow([f'Late: {stats["late"]}'])
    writer.writerow([f'Attendance %: {stats["attendance_pct"]}%'])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_{makeup_class.course_code}_{makeup_class.date}.csv'
    )


@faculty_bp.route('/reports')
@login_required
@faculty_required
def reports():
    """View reports and analytics"""
    # Get all completed classes
    classes = MakeUpClass.query.filter_by(
        faculty_id=current_user.id,
        status='completed'
    ).order_by(MakeUpClass.date.desc()).all()
    
    # Prepare chart data
    attendance_data = []
    for cls in classes[:10]:  # Last 10 classes
        stats = cls.get_attendance_stats()
        attendance_data.append({
            'label': f'{cls.course_code} ({cls.date})',
            'present': stats['present'],
            'late': stats['late'],
            'absent': stats['absent'],
            'pct': stats['attendance_pct']
        })
    
    # Course-wise statistics
    course_stats = {}
    for cls in classes:
        course = cls.course_name
        if course not in course_stats:
            course_stats[course] = {'total': 0, 'present': 0, 'classes': 0}
        
        stats = cls.get_attendance_stats()
        course_stats[course]['total'] += stats['total']
        course_stats[course]['present'] += stats['present'] + stats['late']
        course_stats[course]['classes'] += 1
    
    return render_template('faculty/reports.html',
                         attendance_data=attendance_data,
                         course_stats=course_stats)


@faculty_bp.route('/notifications')
@login_required
@faculty_required
def notifications():
    """View all notifications"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('faculty/notifications.html', notifications=notifications)


@faculty_bp.route('/notification/<int:notif_id>/read', methods=['POST'])
@login_required
@faculty_required
def mark_notification_read(notif_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(
        id=notif_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({'success': True})


@faculty_bp.route('/api/stats')
@login_required
@faculty_required
def api_stats():
    """API endpoint for dashboard stats"""
    total_classes = MakeUpClass.query.filter_by(faculty_id=current_user.id).count()
    upcoming_classes = MakeUpClass.query.filter_by(
        faculty_id=current_user.id,
        status='upcoming'
    ).count()
    
    completed_classes = MakeUpClass.query.filter_by(
        faculty_id=current_user.id,
        status='completed'
    ).all()
    
    avg_attendance = 0
    if completed_classes:
        total_pct = sum([c.get_attendance_stats()['attendance_pct'] for c in completed_classes])
        avg_attendance = round(total_pct / len(completed_classes), 1)
    
    return jsonify({
        'total_classes': total_classes,
        'upcoming_classes': upcoming_classes,
        'avg_attendance': avg_attendance
    })
