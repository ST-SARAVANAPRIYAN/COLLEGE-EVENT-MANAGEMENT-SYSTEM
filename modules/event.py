from flask import Blueprint, request, jsonify, send_from_directory, session, render_template, flash, redirect, url_for
from models.models import db, Event, Registration, User, Notification
from utils.email_service import send_email, notify_participants_about_exploration
import os
import shutil
import zipfile
import uuid
from werkzeug.utils import secure_filename
import json
from datetime import datetime, timedelta

event_bp = Blueprint('event', 'event')

# Directory for event exploration pages - keeping this for backward compatibility but not creating new directories
EVENT_EXPLORATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'event_explorations')

# Remove the directory creation code to prevent new directories from being created
# If you want to completely remove the directory, uncomment and use the following code:
# if os.path.exists(EVENT_EXPLORATIONS_DIR):
#     shutil.rmtree(EVENT_EXPLORATIONS_DIR)

NEW_THEMES = ['creative', 'elegant', 'minimalist', 'retro', 'tech']

@event_bp.route('/api/events')
def api_events():
    try:
        # Filter for parent events only if specified
        parent_only = request.args.get('parent_only', 'false').lower() == 'true'
        if (parent_only):
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

@event_bp.route('/register-event/<int:event_id>/guest', methods=['POST'])
def register_event_guest(event_id):
    try:
        # Check if event exists
        event = Event.query.get_or_404(event_id)
        
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if not name or not email or not phone:
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('events_list'))
        
        # Check if seats available
        if event.seats_available <= 0:
            flash('Sorry, no seats available', 'danger')
            return redirect(url_for('events_list'))
            
        # Check registration deadline
        if event.registration_end_date and event.registration_end_date < datetime.now():
            flash('Registration deadline has passed', 'danger')
            return redirect(url_for('events_list'))
            
        # Check if user already exists in the system
        existing_user = User.query.filter_by(email=email).first()
        
        # If user exists, use their account
        if existing_user:
            user_id = existing_user.id
            
            # Check if already registered
            existing_reg = Registration.query.filter_by(
                event_id=event_id,
                user_id=user_id
            ).first()
            
            if existing_reg:
                flash('You are already registered for this event', 'info')
                return redirect(url_for('events_list'))
        else:
            # Create a temporary user with participant role
            # Generate a random password that they can reset later if they want to login
            import random
            import string
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            
            # Hash the password
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(temp_password)
            
            new_user = User(
                name=name,
                email=email,
                contact_number=phone,
                password=hashed_password,
                role='participant'
            )
            
            db.session.add(new_user)
            db.session.commit()
            user_id = new_user.id
        
        # Create registration
        new_reg = Registration(
            event_id=event_id,
            user_id=user_id
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
        
        # Send confirmation email
        user = User.query.get(user_id)
        send_email(
            email,
            f"Registration Confirmation: {event.name}",
            f"""Hi {name},

Thank you for registering for {event.name} on {event.date}.

Event Details:
- Date: {event.date}
- Time: {event.start_time or 'TBA'}
- Venue: {event.venue or 'TBA'}

{'Payment will be collected at the venue.' if not event.is_free else ''}

If this is your first time using our system, we've created an account for you that you can use to track your registrations.
Email: {email}
{'If you wish to access your account, you can use the password reset feature on the login page.' if not existing_user else ''}

Regards,
CEMS Team"""
        )
        
        flash('Registration successful! Check your email for confirmation', 'success')
        return redirect(url_for('events_list'))
        
    except Exception as e:
        flash(f'Error registering for event: {str(e)}', 'danger')
        return redirect(url_for('events_list'))

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
        
        # Venue information - updated structure
        venue_name = data.get('venue_name')
        venue_address = data.get('venue_address')
        venue_lat = data.get('venue_lat')
        venue_lng = data.get('venue_lng')
        
        # Create structured venue data
        venue_data = {
            "name": venue_name,
            "address": venue_address,
            "coordinates": {
                "lat": venue_lat,
                "lng": venue_lng
            }
        }
        
        # Combine venue name and address for legacy support
        venue = f"{venue_name}, {venue_address}" if venue_name and venue_address else data.get('venue')
        
        # Seating
        seats_total = int(data.get('seats_total', 50))
        
        # Registration theme
        registration_theme = data.get('registration_theme', 'minimalistic-elegant')
        
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
        
        # Process resource requirements
        resources_required = {
            "projectors": int(data.get('req_projectors', 0)),
            "sound": int(data.get('req_sound', 0)),
            "chairs": int(data.get('req_chairs', 0)),
            "tables": int(data.get('req_tables', 0)),
            "lights": int(data.get('req_lights', 0)),
            "volunteers": int(data.get('req_volunteers', 0))
        }
                
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
                "resources_required": resources_required,
                "venue_data": venue_data
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
            
        # Process sub-events if any
        sub_events_data = {}
        for key in data.keys():
            if key.startswith('sub_events['):
                # Extract sub event index and field name from key format: sub_events[0][name]
                parts = key.replace('sub_events[', '').replace(']', '').split('[')
                if len(parts) == 2:
                    idx, field = parts
                    if idx not in sub_events_data:
                        sub_events_data[idx] = {}
                    sub_events_data[idx][field] = data.get(key)
        
        # Add to events list
        db.session.add(new_event)
        db.session.commit()
        
        # Create sub-events after main event is created
        for idx, sub_event_data in sub_events_data.items():
            # Create sub-event with same venue information as parent
            sub_event = Event(
                name=sub_event_data.get('name'),
                description=sub_event_data.get('description', ''),
                date=date,  # Use parent date as fallback
                start_date=datetime.strptime(sub_event_data.get('start_date', start_date), '%Y-%m-%d'),
                end_date=datetime.strptime(sub_event_data.get('end_date', end_date), '%Y-%m-%d'),
                start_time=sub_event_data.get('start_time', start_time),
                end_time=sub_event_data.get('end_time', end_time),
                category=sub_event_data.get('category', category),
                tag=sub_event_data.get('category', category),  # Default tag to category
                venue=venue,  # Use parent venue
                price=float(sub_event_data.get('price', 0)) if sub_event_data.get('is_free') != 'on' else 0,
                is_free=sub_event_data.get('is_free') == 'on',
                seats_total=int(sub_event_data.get('seats_total', 50)),
                seats_available=int(sub_event_data.get('seats_total', 50)),
                registration_end_date=datetime.strptime(registration_end_date, '%Y-%m-%d') if registration_end_date else None,
                parent_event_id=new_event.id,
                created_by=session.get('user_id'),
                organiser_id=session.get('user_id'),
                custom_data=json.dumps({
                    "registration_theme": registration_theme,
                    "resources_required": {},  # Sub-events share resources with parent
                    "venue_data": venue_data  # Same venue data as parent
                })
            )
            
            db.session.add(sub_event)
        
        # Commit all sub-events
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

def get_upload_path(folder):
    return os.path.join('static/uploads', folder)

# Removing the duplicate '/events' route that conflicts with app.py

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
        registration_theme = 'minimalist'  # Default theme
        
        if event.custom_data:
            try:
                custom_data = json.loads(event.custom_data)
                registration_theme = custom_data.get('registration_theme', 'minimalist')
            except:
                pass
                
        # Make sure the theme exists in our available themes list
        if registration_theme not in NEW_THEMES:
            registration_theme = 'minimalist'  # Fallback to default
            
        # Check if user is already registered
        is_registered = False
        if session.get('user_id'):
            reg = Registration.query.filter_by(
                event_id=event_id,
                user_id=session['user_id']
            ).first()
            is_registered = reg is not None
            
        # Add current datetime for comparison with registration_end_date
        now = datetime.now()
            
        return render_template(
            'event_detail.html', 
            event=event, 
            parent_event=parent_event,
            sub_events=sub_events,
            is_registered=is_registered,
            registration_theme=registration_theme,
            now=now,
            custom_data=custom_data,
            theme_assets_path='/static/theme_assets/'  # Add the correct path to theme assets
        )
    except Exception as e:
        flash(f'Error loading event details: {str(e)}', 'danger')
        return redirect(url_for('events_list'))

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

@event_bp.route('/preview_registration_theme/<theme>')
def preview_registration_theme(theme):
    """
    Preview a registration theme with sample data
    """
    try:
        if theme not in NEW_THEMES:
            return f"Theme '{theme}' is not available.", 404

        # Get event data from query parameters or use sample data
        event_name = request.args.get('event_name', 'Sample Event')
        event_description = request.args.get('event_description', 'This is a preview of how the registration form will look with this theme.')
        is_preview = request.args.get('is_preview', 'false').lower() == 'true'

        # Sample event data for preview
        event_data = {
            'name': event_name,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'start_time': '10:00 AM',
            'venue': 'Sample Venue, Location',
            'description': event_description,
            'organiser': 'Event Organiser',
            'price': 500,
            'is_free': False
        }

        # Create a context with additional theme-related variables
        context = {
            'event': event_data,
            'is_preview': is_preview,
            'theme_name': theme,
            'theme_assets_path': '/static/theme_assets/',  # Fixed path - removed incorrect space
            'static_url': '/static'
        }

        # Load the requested theme template
        theme_template = f'registration_themes/{theme}.html'

        # Render the theme with sample data and additional context
        return render_template(theme_template, **context)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading theme: {str(e)}", 500

@event_bp.route('/api/registration/<int:event_id>/preview/<theme>', methods=['GET'])
def api_preview_registration_theme(event_id, theme):
    try:
        if theme not in NEW_THEMES:
            return jsonify({'error': f"Theme '{theme}' is not available."}), 404

        event = Event.query.get_or_404(event_id)

        # Pass the theme name and the event to the template - fixed path
        return render_template(f'registration_themes/{theme}.html', 
            event=event,
            theme_assets_path='/static/theme_assets/')  # Fixed path - removed incorrect space
    except Exception as e:
        return jsonify({'error': str(e)}), 500