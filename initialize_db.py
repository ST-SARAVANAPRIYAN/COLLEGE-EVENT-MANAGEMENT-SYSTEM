from app import app, db
from models.models import User, Event, Registration, Notification
from datetime import datetime
import os

def initialize_database():
    """Initialize the database with sample data for testing."""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if users already exist
        if User.query.count() > 0:
            print("Database already contains data. Skipping initialization.")
            return
        
        # Create sample users
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password="admin123",  # In production, use password hashing
            role="admin"
        )
        
        organiser = User(
            name="Event Organiser",
            email="organiser@example.com",
            password="organiser123",
            role="organiser"
        )
        
        participant = User(
            name="Student Participant",
            email="student@example.com",
            password="student123",
            role="participant"
        )
        
        db.session.add_all([admin, organiser, participant])
        db.session.commit()
        
        # Create sample events
        main_event = Event(
            name="Tech Fest 2025",
            date="2025-05-10",
            description="Annual technology festival with various competitions and workshops",
            tag="technical",
            fee=0,
            created_by=organiser.id
        )
        
        sub_event1 = Event(
            name="Hackathon",
            date="2025-05-10",
            description="24-hour coding competition to solve real-world problems",
            tag="technical",
            fee=500,
            created_by=organiser.id
        )
        
        sub_event2 = Event(
            name="Robotics Workshop",
            date="2025-05-11",
            description="Learn to build and program your own robot",
            tag="technical",
            fee=300,
            created_by=organiser.id
        )
        
        cultural_event = Event(
            name="Cultural Night",
            date="2025-05-12",
            description="An evening of music, dance, and other cultural performances",
            tag="non-technical",
            fee=100,
            created_by=organiser.id
        )
        
        db.session.add_all([main_event, sub_event1, sub_event2, cultural_event])
        db.session.commit()
        
        # Set up main event and sub-events relationship
        main_event.sub_events.append(sub_event1)
        main_event.sub_events.append(sub_event2)
        db.session.commit()
        
        # Create sample registrations
        registration1 = Registration(
            event_id=sub_event1.id,
            user_id=participant.id,
            payment_status="completed",
            payment_id="pay_sample123"
        )
        
        registration2 = Registration(
            event_id=cultural_event.id,
            user_id=participant.id,
            payment_status="completed",
            payment_id="pay_sample456"
        )
        
        db.session.add_all([registration1, registration2])
        db.session.commit()
        
        # Create sample notifications
        notification1 = Notification(
            message="Welcome to the College Event Management System!",
            user_id=None,  # Broadcast notification
            created_by=admin.id
        )
        
        notification2 = Notification(
            message="You are registered for the Hackathon. Get ready!",
            user_id=participant.id,
            created_by=organiser.id
        )
        
        db.session.add_all([notification1, notification2])
        db.session.commit()
        
        print("Database initialized with sample data.")

if __name__ == "__main__":
    initialize_database()