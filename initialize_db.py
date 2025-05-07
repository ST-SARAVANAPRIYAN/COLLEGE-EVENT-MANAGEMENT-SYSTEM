from app import app, db
from models.models import User, Event, Registration, Notification
from datetime import datetime
import os

def initialize_database():
    """Initialize the database structure without sample data."""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if data already exists
        if User.query.count() > 0:
            print("Database already contains data. Skipping initialization.")
            return
        
        # No sample data will be added
        print("Database tables have been initialized successfully.")

if __name__ == "__main__":
    initialize_database()