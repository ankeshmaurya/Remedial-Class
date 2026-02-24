"""
Database Models for Make-Up Class & Remedial Code Module
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for both faculty and students"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'faculty' or 'student'
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    makeup_classes = db.relationship('MakeUpClass', backref='faculty', lazy='dynamic',
                                     foreign_keys='MakeUpClass.faculty_id')
    attendances = db.relationship('MakeUpAttendance', backref='student', lazy='dynamic',
                                  foreign_keys='MakeUpAttendance.student_id')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the password matches"""
        return check_password_hash(self.password_hash, password)
    
    def is_faculty(self):
        """Check if user is faculty"""
        return self.role == 'faculty'
    
    def is_student(self):
        """Check if user is student"""
        return self.role == 'student'
    
    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


class MakeUpClass(db.Model):
    """Model for make-up/remedial classes"""
    __tablename__ = 'makeup_classes'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    course_code = db.Column(db.String(20))
    section = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.Text)
    
    # Remedial code settings
    remedial_code = db.Column(db.String(10), unique=True, nullable=False)
    code_expiry = db.Column(db.DateTime, nullable=False)
    
    # Class settings
    allow_late_entry = db.Column(db.Boolean, default=True)
    enable_face_recognition = db.Column(db.Boolean, default=False)
    max_students = db.Column(db.Integer, default=50)
    
    # Status: 'upcoming', 'ongoing', 'completed', 'cancelled'
    status = db.Column(db.String(20), default='upcoming')
    
    # AI predictions
    predicted_attendance_pct = db.Column(db.Float)
    rush_level = db.Column(db.String(20))  # 'low', 'medium', 'high', 'overcrowded'
    
    # QR Code path
    qr_code_path = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('MakeUpAttendance', backref='makeup_class', 
                                  lazy='dynamic', cascade='all, delete-orphan')
    
    def get_attendance_stats(self):
        """Get attendance statistics for this class"""
        total = self.attendances.count()
        present = self.attendances.filter_by(attendance_status='present').count()
        late = self.attendances.filter_by(attendance_status='late').count()
        absent = self.attendances.filter_by(attendance_status='absent').count()
        
        return {
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'attendance_pct': round((present + late) / total * 100, 1) if total > 0 else 0
        }
    
    def is_code_valid(self):
        """Check if the remedial code is still valid"""
        return datetime.utcnow() < self.code_expiry and self.status not in ['completed', 'cancelled']
    
    def __repr__(self):
        return f'<MakeUpClass {self.course_name} - {self.date}>'


class MakeUpAttendance(db.Model):
    """Model for make-up class attendance records"""
    __tablename__ = 'makeup_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('makeup_classes.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Attendance details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_status = db.Column(db.String(20), default='present')  # 'present', 'late', 'absent'
    
    # Location verification (optional)
    ip_address = db.Column(db.String(50))
    device_info = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Unique constraint: one attendance per student per class
    __table_args__ = (
        db.UniqueConstraint('class_id', 'student_id', name='unique_student_class_attendance'),
    )
    
    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.class_id}>'


class Notification(db.Model):
    """Model for user notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification content
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # 'class_scheduled', 'class_cancelled', 'reminder', 'code_active'
    
    # Link to related content
    related_class_id = db.Column(db.Integer, db.ForeignKey('makeup_classes.id'))
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_email_sent = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationship
    related_class = db.relationship('MakeUpClass', backref='notifications')
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Notification {self.title} for User {self.user_id}>'


class Course(db.Model):
    """Model for courses (for dropdown selections)"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    credits = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<Course {self.code} - {self.name}>'


class StudentEnrollment(db.Model):
    """Model for student course enrollments"""
    __tablename__ = 'student_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    section = db.Column(db.String(20), nullable=False)
    semester = db.Column(db.String(20))  # e.g., 'Fall 2026'
    
    # Relationships
    student = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', 'section', name='unique_student_course_section'),
    )
    
    def __repr__(self):
        return f'<Enrollment Student {self.student_id} - Course {self.course_id}>'


class AttendancePredictionData(db.Model):
    """Model for storing historical data for AI predictions"""
    __tablename__ = 'attendance_prediction_data'
    
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20))
    section = db.Column(db.String(20))
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday
    time_slot = db.Column(db.String(20))  # 'morning', 'afternoon', 'evening'
    actual_attendance_pct = db.Column(db.Float)
    total_enrolled = db.Column(db.Integer)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PredictionData {self.course_code} - {self.actual_attendance_pct}%>'
