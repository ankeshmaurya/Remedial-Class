# Make-Up Class & Remedial Code Module

A comprehensive Flask-based web application for managing make-up classes and remedial sessions with AI-powered features.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-Educational-yellow.svg)

## 🌟 Features

### Faculty Dashboard
- Schedule and manage make-up classes
- Generate unique remedial codes (MUP-XXXXXX format)
- Generate styled QR codes for easy attendance marking
- View and download QR codes for distribution
- View detailed attendance reports with statistics
- AI-powered scheduling recommendations
- Rush prediction for optimal class timing
- Export attendance data to CSV
- Real-time class status updates

### Student Dashboard
- View available make-up classes
- Mark attendance using remedial codes or QR scanning
- Direct QR code scanning with camera
- View attendance history with status indicators
- Receive real-time notifications about classes
- Enroll in courses

### AI Integration
- Smart scheduling recommendations based on historical data
- Rush hour prediction to avoid crowded times
- Attendance pattern analysis
- Predicted attendance percentage for classes
- Automated notifications for class updates

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

1. **Clone or download the project**

2. **Create and activate virtual environment (optional but recommended):**
   ```powershell
   # Windows PowerShell
   py -m venv venv
   .\venv\Scripts\Activate
   ```
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```powershell
   # Windows
   py app.py
   ```
   ```bash
   # macOS/Linux
   python app.py
   ```

5. **Access the application:**
   - Open browser and navigate to `http://localhost:5000`
   - Default faculty account: Register as faculty to get started

## 📁 Project Structure

```
Remidial Class/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── instance/                   # SQLite database location
│   └── makeup.db
├── makeup_module/
│   ├── __init__.py
│   ├── config.py              # Application configuration
│   ├── models.py              # Database models (SQLAlchemy)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication routes
│   │   ├── faculty.py         # Faculty dashboard routes
│   │   └── student.py         # Student dashboard routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── code_generator.py  # Remedial code & QR generation
│   │   ├── ai_prediction.py   # AI prediction service
│   │   └── notification_service.py  # Email & in-app notifications
│   ├── templates/
│   │   ├── base.html          # Base layout template
│   │   ├── auth/              # Login, register, profile templates
│   │   ├── faculty/           # Faculty dashboard templates
│   │   └── student/           # Student dashboard templates
│   └── static/
│       ├── css/
│       │   └── style.css      # Main stylesheet (modern design)
│       ├── js/
│       │   └── main.js        # Client-side JavaScript
│       ├── qrcodes/           # Generated QR code images
│       └── uploads/           # User uploads
```

## 🎨 UI Features

- **Modern 2026 Design Standard**
- Deep Blue/Indigo primary color scheme
- Emerald accent colors
- Fully responsive design (mobile-friendly)
- Dark mode support
- Smooth micro-animations
- Card-based layout with soft shadows
- Toast notifications for user feedback

## 📱 QR Code Features

- **Styled QR codes** with gradient colors (Indigo to Emerald)
- **Download QR** codes as PNG images
- **Print QR** codes directly from the browser
- **Direct scan** URLs that redirect students to attendance marking
- **Cross-platform** compatibility with any camera app

## 🔧 Configuration

The application uses SQLite by default. For custom configuration, set environment variables:

```env
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
SQLALCHEMY_DATABASE_URI=sqlite:///makeup.db
```

Optional mail configuration for notifications:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## 📝 Database Models

- **User**: Faculty and student accounts
- **Course**: Course information
- **MakeUpClass**: Make-up class sessions
- **MakeUpAttendance**: Attendance records
- **Notification**: In-app notifications
- **StudentEnrollment**: Course enrollments
- **AttendancePredictionData**: AI training data

## 🛡️ Security Features

- CSRF protection
- Password hashing with Werkzeug
- Session-based authentication
- Role-based access control
- Input validation

## 📊 API Endpoints

### Faculty API
- `POST /faculty/api/classes/<id>/regenerate-code` - Regenerate remedial code
- `GET /faculty/api/schedule-recommendations` - Get AI recommendations

### Student API
- `POST /student/api/mark-attendance` - Mark attendance via API
- `POST /student/api/notifications/<id>/read` - Mark notification as read

## 📧 Contact & Support

For issues or feature requests, please contact the system administrator.

## 📄 License

This project is developed for educational purposes.

---

**Make-Up Class & Remedial Code Module** - Modern Education Management System © 2026
