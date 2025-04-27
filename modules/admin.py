from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from models.models import db, User, Event, Registration
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') or session.get('user_role') != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin_dashboard')
@admin_required
def dashboard():
    try:
        return render_template('admin_dashboard.html')
    except Exception as e:
        return f"Error loading admin dashboard: {e}", 500

@admin_bp.route('/api/users')
@admin_required
def get_users():
    try:
        # Remove passwords from response
        result = []
        for user in User.query.all():
            user_data = user.to_dict()
            result.append(user_data)
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/analytics/users')
@admin_required
def get_user_analytics():
    try:
        # Get user counts by role
        role_counts = {}
        for user in User.query.all():
            role = user.role
            if role in role_counts:
                role_counts[role] += 1
            else:
                role_counts[role] = 1
                
        return jsonify(role_counts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/analytics/events')
@admin_required
def get_event_analytics():
    try:
        # Get event counts by tag
        tag_counts = {}
        for event in Event.query.all():
            tag = event.tag
            if tag:
                if tag in tag_counts:
                    tag_counts[tag] += 1
                else:
                    tag_counts[tag] = 1
        
        # Get registration counts
        registrations = {
            'total': Registration.query.count(),
            'completed': Registration.query.filter_by(payment_status='completed').count(),
            'pending': Registration.query.filter_by(payment_status='pending').count()
        }
        
        return jsonify({
            'events_by_tag': tag_counts,
            'registrations': registrations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500