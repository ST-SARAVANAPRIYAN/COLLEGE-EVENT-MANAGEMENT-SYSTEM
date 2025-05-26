from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request, current_app
from models.models import db, User, Event, Registration, Notification, Resource, ResourceAllocation
from utils.email_service import send_email
from functools import wraps
from datetime import datetime, time as dt_time
import json
import os
from werkzeug.utils import secure_filename
# CSRF protection disabled as per requirement
# from flask_wtf.csrf import CSRFProtect

organiser_bp = Blueprint('organiser', __name__)

# CSRF protection disabled as per requirement
# csrf = CSRFProtect()

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
        # Get current user ID
        organiser_id = session.get('user_id')
        
        # Find all events created by this organiser
        events = Event.query.filter(
            (Event.created_by == organiser_id) | (Event.organiser_id == organiser_id)
        ).all()
        
        # Get event IDs
        event_ids = [event.id for event in events]
          # Find registrations with pending UPI payments for these events
        pending_payments = []
        if event_ids:
            pending_payments = db.session.query(Registration, Event, User)\
                .join(Event, Registration.event_id == Event.id)\
                .join(User, Registration.user_id == User.id)\
                .filter(Registration.event_id.in_(event_ids))\
                .filter(Registration.payment_status.in_(['pending', 'verification_pending']))\
                .all()
        
        return render_template('organiser_dashboard.html', 
                              pending_payments=pending_payments)
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

@organiser_bp.route('/organiser/payment_transactions')
@organiser_required
def payment_transactions():
    """Display payment transactions for the organizer's events"""
    try:
        # Get current user ID
        organiser_id = session.get('user_id')
        
        # Find all events created by this organiser
        events = Event.query.filter(
            (Event.created_by == organiser_id) | (Event.organiser_id == organiser_id)
        ).all()
        
        # Get event IDs
        event_ids = [event.id for event in events]
        
        # Find all transactions for these events
        transactions = []
        if event_ids:
            # Get all registrations for these events
            registrations = Registration.query.filter(Registration.event_id.in_(event_ids)).all()
            registration_ids = [reg.id for reg in registrations]
            
            if registration_ids:
                # Get all transactions for these registrations
                # Query registrations directly instead of transactions
                transactions = db.session.query(
                    Registration, Event, User
                ).join(
                    Event, Registration.event_id == Event.id
                ).join(
                    User, Registration.user_id == User.id
                ).filter(
                    Registration.id.in_(registration_ids),
                    Registration.payment_status == 'completed'
                ).order_by(
                    Registration.transaction_timestamp.desc()
                ).all()
        
        # Get statistics
        total_transactions = len(transactions)
        total_amount = sum(t[0].amount for t in transactions) if transactions else 0
        upi_transactions = sum(1 for t in transactions if t[0].payment_method == 'upi') if transactions else 0
        razorpay_transactions = sum(1 for t in transactions if t[0].payment_method == 'razorpay') if transactions else 0
        
        stats = {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'upi_transactions': upi_transactions,
            'razorpay_transactions': razorpay_transactions
        }
        
        return render_template(
            'organiser_transactions.html',
            transactions=transactions,
            stats=stats
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading transactions page: {e}", 500

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

@organiser_bp.route('/organiser/upi_verification')
@organiser_required
def upi_verification():
    """Display a dedicated page for UPI payment verification"""
    try:
        # Get current user ID
        organiser_id = session.get('user_id')
        
        # Find all events created by this organiser
        events = Event.query.filter(
            (Event.created_by == organiser_id) | (Event.organiser_id == organiser_id)
        ).all()
        
        # Get event IDs
        event_ids = [event.id for event in events]
        
        # Find registrations with pending UPI payments for these events
        pending_payments = []
        if event_ids:
            pending_payments = db.session.query(Registration, Event, User)\
                .join(Event, Registration.event_id == Event.id)\
                .join(User, Registration.user_id == User.id)\
                .filter(Registration.event_id.in_(event_ids))\
                .filter(Registration.payment_status.in_(['pending', 'verification_pending']))\
                .order_by(Registration.registration_date.desc())\
                .all()
        
        return render_template('organiser_upi_verification.html', 
                            pending_payments=pending_payments)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading UPI verification page: {e}", 500

@organiser_bp.route('/organiser/profile')
@organiser_required
def profile():
    try:
        user = User.query.get(session.get('user_id'))
        # Only load organiser profile, no verification/subscription logic
        return render_template('organiser_profile_new.html', user=user)
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
                    "event_date": event.start_date.strftime("%Y-%m-%d") if event.start_date else None,
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
        event_ids = [event.id for event_created in events_created]
        
        for reg in Registration.query.filter(Registration.event_id.in_(event_ids)).all():
            event_id = reg.event_id
            if (event_id in event_counts):
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

# CSRF protection disabled
@organiser_bp.route('/api/resources', methods=['GET'])
def get_resources():
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        user_id = session.get('user_id')
        # Organisers see only their own resources; admins see all
        if session.get('user_role') == 'organiser':
            resources = Resource.query.filter_by(created_by=user_id).all()
        else:
            resources = Resource.query.all()
        return jsonify([r.to_dict() for r in resources])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CSRF protection disabled
@organiser_bp.route('/api/resources', methods=['POST'])
def create_resource():
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        user_id = session.get('user_id')
        # Accept both JSON and multipart/form-data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form
            image_file = request.files.get('image')
        else:
            data = request.json or {}
            image_file = None
        # Required fields
        if 'name' not in data or 'category' not in data:
            return jsonify({'error': 'Name and resource type are required'}), 400
        # Handle image upload
        image_path = None
        if image_file and image_file.filename:
            from werkzeug.utils import secure_filename
            import os
            upload_dir = os.path.join('static', 'uploads', 'resource_images')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{image_file.filename}")
            image_path = os.path.join(upload_dir, filename)
            image_file.save(image_path)
            image_path = image_path.replace('\\', '/').replace('static/', '')  # Store relative to static
        # Create new resource
        new_resource = Resource(
            name=data.get('name'),
            category=data.get('category'),
            total_quantity=int(data.get('total_quantity', 1)),
            available_quantity=int(data.get('available_quantity', data.get('total_quantity', 1))),
            description=data.get('description'),
            image=image_path,
            created_by=user_id
        )
        db.session.add(new_resource)
        db.session.commit()
        return jsonify({
            'success': True,
            'resource': new_resource.to_dict()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# CSRF protection disabled
@organiser_bp.route('/api/resources/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        data = request.json or {}
        # --- Enhanced logic: enforce allocation constraints ---
        from models.models import ResourceAllocation
        # Calculate total allocated quantity (status = 'allocated')
        allocated = db.session.query(db.func.sum(ResourceAllocation.quantity)).filter(
            ResourceAllocation.resource_id == resource_id,
            ResourceAllocation.status == 'allocated'
        ).scalar() or 0
        new_total = data.get('total_quantity', resource.total_quantity)
        # Prevent reducing total below allocated
        if new_total < allocated:
            return jsonify({'error': f'Cannot set total quantity below allocated ({allocated}).'}), 400
        # Adjust available_quantity based on new total and allocations
        delta = new_total - resource.total_quantity
        if delta != 0:
            # If increasing, add delta to available
            if delta > 0:
                resource.available_quantity += delta
            # If decreasing, set available = total - allocated (never negative)
            else:
                resource.available_quantity = max(new_total - allocated, 0)
        resource.total_quantity = new_total
        # Update other fields
        if 'name' in data:
            resource.name = data['name']
        if 'category' in data:
            resource.category = data['category']
        if 'description' in data:
            resource.description = data['description']
        db.session.commit()
        return jsonify({
            'success': True,
            'resource': resource.to_dict(),
            'allocated': allocated
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# CSRF protection disabled
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

# CSRF protection disabled
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

# CSRF protection disabled
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

# CSRF protection disabled
@organiser_bp.route('/api/resource-allocations/<int:allocation_id>/deallocate', methods=['POST'])
@organiser_required
def deallocate_resource(allocation_id):
    try:
        allocation = ResourceAllocation.query.get(allocation_id)
        if not allocation:
            return jsonify({'success': False, 'error': 'Allocation not found'}), 404
        if allocation.status == 'returned':
            return jsonify({'success': False, 'error': 'Resource already deallocated'}), 400
        resource = Resource.query.get(allocation.resource_id)
        if resource:
            resource.available_quantity += allocation.quantity
        allocation.status = 'returned'
        allocation.returned_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Resource deallocated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# CSRF protection disabled
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

@organiser_bp.route('/api/resources/<int:resource_id>/allocations', methods=['GET'])
def get_resource_allocations(resource_id):
    try:
        # Get all allocations for the given resource
        allocations = ResourceAllocation.query.filter_by(resource_id=resource_id).all()
        result = []
        for allocation in allocations:
            event = Event.query.get(allocation.event_id)
            result.append({
                'allocation_id': allocation.id,
                'event_id': allocation.event_id,
                'event_name': event.name if event else 'Unknown',
                'allocation_start': allocation.allocated_at.strftime('%Y-%m-%dT%H:%M:%S') if allocation.allocated_at else '',
                'allocation_end': allocation.returned_at.strftime('%Y-%m-%dT%H:%M:%S') if allocation.returned_at else '',
                'quantity': allocation.quantity,
                'status': allocation.status
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
        events = Event.query.filter_by(created_by(user_id)).all()
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
        notification_count = Notification.query.filter_by(created_by(user_id)).count()
        
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
        recent_events = Event.query.filter_by(created_by(user_id)).order_by(
            Event.created_at.desc()).limit(3).all()
            
        for event in recent_events:
            recent_activity.append({
                'type': 'event_created',
                'message': f'You created a new event "{event.name}"',
                'time_ago': get_time_ago(event.created_at) if event.created_at else 'Recently'
            })
        
        # Add recent notifications
        recent_notifs = Notification.query.filter_by(created_by(user_id)).order_by(Notification.created_at.desc()).limit(3).all()
            
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

# This API endpoint has been moved to api_organiser.py
# to avoid route duplication and conflicts
# The functionality is now handled by api_organiser_bp

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
        notifications = Notification.query.filter_by(created_by(user_id)).order_by(
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

# CSRF protection disabled
@organiser_bp.route('/organiser/events/<int:event_id>', methods=['DELETE'])
@organiser_required
def delete_event_direct(event_id):
    """Route to handle direct deletion from frontend."""
    # Reuse the existing delete function logic
    return delete_organiser_event(event_id)

# CSRF protection disabled
@organiser_bp.route('/api/organiser/events/<int:event_id>', methods=['DELETE'])
@organiser_required
def delete_organiser_event(event_id):
    try:
        # Get the event
        event = Event.query.get_or_404(event_id)
        
        # Check if event belongs to current organiser
        if event.created_by != session.get('user_id') and session.get('user_role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized to delete this event'}), 403
        
        # Deallocate all resources for this event before deleting
        allocations = ResourceAllocation.query.filter_by(event_id=event_id).all()
        for alloc in allocations:
            try:
                if alloc.status == 'allocated':
                    resource = Resource.query.get(alloc.resource_id)
                    if resource:
                        resource.available_quantity += alloc.quantity
                    alloc.status = 'returned'
                    alloc.returned_at = datetime.utcnow()
            except Exception as alloc_e:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Error deallocating resource: {str(alloc_e)}'}), 500
        
        # Check if there are registrations
        registrations = Registration.query.filter_by(event_id=event_id).all()
        if registrations and session.get('user_role') != 'admin':
            return jsonify({'success': False, 'error': 'Cannot delete an event with existing registrations'}), 400
        
        # Delete registrations if admin is deleting the event
        if registrations and session.get('user_role') == 'admin':
            for reg in registrations:
                db.session.delete(reg)
        
        # Delete all resource allocations for this event
        for alloc in allocations:
            db.session.delete(alloc)
        
        # Delete the main event
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Event deleted successfully'})
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Error deleting event: {str(e)}'}), 500

# CSRF protection disabled
@organiser_bp.route('/api/events/create', methods=['POST'])
@organiser_required
def create_new_event():
    try:
        user_id = session.get('user_id')
          # Handle form data with file uploads
        if 'multipart/form-data' in request.content_type:
            data = request.form
            # Get uploaded files
            image_file = request.files.get('image')
            video_file = request.files.get('video')
            brochure_file = request.files.get('brochure')
        else:
            data = request.json
            image_file = video_file = brochure_file = None
        
        # Validate required fields
        required_fields = ['name', 'category', 'description', 'start_date', 'start_time', 'end_date', 'end_time', 'venue']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f"Missing required field: {field}"}), 400        # Process uploaded files
        image_path = video_path = brochure_path = None
        
        # Process and save uploaded files if provided
        if image_file and image_file.filename:
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{image_file.filename}")
            image_path = os.path.join('static/uploads/images', filename)
            image_file.save(image_path)
            
        if video_file and video_file.filename:
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{video_file.filename}")
            video_path = os.path.join('static/uploads/videos', filename)
            video_file.save(video_path)
            
        if brochure_file and brochure_file.filename:
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{brochure_file.filename}")
            brochure_path = os.path.join('static/uploads/brochures', filename)
            brochure_file.save(brochure_path)
          # Extract event details
        name = data.get('name')
        category = data.get('category')
        description = data.get('description')
        start_date = data.get('start_date')
        start_time = data.get('start_time')
        end_date = data.get('end_date')
        end_time = data.get('end_time')
        venue = data.get('venue')
        
        # Get location coordinates
        location_lat = data.get('location_lat')
        location_lng = data.get('location_lng')
        
        # Convert coordinates to float if provided
        venue_lat = float(location_lat) if location_lat else None
        venue_lng = float(location_lng) if location_lng else None
        
        # Optional fields with defaults
        is_free = data.get('is_free') == 'on' or data.get('is_free') == 'true'
        price = 0 if is_free else float(data.get('price', 0))
        seats_total = int(data.get('seats_total', 50))
        tags = data.get('tags', '')
        
        print(f"Creating event: {name} by user_id {user_id}, is_free={is_free}, price={price}")
        
        venue_address = data.get('venue_address', '').strip()
        if not venue_address:
            return jsonify({'success': False, 'error': 'Venue address is required and cannot be empty.'}), 400
        
        # Create event object
        new_event = Event(
            name=name,
            start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None,
            start_time=start_time,
            end_time=end_time,
            description=description,            tag=category,  # Use category as primary tag
            category=category,
            venue=venue,
            venue_lat=venue_lat,
            venue_lng=venue_lng,
            image=image_path,
            video=video_path,
            brochure=brochure_path,
            tags=tags,
            price=price,
            is_free=is_free,
            seats_total=seats_total,
            seats_available=seats_total,
            created_by=user_id,
            organiser_id=user_id,
            custom_data=json.dumps({
                "registration_theme": data.get('registration_theme', 'minimalist'),
            }),
            venue_address=venue_address
        )
          # Add to database and commit
        db.session.add(new_event)
        db.session.commit()
        print(f"Event created successfully with ID: {new_event.id}")
        
        # --- Resource Allocation Logic ---
        # Parse resources from form (resource_type[] and resource_quantity[])
        resource_ids = data.getlist('resource_type[]') if hasattr(data, 'getlist') else data.get('resource_type', [])
        resource_quantities = data.getlist('resource_quantity[]') if hasattr(data, 'getlist') else data.get('resource_quantity', [])
        if isinstance(resource_ids, str):
            resource_ids = [resource_ids]
        if isinstance(resource_quantities, str):
            resource_quantities = [resource_quantities]
        allocated_resources = []
        from models.models import Resource, ResourceAllocation
        for idx, res_id in enumerate(resource_ids):
            if res_id == 'other' or not res_id:
                continue  # Skip custom/empty
            try:
                quantity = int(resource_quantities[idx]) if idx < len(resource_quantities) else 1
                resource = Resource.query.get(int(res_id))
                if not resource:
                    return jsonify({'success': False, 'error': f'Resource not found (ID: {res_id})'}), 400
                if resource.available_quantity < quantity:
                    return jsonify({'success': False, 'error': f'Not enough quantity for resource {resource.name}'}), 400
                # Allocate
                allocation = ResourceAllocation(
                    resource_id=resource.id,
                    event_id=new_event.id,
                    quantity=quantity,
                    status='allocated'
                )
                db.session.add(allocation)
                resource.available_quantity -= quantity
                allocated_resources.append({'name': resource.name, 'quantity': quantity})
            except Exception as alloc_e:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Error allocating resource: {str(alloc_e)}'}), 500
        db.session.commit()
        
        # Check if notifications should be sent
        notify_participants = data.get('notify_participants') == 'on' or data.get('notify_participants') == 'true'
        
        if notify_participants:
            try:
                participants = User.query.filter_by(role='participant').all()
                organizer = User.query.get(user_id)
                organizer_name = organizer.name if organizer else "Event Organizer"
                
                # Check for highlight importance
                highlight_important = data.get('highlight_important') == 'on' or data.get('highlight_important') == 'true'
                
                # Get custom notification message or use default
                custom_message = data.get('custom_notification_message')
                
                if custom_message and custom_message.strip():
                    notification_message = custom_message.strip()
                else:
                    notification_message = f"New event '{name}' created by {organizer_name}. Event will take place on {start_date} at {venue}."
                
                # If marked as important, add a prefix
                if highlight_important:
                    notification_message = f"[IMPORTANT] {notification_message}"
                
                # Add notifications for all participants
                for participant in participants:
                    # Create in-app notification with proper importance flag
                    notification = Notification(
                        message=notification_message,
                        created_by=user_id,
                        user_id=participant.id,
                        is_important=highlight_important
                    )
                    db.session.add(notification)
                    
                    # Send email notification if participant has email
                    if participant.email:
                        from utils.email_service import send_email
                        
                        # Create email subject with importance marker if needed
                        email_subject = f"{'[IMPORTANT] ' if highlight_important else ''}New Event: {name}"
                        
                        # Create HTML email with formatting
                        email_body = f"""
                        <html>
                        <head>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                                .header {{ background-color: {('#ff3e3e' if highlight_important else '#3e64ff')}; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                                .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                                .event-details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                                .button {{ display: inline-block; padding: 10px 20px; background-color: {('#ff3e3e' if highlight_important else '#3e64ff')}; color: white; 
                                          text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                                .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                                .important-badge {{ background-color: #ff3e3e; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; display: inline-block; margin-bottom: 10px; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h2>New Event Announcement</h2>
                                </div>
                                <div class="content">
                                    <p>Hello {participant.name},</p>
                                    
                                    {('<div class="important-badge">IMPORTANT</div>' if highlight_important else '')}
                                    
                                    <p>A new event has been created that might interest you!</p>
                                    
                                    <div class="event-details">
                                        <h3>{name}</h3>
                                        <p><strong>Date:</strong> {start_date}</p>
                                        <p><strong>Time:</strong> {start_time}</p>
                                        <p><strong>Venue:</strong> {venue}</p>
                                        <p><strong>Category:</strong> {category}</p>
                                        <p><strong>Organizer:</strong> {organizer_name}</p>
                                    </div>
                                      <p>{description[:150] + '...' if len(description) > 150 else description}</p>
                                    
                                    {('<p><strong>' + custom_message + '</strong></p>' if custom_message and custom_message.strip() else '')}
                                    
                                    <a href="http://localhost:5000/event/{new_event.id}" class="button">View Event Details</a>
                                    
                                    <p>We hope to see you there!</p>
                                    <p>Regards,<br>College Event Management System Team</p>
                                </div>
                                <div class="footer">
                                    <p>This email was sent to {participant.email}. If you prefer not to receive these emails, please update your notification preferences.</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        # Send the email
                        send_email(
                            participant.email,
                            email_subject,
                            email_body
                        )
                
                # Commit the notifications to the database
                db.session.commit()
                print(f"Notifications sent to {len(participants)} participants about new event {new_event.id}")
            except Exception as e:
                print(f"Error sending notifications: {str(e)}")
                # Continue even if notifications fail - the event is already created
        else:
            print("Notifications disabled for this event creation")
        
        return jsonify({
            'success': True, 
            'message': 'Event created successfully',
            'redirect': url_for('organiser.events')
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        current_app.logger.error(f"Error creating event: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@organiser_bp.route('/api/organiser/events/update/<int:event_id>', methods=['POST'])
@organiser_required
def update_organiser_event(event_id):
    try:
        user_id = session.get('user_id')
        
        # Check if event exists and belongs to this organiser
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        if event.created_by != user_id:
            return jsonify({'success': False, 'error': 'You are not authorized to edit this event'}), 403
        
        # Get form data
        data = request.form
          # Process uploaded files
        image_file = request.files.get('image')
        video_file = request.files.get('video')
        brochure_file = request.files.get('brochure')
        
        # Update event basic details
        event.name = data.get('name', event.name)
        event.description = data.get('description', event.description)
        event.category = data.get('category', event.category)
        event.tag = data.get('tag', event.tag)
        event.tags = data.get('tags', event.tags)
        
        # Update dates
        if data.get('start_date'):
            event.start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        if data.get('end_date'):
            event.end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        
        # Update times
        event.start_time = data.get('start_time', event.start_time)
        event.end_time = data.get('end_time', event.end_time)
          # Update venue and location
        event.venue = data.get('venue', event.venue)
        if data.get('location_lat') and data.get('location_lng'):
            try:
                event.venue_lat = float(data.get('location_lat'))
                event.venue_lng = float(data.get('location_lng'))
            except (ValueError, TypeError):
                # If conversion fails, don't update these fields
                pass
        
        # Update pricing
        event.is_free = data.get('is_free') == 'on'
        if not event.is_free and data.get('price'):
            event.price = float(data.get('price'))
        else:
            event.price = 0
        
        # Update seats
        if data.get('seats_total'):
            event.seats_total = int(data.get('seats_total'))
        if data.get('seats_available'):
            event.seats_available = int(data.get('seats_available'))
          # Update media files
        if image_file and image_file.filename:
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{image_file.filename}")
            image_path = os.path.join('static/uploads/images', filename)
            image_file.save(image_path)
            event.image = image_path
        if video_file and video_file.filename:
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{video_file.filename}")
            video_path = os.path.join('static/uploads/videos', filename)
            video_file.save(video_path)
        
        if brochure_file and brochure_file.filename:
            filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{brochure_file.filename}")
            brochure_path = os.path.join('static/uploads/brochures', filename)
            brochure_file.save(brochure_path)
            event.brochure = brochure_path
          # Update UI theme
        event.ui_theme = data.get('ui_theme', event.ui_theme)
        
        # Update location coordinates if provided
        if 'location_lat' in data and 'location_lng' in data:
            try:
                event.venue_lat = float(data.get('location_lat'))
                event.venue_lng = float(data.get('location_lng'))
            except (ValueError, TypeError):
                # If conversion fails, don't update these fields
                pass
        
        venue_address = data.get('venue_address', '').strip()
        if not venue_address:
            return jsonify({'success': False, 'error': 'Venue address is required and cannot be empty.'}), 400
        event.venue_address = venue_address
        
        # Update custom data
        if data.get('custom_data'):
            event.custom_data = data.get('custom_data')
        
        # Save changes
        db.session.commit()
        
        # --- Improved Resource Allocation Update Logic (handle 0/returned allocations properly) ---
        from models.models import Resource, ResourceAllocation
        # Get all previous allocations for this event (any status)
        all_prev_allocs = ResourceAllocation.query.filter_by(event_id=event.id).all()
        prev_alloc_map = {}
        for alloc in all_prev_allocs:
            # Only keep the latest allocation for each resource_id
            if alloc.resource_id not in prev_alloc_map or (alloc.allocated_at and alloc.allocated_at > prev_alloc_map[alloc.resource_id].allocated_at):
                prev_alloc_map[alloc.resource_id] = alloc
        # Parse new allocations from form
        resource_ids = data.getlist('resource_type[]') if hasattr(data, 'getlist') else data.get('resource_type', [])
        resource_quantities = data.getlist('resource_quantity[]') if hasattr(data, 'getlist') else data.get('resource_quantity', [])
        resource_others = data.getlist('resource_other[]') if hasattr(data, 'getlist') else data.get('resource_other', [])
        if isinstance(resource_ids, str):
            resource_ids = [resource_ids]
        if isinstance(resource_quantities, str):
            resource_quantities = [resource_quantities]
        if isinstance(resource_others, str):
            resource_others = [resource_others]
        # Track which resource_ids are in the new allocation
        new_resource_ids = set()
        for idx, res_id in enumerate(resource_ids):
            if not res_id or res_id == 'other':
                continue
            try:
                res_id_int = int(res_id)
                quantity = int(resource_quantities[idx]) if idx < len(resource_quantities) else 1
                resource = Resource.query.get(res_id_int)
                if not resource:
                    continue
                new_resource_ids.add(res_id_int)
                prev_alloc = prev_alloc_map.get(res_id_int)
                # Always use the previous allocation if it exists, regardless of status or quantity
                effective_available = resource.available_quantity
                if prev_alloc and prev_alloc.status == 'allocated':
                    effective_available += prev_alloc.quantity
                if quantity > effective_available:
                    continue
                if prev_alloc:
                    # Update existing allocation (even if it was returned or had quantity 0)
                    resource.available_quantity = effective_available - quantity
                    prev_alloc.quantity = quantity
                    prev_alloc.allocated_at = datetime.utcnow()
                    prev_alloc.status = 'allocated'
                    prev_alloc.returned_at = None
                else:
                    # Create new allocation
                    allocation = ResourceAllocation(
                        resource_id=resource.id,
                        event_id=new_event.id,
                        quantity=quantity,
                        status='allocated'
                    )
                    db.session.add(allocation)
                    resource.available_quantity = resource.available_quantity - quantity
            except Exception as alloc_e:
                db.session.rollback()
                print(f"Error allocating resource: {alloc_e}")
        # Mark allocations not in the new list as returned
        for res_id, alloc in prev_alloc_map.items():
            if res_id not in new_resource_ids and alloc.status == 'allocated':
                resource = Resource.query.get(res_id)
                if resource:
                    resource.available_quantity += alloc.quantity
                alloc.status = 'returned'
                alloc.returned_at = datetime.utcnow()
        db.session.commit()
        # --- Registration Theme Update ---
        reg_theme = data.get('registration_theme') or data.get('ui_theme')
        if reg_theme:
            event.ui_theme = reg_theme
            try:
                import json
                custom_data = json.loads(event.custom_data) if event.custom_data else {}
                custom_data['registration_theme'] = reg_theme
                event.custom_data = json.dumps(custom_data)
            except Exception:
                pass
        db.session.commit()
        # Return success response with redirect
        return jsonify({
            'success': True,
            'message': 'Event updated successfully',
            'redirect': f"/event/{event.id}"
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        current_app.logger.error(f"Error updating event: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@organiser_bp.route('/api/organiser/pending-deallocations', methods=['GET'])
@organiser_required
def get_pending_deallocations():
    """
    Enhanced: Only consider event finished if both end_date and end_time have passed.
    Handles missing/invalid end_time gracefully.
    """
    try:
        user_id = session.get('user_id')
        from models.models import ResourceAllocation, Resource, Event
        now = datetime.utcnow()
        auto_deallocate_cutoff = now.timestamp() - 24*3600  # 24 hours ago

        # Find events created by this organiser
        events = Event.query.filter_by(created_by=user_id).all()
        event_ids = []
        event_end_times = {}

        for e in events:
            # Only process events with end_date
            if e.end_date:
                end_dt = e.end_date
                # If end_time is present, combine with end_date
                if e.end_time:
                    try:
                        h, m = map(int, e.end_time.split(':'))
                        end_dt = end_dt.replace(hour=h, minute=m, second=0, microsecond=0)
                    except Exception as time_error:
                        # If time parsing fails, treat as end of day
                        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)
                else:
                    # No end_time: treat as end of day
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)
                # Only consider events that have ended (date+time)
                if end_dt < now:
                    event_ids.append(e.id)
                    event_end_times[e.id] = end_dt

        # Find allocations for these events that are still allocated
        allocations = ResourceAllocation.query.filter(ResourceAllocation.event_id.in_(event_ids), 
                                                     ResourceAllocation.status == 'allocated').all()
        result = []
        auto_deallocated = []

        for alloc in allocations:
            try:
                resource = Resource.query.get(alloc.resource_id)
                event = Event.query.get(alloc.event_id)
                end_dt = event_end_times.get(alloc.event_id)
                # If allocation is overdue (>24h after event end), auto-deallocate
                if end_dt and (now - end_dt).total_seconds() > 24*3600:
                    alloc.status = 'returned'
                    alloc.returned_at = now
                    if resource:
                        resource.available_quantity += alloc.quantity
                    auto_deallocated.append({
                        'id': alloc.id,
                        'resource_name': resource.name if resource else 'Unknown',
                        'event_name': event.name if event else 'Unknown'
                    })
                else:
                    # Add to pending deallocation list
                    result.append({
                        'allocation_id': alloc.id,
                        'resource_name': resource.name if resource else 'Unknown',
                        'event_name': event.name if event else 'Unknown',
                        'quantity': alloc.quantity,
                        'end_time': end_dt.strftime("%Y-%m-%d %H:%M") if end_dt else 'Unknown'
                    })
            except Exception as alloc_error:
                print(f"Error processing allocation {alloc.id}: {str(alloc_error)}")
                continue

        if auto_deallocated:
            db.session.commit()

        return jsonify({
            'success': True, 
            'allocations': result, 
            'auto_deallocated': auto_deallocated
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in get_pending_deallocations: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@organiser_bp.route('/organiser/payments')
def organiser_payments():
    """Landing page for organiser payments: shows options for transactions, verification, etc."""
    return render_template('organiser_payments.html')
