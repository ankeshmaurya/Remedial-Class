"""
AI Prediction Service
Provides attendance prediction and smart scheduling recommendations
"""
import numpy as np
from datetime import datetime, timedelta, date
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle
import os


class AttendancePredictionModel:
    """
    Machine Learning model for predicting class attendance
    Uses historical attendance data to predict rush levels
    """
    
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'attendance_model.pkl'
        )
    
    def _get_time_slot(self, hour):
        """Convert hour to time slot category"""
        if hour < 12:
            return 'morning'
        elif hour < 17:
            return 'afternoon'
        else:
            return 'evening'
    
    def _prepare_features(self, course_code, section, day_of_week, time_slot_hour):
        """Prepare feature vector for prediction"""
        # Convert time slot
        time_slot = self._get_time_slot(time_slot_hour)
        
        # Create feature dictionary
        features = {
            'day_of_week': day_of_week,
            'time_slot_morning': 1 if time_slot == 'morning' else 0,
            'time_slot_afternoon': 1 if time_slot == 'afternoon' else 0,
            'time_slot_evening': 1 if time_slot == 'evening' else 0,
            'is_monday': 1 if day_of_week == 0 else 0,
            'is_friday': 1 if day_of_week == 4 else 0,
            'is_weekend': 1 if day_of_week >= 5 else 0,
        }
        
        return np.array([[
            features['day_of_week'],
            features['time_slot_morning'],
            features['time_slot_afternoon'],
            features['time_slot_evening'],
            features['is_monday'],
            features['is_friday'],
            features['is_weekend']
        ]])
    
    def train(self, historical_data):
        """
        Train the model on historical attendance data
        
        Args:
            historical_data: List of dicts with course_code, section, day_of_week, 
                           time_slot, attendance_pct
        """
        if not historical_data or len(historical_data) < 10:
            return False
        
        X = []
        y = []
        
        for record in historical_data:
            features = self._prepare_features(
                record.get('course_code', ''),
                record.get('section', ''),
                record['day_of_week'],
                record['time_slot']
            )[0]
            X.append(features)
            
            # Classify attendance percentage into categories
            pct = record['attendance_pct']
            if pct >= 80:
                label = 'high'
            elif pct >= 50:
                label = 'medium'
            else:
                label = 'low'
            y.append(label)
        
        X = np.array(X)
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Train Random Forest model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X, y_encoded)
        self.is_trained = True
        
        # Save model
        self._save_model()
        
        return True
    
    def predict(self, course_code, section, day_of_week, time_slot_hour):
        """
        Predict attendance for a class
        
        Args:
            course_code: Course code
            section: Section identifier
            day_of_week: 0=Monday, 6=Sunday
            time_slot_hour: Hour of the day (0-23)
        
        Returns:
            dict: Prediction results with attendance_pct and rush_level
        """
        # If model not trained, return default prediction based on heuristics
        if not self.is_trained:
            return self._heuristic_prediction(day_of_week, time_slot_hour)
        
        features = self._prepare_features(course_code, section, day_of_week, time_slot_hour)
        
        # Get prediction and probabilities
        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]
        
        rush_level = self.label_encoder.inverse_transform([prediction])[0]
        
        # Estimate attendance percentage based on probabilities
        if rush_level == 'high':
            attendance_pct = 75 + (probabilities.max() * 25)
        elif rush_level == 'medium':
            attendance_pct = 50 + (probabilities.max() * 25)
        else:
            attendance_pct = 20 + (probabilities.max() * 30)
        
        return {
            'attendance_pct': round(attendance_pct, 1),
            'rush_level': rush_level,
            'confidence': round(probabilities.max() * 100, 1)
        }
    
    def _heuristic_prediction(self, day_of_week, time_slot_hour):
        """
        Make prediction based on simple heuristics when model isn't trained
        """
        base_attendance = 60
        
        # Day adjustments
        if day_of_week == 0:  # Monday
            base_attendance += 10
        elif day_of_week == 4:  # Friday
            base_attendance -= 15
        elif day_of_week >= 5:  # Weekend
            base_attendance -= 20
        
        # Time adjustments
        if time_slot_hour < 9:  # Early morning
            base_attendance -= 15
        elif time_slot_hour >= 17:  # Evening
            base_attendance -= 10
        elif 10 <= time_slot_hour <= 14:  # Mid-day
            base_attendance += 5
        
        # Add some randomness
        base_attendance += np.random.randint(-5, 6)
        
        # Clamp to valid range
        base_attendance = max(20, min(95, base_attendance))
        
        # Determine rush level
        if base_attendance >= 75:
            rush_level = 'high'
        elif base_attendance >= 50:
            rush_level = 'medium'
        else:
            rush_level = 'low'
        
        return {
            'attendance_pct': round(base_attendance, 1),
            'rush_level': rush_level,
            'confidence': 65.0  # Lower confidence for heuristic
        }
    
    def _save_model(self):
        """Save trained model to disk"""
        if self.model and self.is_trained:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'label_encoder': self.label_encoder
                }, f)
    
    def _load_model(self):
        """Load trained model from disk"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.label_encoder = data['label_encoder']
                    self.is_trained = True
                return True
            except Exception:
                pass
        return False


# Global model instance
_prediction_model = AttendancePredictionModel()


def predict_attendance(course_code, section, day_of_week, time_slot):
    """
    Predict attendance for a make-up class
    
    Args:
        course_code: Course code
        section: Section identifier  
        day_of_week: 0=Monday, 6=Sunday
        time_slot: Hour of the day (0-23)
    
    Returns:
        dict: Prediction with attendance_pct and rush_level
    """
    # Try to load model if not trained
    if not _prediction_model.is_trained:
        _prediction_model._load_model()
    
    return _prediction_model.predict(course_code, section, day_of_week, time_slot)


def get_smart_schedule_recommendations(faculty_id, target_date=None):
    """
    Get smart scheduling recommendations for a faculty member
    
    Args:
        faculty_id: ID of the faculty member
        target_date: Target date for scheduling (default: next 7 days)
    
    Returns:
        list: List of recommended time slots with predicted attendance
    """
    if target_date is None:
        target_date = date.today() + timedelta(days=1)
    
    recommendations = []
    
    # Generate recommendations for next 5 weekdays
    current_date = target_date
    days_checked = 0
    
    while days_checked < 5:
        # Skip weekends for recommendations
        if current_date.weekday() < 5:
            day_of_week = current_date.weekday()
            
            # Check different time slots
            time_slots = [
                (9, '09:00 - 10:30', 'Morning'),
                (11, '11:00 - 12:30', 'Late Morning'),
                (14, '14:00 - 15:30', 'Afternoon'),
                (16, '16:00 - 17:30', 'Late Afternoon')
            ]
            
            for hour, time_range, slot_name in time_slots:
                prediction = predict_attendance('', '', day_of_week, hour)
                
                recommendations.append({
                    'date': current_date.isoformat(),
                    'day_name': current_date.strftime('%A'),
                    'time_slot': slot_name,
                    'time_range': time_range,
                    'predicted_attendance': prediction['attendance_pct'],
                    'rush_level': prediction['rush_level'],
                    'confidence': prediction.get('confidence', 70),
                    'recommendation_score': _calculate_recommendation_score(prediction)
                })
            
            days_checked += 1
        
        current_date += timedelta(days=1)
    
    # Sort by recommendation score (higher is better)
    recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
    
    return recommendations[:10]  # Return top 10 recommendations


def _calculate_recommendation_score(prediction):
    """
    Calculate a recommendation score based on prediction
    Higher attendance + medium rush = better score
    """
    attendance_score = prediction['attendance_pct']
    
    # Rush level adjustment (prefer medium rush - not too empty, not overcrowded)
    rush_adjustment = {
        'low': -10,      # Too empty might indicate inconvenient time
        'medium': +15,   # Optimal
        'high': -5       # Might be overcrowded
    }.get(prediction['rush_level'], 0)
    
    return round(attendance_score + rush_adjustment, 1)


def train_model_with_data(historical_data):
    """
    Train the prediction model with historical attendance data
    
    Args:
        historical_data: List of attendance records
    
    Returns:
        bool: True if training successful
    """
    return _prediction_model.train(historical_data)


def get_conflict_detection(faculty_id, proposed_date, proposed_start, proposed_end):
    """
    Check for scheduling conflicts
    
    Args:
        faculty_id: Faculty ID
        proposed_date: Proposed date
        proposed_start: Proposed start time
        proposed_end: Proposed end time
    
    Returns:
        list: List of conflicting classes
    """
    from ..models import MakeUpClass
    
    conflicts = MakeUpClass.query.filter(
        MakeUpClass.faculty_id == faculty_id,
        MakeUpClass.date == proposed_date,
        MakeUpClass.status.in_(['upcoming', 'ongoing'])
    ).all()
    
    conflicting = []
    for cls in conflicts:
        # Check time overlap
        if not (proposed_end <= cls.start_time or proposed_start >= cls.end_time):
            conflicting.append({
                'class_id': cls.id,
                'course': cls.course_name,
                'time': f'{cls.start_time} - {cls.end_time}'
            })
    
    return conflicting
