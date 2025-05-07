from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from models.models import db, User, Event, Registration, Notification, Resource, ResourceAllocation
from utils.email_service import send_email
from functools import wraps
from datetime import datetime
import json

organiser_bp = Blueprint('organiser', __name__)

# Organiser authentication decorator
def organiser_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') or session.get('user_role') != 'organiser':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@organiser_bp.route('/organiser_dashboard')
@organiser_required
def dashboard():
    try:
        return render_template('organiser_dashboard.html')
    except Exception as e:
        return f"Error loading organiser dashboard: {e}", 500

@organiser_bp.route('/organiser/events')
@organiser_required
def events():
    try:
        return render_template('organiser_events.html')
    except Exception as e:
        return f"Error loading events page: {e}", 500

@organiser_bp.route('/organiser/create_event')
@organiser_required
def create_event():
    try:
        return render_template('organiser_create_event.html')
    except Exception as e:
        return f"Error loading create event page: {e}", 500

@organiser_bp.route('/organiser/resources')
@organiser_required
def resources():
    try:
        return render_template('organiser_resources.html')
    except Exception as e:
        return f"Error loading resources page: {e}", 500

@organiser_bp.route('/organiser/notifications')
@organiser_required
def notifications():
    try:
        return render_template('organiser_notifications.html')
    except Exception as e:
        return f"Error loading notifications page: {e}", 500

@organiser_bp.route('/organiser/reports')
@organiser_required
def reports():
    try:
        return render_template('organiser_reports.html')
    except Exception as e:
        return f"Error loading reports page: {e}", 500

@organiser_bp.route('/organiser/profile')
@organiser_required
def profile():
    try:
        user = User.query.get(session.get('user_id'))
        return render_template('organiser_profile.html', user=user)
    except Exception as e:
        return f"Error loading profile page: {e}", 500

@organiser_bp.route('/organiser/edit_event/<int:event_id>')
@organiser_required
def edit_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        # Check if event belongs to current organiser
        if event.created_by != session.get('user_id') and session.get('user_role') != 'admin':
            return redirect(url_for('organiser.events'))
        return render_template('organiser_edit_event.html', event=event)
    except Exception as e:
        return f"Error loading edit event page: {e}", 500

@organiser_bp.route('/api/registrations')
@organiser_required
def get_registrations():
    try:
        # Get all registrations for events created by this organiser
        user_id = session.get('user_id')
        
        # Find events created by this organiser
        events_created = Event.query.filter_by(created_by=user_id).all()
        event_ids = [event.id for event in events_created]
        
        # Find registrations for these events
        event_registrations = Registration.query.filter(Registration.event_id.in_(event_ids)).all()
        
        # Enrich data with event and user details
        result = []
        for reg in event_registrations:
            event = Event.query.get(reg.event_id)
            user = User.query.get(reg.user_id)
            
            if event and user:
                registration_data = {
                    "id": reg.id,
                    "event_id": reg.event_id,
                    "event_name": event.name,
                    "event_date": event.date,
                    "event_tag": event.tag,
                    "user_id": reg.user_id,
                    "user_name": user.name,
                    "user_email": user.email,
                    "registration_date": reg.registration_date.strftime("%Y-%m-%d") if reg.registration_date else None,
                    "payment_id": reg.payment_id,
                    "payment_status": reg.payment_status
                }
                result.append(registration_data)
                
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/notifications', methods=['POST'])
@organiser_required
def send_notification():
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        # Target audience (optional)
        event_id = data.get('event_id')  # If targeting registrants of a specific event
        
        # Create notification
        new_notification = Notification(
            message=message,
            created_by=session.get('user_id')
        )
        
        if event_id:
            # Send to users registered for this event
            reg_user_ids = [r.user_id for r in Registration.query.filter_by(event_id=int(event_id)).all()]
            for user_id in reg_user_ids:
                user_notification = Notification(
                    message=message,
                    created_by=session.get('user_id'),
                    user_id=user_id
                )
                db.session.add(user_notification)
                
                # Also send email
                user = User.query.get(user_id)
                if user:
                    send_email(
                        user.email,
                        "Event Notification",
                        message
                    )
        else:
            # Organizers can only send to all participants
            participant_user_ids = [u.id for u in User.query.filter_by(role='participant').all()]
            for user_id in participant_user_ids:
                user_notification = Notification(
                    message=message,
                    created_by=session.get('user_id'),
                    user_id=user_id
                )
                db.session.add(user_notification)
                
                # Also send email
                user = User.query.get(user_id)
                if user:
                    send_email(
                        user.email,
                        "CEMS Notification",
                        message
                    )
                
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/analytics/events')
@organiser_required
def get_event_analytics():
    try:
        user_id = session.get('user_id')
        
        # Get registration counts by event for this organiser's events
        event_counts = {}
        events_created = Event.query.filter_by(created_by=user_id).all()
        event_ids = [event.id for event in events_created]
        
        for reg in Registration.query.filter(Registration.event_id.in_(event_ids)).all():
            event_id = reg.event_id
            if event_id in event_counts:
                event_counts[event_id] += 1
            else:
                event_counts[event_id] = 1
                
        # Prepare results
        result = []
        for event_id, count in event_counts.items():
            event = Event.query.get(event_id)
            if event:
                result.append({
                    "event_id": event_id,
                    "event_name": event.name,
                    "registrations": count,
                    "tag": event.tag
                })
                
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/resources', methods=['GET'])
def get_resources():
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get all resources
        resources = Resource.query.all()
        return jsonify([r.to_dict() for r in resources])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/resources', methods=['POST'])
def create_resource():
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        data = request.json or {}
        
        # Required fields
        if 'name' not in data or 'resource_type' not in data:
            return jsonify({'error': 'Name and resource type are required'}), 400
            
        # Create new resource
        new_resource = Resource(
            name=data.get('name'),
            resource_type=data.get('resource_type'),
            total_quantity=data.get('total_quantity', 1),
            available_quantity=data.get('available_quantity', data.get('total_quantity', 1)),
            description=data.get('description'),
            properties=json.dumps(data.get('properties', {}))
        )
        
        db.session.add(new_resource)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'resource': new_resource.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/resources/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
            
        data = request.json or {}
        
        # Update fields
        if 'name' in data:
            resource.name = data['name']
        if 'resource_type' in data:
            resource.resource_type = data['resource_type']
        if 'total_quantity' in data:
            resource.total_quantity = data['total_quantity']
        if 'available_quantity' in data:
            resource.available_quantity = data['available_quantity']
        if 'description' in data:
            resource.description = data['description']
        if 'properties' in data:
            resource.properties = json.dumps(data['properties'])
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'resource': resource.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
            
        # Check if resource is allocated to any events
        if ResourceAllocation.query.filter_by(resource_id=resource_id).first():
            return jsonify({'error': 'Cannot delete a resource that is allocated to events'}), 400
            
        db.session.delete(resource)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/resource-allocations', methods=['POST'])
def allocate_resource():
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        data = request.json or {}
        
        # Required fields
        if not all(k in data for k in ['resource_id', 'event_id', 'quantity', 'allocation_start', 'allocation_end']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Check if resource exists
        resource = Resource.query.get(data['resource_id'])
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
            
        # Check if event exists
        event = Event.query.get(data['event_id'])
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        # Check if quantity is available
        if resource.available_quantity < data['quantity']:
            return jsonify({'error': 'Not enough resources available'}), 400
            
        # Create allocation
        allocation = ResourceAllocation(
            resource_id=data['resource_id'],
            event_id=data['event_id'],
            quantity=data['quantity'],
            allocation_start=datetime.fromisoformat(data['allocation_start'].replace('Z', '+00:00')),
            allocation_end=datetime.fromisoformat(data['allocation_end'].replace('Z', '+00:00')),
            notes=data.get('notes')
        )
        
        # Update available quantity
        resource.available_quantity -= data['quantity']
        
        db.session.add(allocation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'allocation': allocation.to_dict()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/resource-allocations/<int:allocation_id>', methods=['PUT'])
def update_allocation(allocation_id):
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        allocation = ResourceAllocation.query.get(allocation_id)
        if not allocation:
            return jsonify({'error': 'Allocation not found'}), 404
            
        data = request.json or {}
        
        # If returning resources
        if data.get('status') == 'returned' and allocation.status == 'allocated':
            resource = Resource.query.get(allocation.resource_id)
            if resource:
                resource.available_quantity += allocation.quantity
                
        # Update fields
        if 'status' in data:
            allocation.status = data['status']
        if 'notes' in data:
            allocation.notes = data['notes']
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'allocation': allocation.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/resources/by-event/<int:event_id>', methods=['GET'])
def get_resources_by_event(event_id):
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get all allocations for the event
        allocations = ResourceAllocation.query.filter_by(event_id=event_id).all()
        
        # Get the resources
        result = []
        for allocation in allocations:
            resource = Resource.query.get(allocation.resource_id)
            if resource:
                result.append({
                    'resource': resource.to_dict(),
                    'allocation': allocation.to_dict()
                })
                
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organiser_bp.route('/api/organiser/dashboard-stats', methods=['GET'])
@organiser_required
def get_dashboard_stats():
    try:
        user_id = session.get('user_id')
        
        # Get events created by this organiser
        events = Event.query.filter_by(created_by=user_id).all()
        event_count = len(events)
        
        # Get event IDs for registrations query
        event_ids = [e.id for e in events]
        
        # Get registrations for these events
        registrations = Registration.query.filter(Registration.event_id.in_(event_ids)).all() if event_ids else []
        registrations_count = len(registrations)
        
        # Get resources allocated to these events
        resource_count = 0
        if event_ids:
            resource_count = ResourceAllocation.query.filter(ResourceAllocation.event_id.in_(event_ids)).count()
        
        # Get notifications sent by this organiser
        notification_count = Notification.query.filter_by(created_by=user_id).count()
        
        # Get recent activity
        recent_activity = []
        
        # Add recent registrations
        recent_regs = Registration.query.filter(Registration.event_id.in_(event_ids)).order_by(
            Registration.registration_date.desc()).limit(3).all() if event_ids else []
            
        for reg in recent_regs:
            event = Event.query.get(reg.event_id)
            user = User.query.get(reg.user_id)
            if event and user:
                recent_activity.append({
                    'type': 'registration',
                    'message': f'New registration for "{event.name}" by {user.name}',
                    'time_ago': get_time_ago(reg.registration_date) if reg.registration_date else 'Recently'
                })
        
        # Add recent events created
        recent_events = Event.query.filter_by(created_by=user_id).order_by(
            Event.created_at.desc()).limit(3).all()
            
        for event in recent_events:
            recent_activity.append({
                'type': 'event_created',
                'message': f'You created a new event "{event.name}"',
                'time_ago': get_time_ago(event.created_at) if event.created_at else 'Recently'
            })
        
        # Add recent notifications
        recent_notifs = Notification.query.filter_by(created_by=user_id).order_by(
            Notification.created_at.desc()).limit(3).all()
            
        for notif in recent_notifs:
            target = 'all participants' if notif.user_id is None else 'a participant'
            recent_activity.append({
                'type': 'notification',
                'message': f'You sent notification to {target}',
                'time_ago': get_time_ago(notif.created_at) if notif.created_at else 'Recently'
            })
        
        # Sort activities by recency (assuming they all have created_at)
        recent_activity.sort(key=lambda x: x['time_ago'], reverse=True)
        
        return jsonify({
            'success': True,
            'stats': {
                'events': event_count,
                'registrations': registrations_count,
                'resources': resource_count,
                'notifications': notification_count
            },
            'recent_activity': recent_activity[:4]  # Limit to 4 most recent activities
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def get_time_ago(date_time):
    """Helper function to format time ago string"""
    if not date_time:
        return "Recently"
        
    now = datetime.now()
    diff = now - date_time
    
    days = diff.days
    
    if days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            minutes = diff.seconds // 60
            if minutes == 0:
                return "Just now"
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return f"{days} days ago"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        return date_time.strftime("%b %d, %Y")

@organiser_bp.route('/api/organiser/events', methods=['GET'])
@organiser_required
def get_organiser_events():
    try:
        user_id = session.get('user_id')
        
        # Get all events created by this organiser
        events = Event.query.filter_by(created_by=user_id).all()
        
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
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@organiser_bp.route('/api/organiser/registrations', methods=['GET'])
@organiser_required
def get_organiser_registrations():
    try:
        user_id = session.get('user_id')
        
        # Get event IDs created by this organiser
        event_ids = [e.id for e in Event.query.filter_by(created_by=user_id).all()]
        
        if not event_ids:
            return jsonify({
                'success': True,
                'registrations': []
            })
        
        # Get registrations for these events
        registrations = Registration.query.filter(Registration.event_id.in_(event_ids)).all()
        
        result = []
        for reg in registrations:
            event = Event.query.get(reg.event_id)
            user = User.query.get(reg.user_id)
            
            if event and user:
                reg_data = reg.to_dict()
                reg_data['event_name'] = event.name
                reg_data['user_name'] = user.name
                reg_data['user_email'] = user.email
                
                result.append(reg_data)
                
        return jsonify({
            'success': True,
            'registrations': result
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@organiser_bp.route('/api/organiser/notifications', methods=['GET'])
@organiser_required
def get_organiser_notifications():
    try:
        user_id = session.get('user_id')
        
        # Get notifications sent by this organiser
        notifications = Notification.query.filter_by(created_by=user_id).order_by(
            Notification.created_at.desc()).all()
            
        result = []
        for notif in notifications:
            notif_data = {
                'id': notif.id,
                'message': notif.message,
                'user_id': notif.user_id,
                'created_at': notif.created_at.strftime("%b %d, %Y %H:%M") if notif.created_at else None
            }
            
            # Add recipient info if notification was sent to a specific user
            if notif.user_id:
                user = User.query.get(notif.user_id)
                if user:
                    notif_data['recipient_name'] = user.name
                    notif_data['recipient_email'] = user.email
            
            result.append(notif_data)
            
        return jsonify({
            'success': True,
            'notifications': result
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500