from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from models.models import db, User, Event, Registration, Notification
from functools import wraps

participant_bp = Blueprint('participant', __name__)

# Participant authentication decorator
def participant_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') or session.get('user_role') != 'participant':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@participant_bp.route('/dashboard')  # Changed from '/participant_dashboard'
@participant_required
def dashboard():
    try:
        return render_template('participant_dashboard.html')
    except Exception as e:
        return f"Error loading participant dashboard: {e}", 500

@participant_bp.route('/api/my_registrations')
@participant_required
def get_my_registrations():
    try:
        user_id = session.get('user_id')
        
        # Get all registrations for this participant
        user_registrations = Registration.query.filter_by(user_id=user_id).all()
        
        # Enrich data with event details
        result = []
        for reg in user_registrations:
            event = Event.query.get(reg.event_id)
            
            if event:
                registration_data = {
                    "id": reg.id,
                    "event_id": reg.event_id,
                    "event_name": event.name,
                    "event_date": event.date,
                    "event_tag": event.tag,
                    "registration_date": reg.registration_date.strftime("%Y-%m-%d") if reg.registration_date else None,
                    "payment_id": reg.payment_id,
                    "payment_status": reg.payment_status,
                    "has_exploration": event.has_exploration
                }
                result.append(registration_data)
                
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@participant_bp.route('/api/my_notifications')
@participant_required
def get_my_notifications():
    try:
        user_id = session.get('user_id')
        
        # Get personal notifications and broadcasts
        user_notifications = Notification.query.filter(
            (Notification.user_id == user_id) | (Notification.user_id == None)
        ).order_by(Notification.created_at.desc()).all()
        
        return jsonify([notification.to_dict() for notification in user_notifications])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@participant_bp.route('/api/mark_notification_read/<int:notification_id>', methods=['POST'])
@participant_required
def mark_notification_read(notification_id):
    try:
        user_id = session.get('user_id')
        notification = Notification.query.get(notification_id)
        
        if notification and (notification.user_id == user_id or notification.user_id is None):
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True})
        
        return jsonify({'error': 'Notification not found or access denied'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500