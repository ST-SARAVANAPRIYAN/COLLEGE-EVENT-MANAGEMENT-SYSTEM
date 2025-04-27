# College Event Management System (CEMS)

A comprehensive platform for organizing, managing, and participating in college events. It supports three user roles: Admin, Organiser, and Participant. The system provides an interactive, visually appealing, and user-friendly experience for all users, with dynamic event pages and robust management features.

## Features

### User Roles
- **Admin:** Manages the entire platform, oversees users and events, handles escalations
- **Organiser:** Creates and manages events, allocates resources, uploads media, sets event details, generates reports
- **Participant:** Registers for events, explores event details, downloads brochures, pays registration fees

### Event Management
- Events can be Main Events, Sub Events, or Single Events
- Organisers can upload exploration website files for each event
- Interactive event pages with adaptive UI based on event tags

### Payment Integration
- Razorpay integration for registration fee payments (development mode)

### Advanced Features
- Event analytics with visualizations
- Real-time notifications via email
- Responsive and accessible UI for all pages
- Dynamic event exploration pages

## Tech Stack
- Backend: Python (Flask)
- Frontend: HTML, CSS, JavaScript
- Database: MySQL
- Payment: Razorpay (dev mode)

## Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL server
- Required Python packages (see below)

### Installation

1. Clone the repository
```
git clone https://github.com/yourusername/college-event-management-system.git
cd college-event-management-system
```

2. Create and activate a virtual environment (recommended)
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages
```
pip install flask flask-sqlalchemy pymysql email
```

4. Create a MySQL database
```
mysql -u root -p
CREATE DATABASE cems_db;
exit
```

5. Update database credentials
   Open `app.py` and update the database URI with your credentials:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/cems_db'
   ```

6. Initialize the database with sample data
```
python initialize_db.py
```

7. Run the application
```
python app.py
```

8. Access the application
   Open a web browser and navigate to `http://localhost:5000`

## Sample User Accounts

- **Admin:**
  - Email: admin@example.com
  - Password: admin123

- **Organiser:**
  - Email: organiser@example.com
  - Password: organiser123

- **Participant:**
  - Email: student@example.com
  - Password: student123

## Project Structure

```
cems/
├── app.py                  # Main application file
├── initialize_db.py        # Database initialization script
├── models/
│   └── models.py           # Database models
├── modules/
│   ├── admin.py            # Admin routes
│   ├── auth.py             # Authentication routes
│   ├── event.py            # Event management routes
│   ├── organiser.py        # Organiser routes
│   ├── participant.py      # Participant routes
│   └── payment.py          # Payment routes
├── event_explorations/     # Directory for event exploration pages
├── static/
│   ├── css/                # CSS files
│   ├── js/                 # JavaScript files
│   └── uploads/            # Uploaded files (images, videos, brochures)
├── templates/              # HTML templates
└── utils/
    └── email_service.py    # Email utility functions
```

## API Endpoints

### Authentication
- `GET/POST /login` - User login
- `GET/POST /signup` - User registration
- `GET /logout` - User logout

### Events
- `GET /api/events` - Get all events
- `GET /api/events/<event_id>` - Get event details
- `POST /api/events/create` - Create a new event
- `PUT /api/events/<event_id>` - Update an event
- `DELETE /api/events/<event_id>` - Delete an event
- `POST /api/events/<event_id>/register` - Register for an event
- `POST /upload_event_exploration` - Upload event exploration files
- `GET /event_exploration/<event_id>` - View event exploration

### Payments
- `POST /api/payments/verify` - Verify payment

### Dashboards
- `GET /admin_dashboard` - Admin dashboard
- `GET /organiser_dashboard` - Organiser dashboard
- `GET /participant_dashboard` - Participant dashboard

### Analytics & Management
- `GET /api/users` - Get all users (admin only)
- `GET /api/analytics/users` - Get user analytics (admin only)
- `GET /api/analytics/events` - Get event analytics (admin/organiser)
- `GET /api/registrations` - Get registrations for events (organiser)
- `GET /api/my_registrations` - Get user's registrations (participant)
- `GET /api/my_notifications` - Get user's notifications (participant)
- `POST /api/notifications` - Send notifications (organiser)

## Future Enhancements
- Implement password hashing for security
- Add more payment gateways
- Enhance analytics with graphical representations
- Create mobile application
- Add real-time chat support