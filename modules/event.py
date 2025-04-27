from flask import Blueprint, request, jsonify, send_from_directory, session, render_template, flash, redirect
from models.models import db, Event, Registration, User, Notification
from utils.email_service import send_email, notify_participants_about_exploration
import os
import shutil
import zipfile
import uuid
from werkzeug.utils import secure_filename
import json
from datetime import datetime

event_bp = Blueprint('event', __name__)

# Directory for event exploration pages
EVENT_EXPLORATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'event_explorations')
if not os.path.exists(EVENT_EXPLORATIONS_DIR):
    os.makedirs(EVENT_EXPLORATIONS_DIR)

@event_bp.route('/api/events')
def api_events():
    try:
        # Filter for parent events only if specified
        parent_only = request.args.get('parent_only', 'false').lower() == 'true'
        if parent_only:
            result = [e.to_dict() for e in Event.query.filter_by(parent_event_id=None).all()]
        else:
            result = [e.to_dict() for e in Event.query.all()]
            
        # Filter by tag if specified
        tag = request.args.get('tag')
        if tag:
            result = [e for e in result if e['tag'] == tag]
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/api/events/<int:event_id>')
def api_event_detail(event_id):
    try:
        event = Event.query.get(event_id)
        if event:
            event_data = event.to_dict()
            # Get sub-events details if needed
            include_sub_events = request.args.get('include_sub_events', 'false').lower() == 'true'
            if include_sub_events and event.sub_events:
                event_data['sub_events_data'] = [se.to_dict() for se in event.sub_events]
            return jsonify(event_data)
        return jsonify({'error': 'Event not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/api/events/<int:event_id>/register', methods=['POST'])
def register_for_event(event_id):
    try:
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = session.get('user_id')
        event = Event.query.get(event_id)
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if already registered
        if Registration.query.filter_by(event_id=event_id, user_id=user_id).first():
            return jsonify({'error': 'Already registered for this event'}), 400
        
        # Create a new registration
        new_registration = Registration(
            event_id=event_id,
            user_id=user_id,
            payment_status="pending" if event.fee > 0 else "completed"
        )
        
        # If there's a fee, generate payment
        if event.fee > 0:
            # This is where you'd integrate with Razorpay API in production
            payment_data = {
                "receipt": f"reg_{new_registration.id}",
                "amount": event.fee * 100,  # Razorpay expects amount in paise
                "currency": "INR",
                "payment_capture": 1
            }
            
            # In a real implementation, you'd call Razorpay API here
            # For demo, simulate a payment ID
            payment_id = f"pay_{uuid.uuid4().hex[:8]}"
            new_registration.payment_id = payment_id
            
            # Save registration
            db.session.add(new_registration)
            db.session.commit()
            
            # Return payment details
            return jsonify({
                "success": True,
                "requires_payment": True,
                "payment_details": {
                    "key_id": "rzp_test_12345678",  # Replace with config value in production
                    "amount": event.fee * 100,
                    "currency": "INR",
                    "name": "College Event Management System",
                    "description": f"Registration for {event.name}",
                    "order_id": f"order_{uuid.uuid4().hex[:8]}",  # In production, get from Razorpay
                    "prefill": {
                        "name": session.get('user_name'),
                        "email": session.get('user_email')
                    }
                }
            })
        else:
            # Free event, no payment needed
            db.session.add(new_registration)
            db.session.commit()
            
            # Send confirmation email
            user = User.query.get(user_id)
            if user:
                send_email(
                    user.email,
                    f"Registration Confirmation: {event.name}",
                    f"Hi {user.name},\n\nYour registration for {event.name} on {event.date} has been confirmed.\n\nRegards,\nCEMS Team"
                )
            
            return jsonify({
                "success": True,
                "requires_payment": False,
                "message": "Registration successful"
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/api/events/create', methods=['POST'])
def create_event():
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        data = request.form
        
        # Required fields
        name = data.get('name')
        description = data.get('description')
        category = data.get('category')
        
        # Handle dates and times
        start_date = data.get('start_date')
        start_time = data.get('start_time', '00:00')
        end_date = data.get('end_date')
        end_time = data.get('end_time', '23:59')
        
        # Legacy date support for backwards compatibility
        date = data.get('date', start_date)
        
        # Handle price/fee
        price = 0
        is_free = data.get('is_free') == 'on'
        if not is_free and data.get('price'):
            try:
                price = float(data.get('price', 0))
            except ValueError:
                price = 0
        
        # Handle tags (comma-separated)
        tags = data.get('tags', '')
        tag = data.get('tag', category)  # For backwards compatibility
        
        # Registration deadline 
        registration_end_date = data.get('registration_end_date')
        
        # Venue and seating
        venue = data.get('venue')
        seats_total = int(data.get('seats_total', 50))
        
        # Registration theme
        registration_theme = data.get('registration_theme', 'minimalistic')
        
        # Optional parent event
        parent_id = data.get('parent_event_id')
        if parent_id and parent_id != '':
            parent_id = int(parent_id)
            # Check if parent exists
            parent = Event.query.get(parent_id)
            if not parent:
                return jsonify({'error': 'Parent event not found'}), 404
        else:
            parent_id = None
                
        # Create new event
        new_event = Event(
            name=name,
            date=date,
            start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None,
            start_time=start_time,
            end_time=end_time,
            description=description,
            tag=tag,
            category=category,
            venue=venue,
            tags=tags,
            price=price,
            is_free=is_free,
            seats_total=seats_total,
            seats_available=seats_total,
            registration_end_date=datetime.strptime(registration_end_date, '%Y-%m-%d') if registration_end_date else None,
            is_featured=data.get('is_featured') == 'on',
            parent_event_id=parent_id,
            created_by=session.get('user_id'),
            organiser_id=session.get('user_id'),
            custom_data=json.dumps({
                "registration_theme": registration_theme,
                "resources_required": {
                    "projectors": int(data.get('req_projectors', 0)),
                    "sound": int(data.get('req_sound', 0)),
                    "volunteers": int(data.get('req_volunteers', 0))
                }
            })
        )
        
        # Handle image upload
        if 'image' in request.files and request.files['image'].filename:
            # Save the image file
            image_file = request.files['image']
            filename = secure_filename(image_file.filename)
            file_path = os.path.join('static/uploads/images', filename)
            image_file.save(file_path)
            new_event.image = file_path
        
        # Handle cover image upload
        if 'cover_image' in request.files and request.files['cover_image'].filename:
            cover_file = request.files['cover_image']
            filename = secure_filename(cover_file.filename)
            file_path = os.path.join('static/uploads/images', filename)
            cover_file.save(file_path)
            new_event.cover_image = file_path
            
        # Handle other uploads (video, brochure)
        if 'video' in request.files and request.files['video'].filename:
            video_file = request.files['video']
            filename = secure_filename(video_file.filename)
            file_path = os.path.join('static/uploads/videos', filename)
            video_file.save(file_path)
            new_event.video = file_path
            
        if 'brochure' in request.files and request.files['brochure'].filename:
            brochure_file = request.files['brochure']
            filename = secure_filename(brochure_file.filename)
            file_path = os.path.join('static/uploads/brochures', filename)
            brochure_file.save(file_path)
            new_event.brochure = file_path
        
        # Add to events list
        db.session.add(new_event)
        db.session.commit()
        
        # If this is a sub-event, update parent
        if parent_id:
            parent = Event.query.get(parent_id)
            if parent:
                parent.sub_events.append(new_event)
                db.session.commit()
                
        # Notify users about new event
        for user in User.query.filter_by(role='participant').all():
            send_email(
                user.email,
                f"New Event: {new_event.name}",
                f"Hi {user.name},\n\nWe're excited to announce a new event: {new_event.name} on {start_date} at {start_time}.\n\nDescription: {new_event.description}\n\nRegister now on the CEMS portal!\n\nRegards,\nCEMS Team"
            )
        
        return jsonify({'success': True, 'event_id': new_event.id})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@event_bp.route('/api/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        data = request.form
        
        # Update fields
        if 'name' in data:
            event.name = data.get('name')
        if 'date' in data:
            event.date = data.get('date')
        if 'description' in data:
            event.description = data.get('description')
        if 'tag' in data:
            event.tag = data.get('tag')
        if 'fee' in data:
            event.fee = float(data.get('fee', 0))
            
        # Handle file updates
        if 'image' in request.files and request.files['image'].filename:
            image_file = request.files['image']
            filename = secure_filename(image_file.filename)
            file_path = os.path.join('static/uploads/images', filename)
            image_file.save(file_path)
            event.image = file_path
            
        if 'video' in request.files and request.files['video'].filename:
            video_file = request.files['video']
            filename = secure_filename(video_file.filename)
            file_path = os.path.join('static/uploads/videos', filename)
            video_file.save(file_path)
            event.video = file_path
            
        if 'brochure' in request.files and request.files['brochure'].filename:
            brochure_file = request.files['brochure']
            filename = secure_filename(brochure_file.filename)
            file_path = os.path.join('static/uploads/brochures', filename)
            brochure_file.save(file_path)
            event.brochure = file_path
            
        db.session.commit()
        
        # Notify registered participants about the update
        registered_users = [r.user_id for r in Registration.query.filter_by(event_id=event_id).all()]
        for user_id in registered_users:
            user = User.query.get(user_id)
            if user:
                send_email(
                    user.email,
                    f"Event Update: {event.name}",
                    f"Hi {user.name},\n\nThere have been updates to an event you're registered for: {event.name} on {event.date}.\n\nPlease check the CEMS portal for details.\n\nRegards,\nCEMS Team"
                )
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        if session.get('user_role') != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
            
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        # Check if there are registrations
        if Registration.query.filter_by(event_id=event_id).first():
            return jsonify({'error': 'Cannot delete an event with registrations'}), 400
            
        # Remove event
        db.session.delete(event)
        
        # Clean up sub-events
        for sub_event in event.sub_events:
            db.session.delete(sub_event)
                
        # Clean up exploration if exists
        event_dir = os.path.join(EVENT_EXPLORATIONS_DIR, str(event_id))
        if os.path.exists(event_dir):
            shutil.rmtree(event_dir)
        
        db.session.commit()
            
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/upload_event_exploration', methods=['POST'])
def upload_event_exploration():
    try:
        if session.get('user_role') not in ['organiser', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        event_id = request.form.get('event_id')
        if not event_id:
            return jsonify({'error': 'Event ID is required'}), 400
        
        # Check if event exists
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Create event directory if it doesn't exist
        event_dir = os.path.join(EVENT_EXPLORATIONS_DIR, event_id)
        if not os.path.exists(event_dir):
            os.makedirs(event_dir)
        else:
            # Clear existing files
            for file in os.listdir(event_dir):
                file_path = os.path.join(event_dir, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        
        # Handle file upload
        if 'exploration_files' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['exploration_files']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Save and extract zip file
        if file and file.filename.endswith('.zip'):
            zip_path = os.path.join(event_dir, secure_filename(file.filename))
            file.save(zip_path)
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(event_dir)
            
            # Remove the zip after extraction
            os.remove(zip_path)
            
            # Update event data
            event.has_exploration = True
            db.session.commit()
            
            # Notify participants about the new exploration experience
            notify_participants_about_exploration(event, db, User, Registration, Notification)
            
            return jsonify({'success': True, 'message': 'Exploration files uploaded successfully'})
        else:
            return jsonify({'error': 'File must be a ZIP archive'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/event_exploration/<int:event_id>')
def event_exploration(event_id):
    try:
        event_dir = os.path.join(EVENT_EXPLORATIONS_DIR, str(event_id))
        
        # Check if event exploration exists
        if not os.path.exists(event_dir):
            return "Event exploration not found", 404
        
        # Look for index.html in the event directory
        index_path = os.path.join(event_dir, 'index.html')
        if os.path.exists(index_path):
            # Serve the custom event exploration page
            return send_from_directory(event_dir, 'index.html')
        else:
            return "Event exploration index file not found", 404
        
    except Exception as e:
        return f"Error accessing event exploration: {e}", 500

@event_bp.route('/event_explorations/<int:event_id>/<path:filename>')
def event_explorations_files(event_id, filename):
    """Serve static files from event exploration directories"""
    try:
        event_dir = os.path.join(EVENT_EXPLORATIONS_DIR, str(event_id))
        return send_from_directory(event_dir, filename)
    except Exception as e:
        return f"Error serving event exploration file: {e}", 500

def get_upload_path(folder):
    return os.path.join('static/uploads', folder)

@event_bp.route('/events')
def events():
    try:
        # Get featured events
        featured_events = Event.query.filter_by(is_featured=True).all()
        
        # Get all other events with no parent
        other_events = Event.query.filter_by(parent_event_id=None, is_featured=False).all()
        
        return render_template('events.html', featured_events=featured_events, other_events=other_events)
    except Exception as e:
        flash(f'Error loading events: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@event_bp.route('/event/<int:event_id>')
def event_detail(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        
        # Check if this is part of a larger event
        parent_event = None
        if event.parent_event_id:
            parent_event = Event.query.get(event.parent_event_id)
            
        # Get sub-events if any
        sub_events = Event.query.filter_by(parent_event_id=event_id).all()
        
        # Get the custom UI theme for registration
        custom_data = {}
        if event.custom_data:
            try:
                custom_data = json.loads(event.custom_data)
            except:
                custom_data = {}
                
        registration_theme = custom_data.get('registration_theme', 'minimalistic')
        
        # Check if user is already registered
        is_registered = False
        if session.get('user_id'):
            reg = Registration.query.filter_by(
                event_id=event_id,
                user_id=session['user_id']
            ).first()
            is_registered = reg is not None
            
        return render_template(
            'event_detail.html', 
            event=event, 
            parent_event=parent_event,
            sub_events=sub_events,
            is_registered=is_registered,
            registration_theme=registration_theme
        )
    except Exception as e:
        flash(f'Error loading event details: {str(e)}', 'danger')
        return redirect(url_for('event.events'))

@event_bp.route('/create-event', methods=['GET', 'POST'])
def create_event_page():
    if not session.get('user_id'):
        flash('Please login to create an event', 'warning')
        return redirect(url_for('auth.login'))
        
    if session.get('user_role') not in ['admin', 'organiser']:
        flash('You do not have permission to create events', 'danger')
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            title = request.form.get('title')
            date = request.form.get('date')
            start_date = request.form.get('start_date')
            start_time = request.form.get('start_time')
            end_date = request.form.get('end_date')
            end_time = request.form.get('end_time')
            tag = request.form.get('tag')
            category = request.form.get('category')
            description = request.form.get('description')
            venue = request.form.get('venue')
            registration_end_date = request.form.get('registration_end_date')
            
            # Process pricing
            price = request.form.get('price', 0)
            is_free = True if request.form.get('is_free') == 'on' else False
            
            if is_free:
                price = 0
                
            # Process tags (multiple, comma-separated)
            tags = request.form.get('tags', '')
            
            # Handle resources required
            resources_required = {}
            for key in request.form:
                if key.startswith('resource_'):
                    resource_id = key.replace('resource_', '')
                    quantity = request.form.get(key)
                    if quantity and int(quantity) > 0:
                        resources_required[resource_id] = int(quantity)
            
            # Process registration theme
            registration_theme = request.form.get('registration_theme', 'minimalistic')
            
            # Create custom data object
            custom_data = {
                'registration_theme': registration_theme,
                'resources_required': resources_required
            }
            
            # Create new event
            new_event = Event(
                name=name,
                title=title,
                date=date,
                start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
                end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None,
                start_time=start_time,
                end_time=end_time,
                tag=tag,
                tags=tags,
                category=category,
                description=description,
                venue=venue,
                seats_total=request.form.get('seats_total', 0),
                seats_available=request.form.get('seats_total', 0),
                price=price,
                is_free=is_free,
                registration_end_date=datetime.strptime(registration_end_date, '%Y-%m-%d') if registration_end_date else None,
                created_by=session.get('user_id'),
                organiser_id=session.get('user_id'),
                custom_data=json.dumps(custom_data)
            )
            
            # Handle image upload
            if 'image' in request.files and request.files['image'].filename:
                image = request.files['image']
                if image:
                    filename = secure_filename(image.filename)
                    os.makedirs(get_upload_path('images'), exist_ok=True)
                    image_path = os.path.join(get_upload_path('images'), filename)
                    image.save(image_path)
                    new_event.image = f'uploads/images/{filename}'
                    
            # Handle cover image upload 
            if 'cover_image' in request.files and request.files['cover_image'].filename:
                cover_image = request.files['cover_image']
                if cover_image:
                    filename = secure_filename(cover_image.filename)
                    os.makedirs(get_upload_path('images'), exist_ok=True)
                    cover_image_path = os.path.join(get_upload_path('images'), filename)
                    cover_image.save(cover_image_path)
                    new_event.cover_image = f'uploads/images/{filename}'
                    
            # Handle video upload
            if 'video' in request.files and request.files['video'].filename:
                video = request.files['video']
                if video:
                    filename = secure_filename(video.filename)
                    os.makedirs(get_upload_path('videos'), exist_ok=True)
                    video_path = os.path.join(get_upload_path('videos'), filename)
                    video.save(video_path)
                    new_event.video = f'uploads/videos/{filename}'
                    
            # Handle brochure upload
            if 'brochure' in request.files and request.files['brochure'].filename:
                brochure = request.files['brochure']
                if brochure:
                    filename = secure_filename(brochure.filename)
                    os.makedirs(get_upload_path('brochures'), exist_ok=True)
                    brochure_path = os.path.join(get_upload_path('brochures'), filename)
                    brochure.save(brochure_path)
                    new_event.brochure = f'uploads/brochures/{filename}'
            
            db.session.add(new_event)
            db.session.commit()
            
            flash('Event created successfully', 'success')
            return redirect(url_for('event.event_detail', event_id=new_event.id))
            
        except Exception as e:
            flash(f'Error creating event: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()
            return redirect(url_for('event.create_event'))
            
    # GET request
    return render_template('create_event.html')

@event_bp.route('/register-event/<int:event_id>', methods=['POST'])
def register_event(event_id):
    if not session.get('user_id'):
        flash('Please login to register for an event', 'warning')
        return redirect(url_for('auth.login'))
        
    try:
        # Check if event exists
        event = Event.query.get_or_404(event_id)
        
        # Check if already registered
        existing_reg = Registration.query.filter_by(
            event_id=event_id,
            user_id=session['user_id']
        ).first()
        
        if existing_reg:
            flash('You are already registered for this event', 'info')
            return redirect(url_for('event.event_detail', event_id=event_id))
            
        # Check if seats available
        if event.seats_available <= 0:
            flash('Sorry, no seats available', 'danger')
            return redirect(url_for('event.event_detail', event_id=event_id))
            
        # Check registration deadline
        if event.registration_end_date and event.registration_end_date < datetime.now():
            flash('Registration deadline has passed', 'danger')
            return redirect(url_for('event.event_detail', event_id=event_id))
            
        # Create registration
        new_reg = Registration(
            event_id=event_id,
            user_id=session['user_id']
        )
        
        # Handle payment for paid events
        if not event.is_free and event.price > 0:
            # Placeholder for payment integration
            new_reg.payment_status = 'pending'
        else:
            new_reg.payment_status = 'completed'
            
        # Update available seats
        event.seats_available -= 1
        
        db.session.add(new_reg)
        db.session.commit()
        
        flash('Registration successful', 'success')
        return redirect(url_for('event.event_detail', event_id=event_id))
        
    except Exception as e:
        flash(f'Error registering for event: {str(e)}', 'danger')
        return redirect(url_for('event.event_detail', event_id=event_id))

@event_bp.route('/api/tags')
def get_tags():
    # Get all unique tags from the database
    events = Event.query.all()
    all_tags = []
    
    for event in events:
        if event.tag:
            all_tags.append(event.tag)
        if event.tags:
            event_tags = [t.strip() for t in event.tags.split(',')]
            all_tags.extend(event_tags)
    
    # Remove duplicates and sort
    unique_tags = sorted(list(set(all_tags)))
    return jsonify(unique_tags)

@event_bp.route('/api/events')
def get_events():
    try:
        tag = request.args.get('tag')
        category = request.args.get('category')
        
        query = Event.query
        
        if tag:
            # Search in both tag field and tags field
            query = query.filter((Event.tag == tag) | 
                                 (Event.tags.like(f'%{tag}%')))
        
        if category:
            query = query.filter_by(category=category)
            
        events = query.all()
        return jsonify([event.to_dict() for event in events])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500