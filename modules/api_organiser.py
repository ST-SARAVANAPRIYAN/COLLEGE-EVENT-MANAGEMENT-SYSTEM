from flask import Blueprint, jsonify, session
from models.models import db, Event, Registration, User, Notification
import traceback

api_organiser_bp = Blueprint('api_organiser', __name__, url_prefix='/api/organiser')

@api_organiser_bp.route('/events', methods=['GET'])
def get_organiser_events():
    """
    Get all events created by the current logged-in organiser.
    This API is used by the organiser dashboard to display events.
    """
    try:
        user_id = session.get('user_id')
        print(f"API: Getting events for user_id: {user_id}, role: {session.get('user_role')}")
        
        if not user_id or session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        
        # Get all events created by this organiser
        events = Event.query.filter_by(created_by=user_id).all()
        print(f"Found {len(events)} events for this organiser")
        
        result = []
        for event in events:
            # For each event, get the registration count
            registration_count = Registration.query.filter_by(event_id=event.id).count()
            
            # Get sub-event IDs
            sub_events = []
            if hasattr(event, 'sub_events'):
                sub_events = [se.id for se in event.sub_events]
                
            event_data = event.to_dict()
            event_data['registration_count'] = registration_count
            event_data['sub_events'] = sub_events
            
            result.append(event_data)
            
        return jsonify({
            'success': True,
            'events': result
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
