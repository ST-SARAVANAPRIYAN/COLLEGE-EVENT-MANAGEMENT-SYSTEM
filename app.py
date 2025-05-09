from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect
import os
import pymysql
from datetime import datetime, timedelta
import json 

from models.models import db, User, Event, Registration
from modules.auth import auth_bp
from modules.event import event_bp
from modules.admin import admin_bp
from modules.organiser import organiser_bp
from modules.participant import participant_bp
from modules.payment import payment_bp
from modules.api_organiser import api_organiser_bp

# Create Flask application
app = Flask(__name__)
app.secret_key = 'cems_secret_key_for_development'

# Configure MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/cems_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CSRF protection disabled as per requirement
# csrf = CSRFProtect(app)

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add custom Jinja filters
@app.template_filter('fromjson')
def from_json(value):
    if value is None:
        return {}
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return value

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(event_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(organiser_bp)
app.register_blueprint(participant_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(api_organiser_bp)

# Create upload directories if they don't exist
for dir_path in ['static/uploads/images', 'static/uploads/videos', 'static/uploads/brochures']:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

@app.route('/')
def home():
    try:
        # Get featured events for the homepage
        featured_events = Event.query.filter_by(is_featured=True).order_by(Event.start_date.desc()).limit(6).all()
        
        # If no featured events, get the most recent ones
        if not featured_events:
            featured_events = Event.query.order_by(Event.start_date.desc()).limit(6).all()
        
        return render_template('index.html', featured_events=featured_events)
    except Exception as e:
        return f"Error loading home page: {e}", 500

@app.route('/events')
def events_list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 9  # Number of events per page
        
        # Get filter parameters
        category = request.args.get('category', '')
        date_filter = request.args.get('date', '')
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        # Start with base query
        query = Event.query
        
        # Apply filters
        if category:
            query = query.filter_by(category=category)
        
        if date_filter:
            today = datetime.now().date()
            if date_filter == 'today':
                query = query.filter(db.func.date(Event.start_date) == today)
            elif date_filter == 'tomorrow':
                tomorrow = today + timedelta(days=1)
                query = query.filter(db.func.date(Event.start_date) == tomorrow)
            elif date_filter == 'week':
                week_end = today + timedelta(days=7)
                query = query.filter(db.func.date(Event.start_date) >= today, db.func.date(Event.start_date) <= week_end)
            elif date_filter == 'month':
                month_end = today + timedelta(days=30)
                query = query.filter(db.func.date(Event.start_date) >= today, db.func.date(Event.start_date) <= month_end)
        
        if status:
            today = datetime.now().date()
            if status == 'open':
                query = query.filter(
                    ((Event.registration_end_date.is_(None)) | 
                     (db.func.date(Event.registration_end_date) >= today)),
                    Event.seats_available > 0
                )
            elif status == 'closed':
                query = query.filter(
                    db.or_(
                        db.and_(Event.registration_end_date.isnot(None), db.func.date(Event.registration_end_date) < today),
                        Event.seats_available <= 0
                    )
                )
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(db.or_(
                Event.name.like(search_term),
                Event.description.like(search_term),
                Event.venue.like(search_term)
            ))
        
        # Order by start date
        query = query.order_by(Event.start_date.asc())
        
        # Paginate results
        events_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        events = events_pagination.items
        
        # Create pagination data for template
        pagination = {
            'page': page,
            'pages': events_pagination.pages,
            'total': events_pagination.total,
            'prev_url': url_for('events_list', page=page-1, category=category, date=date_filter, 
                               status=status, search=search) if events_pagination.has_prev else None,
            'next_url': url_for('events_list', page=page+1, category=category, date=date_filter, 
                               status=status, search=search) if events_pagination.has_next else None,
            'iter_pages': events_pagination.iter_pages,
            'get_url': lambda p: url_for('events_list', page=p, category=category, date=date_filter, 
                                        status=status, search=search)
        }
        
        current_date = datetime.now().date()
        
        return render_template('events.html', events=events, pagination=pagination, 
                              current_date=current_date)
    except Exception as e:
        return f"Error loading events page: {e}", 500

@app.route('/events/<int:event_id>/register')
@login_required
def register_event(event_id):
    if current_user.role != 'participant':
        flash('Only participants can register for events', 'error')
        return redirect(url_for('event.event_detail', event_id=event_id))
    
    try:
        # Get the event
        event = Event.query.get_or_404(event_id)
        
        # Check if registration is open
        current_date = datetime.now().date()
        if event.registration_end_date and event.registration_end_date < current_date:
            flash('Registration for this event has closed', 'error')
            return redirect(url_for('event.event_detail', event_id=event_id))
        
        # Check if seats are available
        if event.seats_available <= 0:
            flash('This event is sold out', 'error')
            return redirect(url_for('event.event_detail', event_id=event_id))
        
        # Check if already registered
        existing_registration = Registration.query.filter_by(
            event_id=event_id,
            user_id=current_user.id
        ).first()
        
        if existing_registration:
            flash('You are already registered for this event', 'info')
            return redirect(url_for('participant.dashboard'))
        
        # Create new registration
        new_registration = Registration(
            event_id=event_id,
            user_id=current_user.id,
            payment_status='pending' if event.price > 0 else 'completed'
        )
        
        # Update available seats
        event.seats_available -= 1
        
        db.session.add(new_registration)
        db.session.commit()
        
        # Redirect to payment page if event has a fee
        if event.price > 0:
            return redirect(url_for('payment.process', registration_id=new_registration.id))
        
        # Send confirmation email
        from utils.email_service import send_registration_confirmation
        send_registration_confirmation(current_user, event, 'completed')
        
        flash('Successfully registered for the event!', 'success')
        return redirect(url_for('participant.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during registration: {str(e)}', 'error')
        return redirect(url_for('event.event_detail', event_id=event_id))

@app.route('/preview_registration_theme/<theme>')
def preview_registration_theme(theme):
    """
    Direct route for theme previews that doesn't rely on the event blueprint
    """
    try:
        # List of available themes
        available_themes = ['creative', 'elegant', 'minimalist', 'retro', 'tech']
        
        if theme not in available_themes:
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
            'theme_assets_path': '/static/theme_assets/',
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

@app.errorhandler(404)
def not_found(e):
    return "Page not found.", 404

@app.errorhandler(500)
def server_error(e):
    return f"Internal server error: {e}", 500

# Create database tables (new approach for Flask 2.0+)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
