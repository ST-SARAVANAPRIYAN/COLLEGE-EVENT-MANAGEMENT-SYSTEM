import os
from flask import Flask
from models.models import db, User
from datetime import datetime
from werkzeug.security import generate_password_hash
import pymysql
from sqlalchemy import text

# Create a minimal Flask app context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/cems_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Drop and recreate all tables
with app.app_context():
    # Confirm with user
    confirm = input("This will drop all existing tables and recreate them. All data will be lost. Continue? (y/n): ")
    if confirm.lower() == 'y':
        print("Dropping all tables...")
        
        # Get a database connection
        conn = db.engine.connect()
          # Disable foreign key checks temporarily
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
        
        try:
            # Instead of using SQLAlchemy's drop_all, we'll manually drop tables in the correct order
            # First get a list of all tables
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables found: {tables}")
            
            # Drop each table individually
            for table in tables:
                try:
                    print(f"Dropping table {table}...")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                except Exception as e:
                    print(f"Could not drop table {table}: {str(e)}")
            
            print("Creating new tables...")
            db.create_all()
            
            # Re-enable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
            
            # Add sample user accounts for testing
            print("Adding sample user accounts...")
            
            # Create sample users with different roles
            users = [
                User(name="System Admin", email="admin@example.com", password=generate_password_hash("1234567890"), role="admin"),
                User(name="Organiser User", email="organiser@example.com", password=generate_password_hash("1234567890"), role="organiser"),
                User(name="SARAVANA", email="saravanapriyanst@gmail.com", password=generate_password_hash("1234567890"), role="participant"),
]
            db.session.add_all(users)
            db.session.commit()
            
            # Example: Add a sample event with a non-null venue_address (if you add events here)
            # from models.models import Event
            # sample_event = Event(
            #     name="Sample Event",
            #     title="Sample Event",
            #     date="2025-05-01",
            #     start_date=datetime(2025, 5, 1, 10, 0),
            #     end_date=datetime(2025, 5, 1, 18, 0),
            #     start_time="10:00",
            #     end_time="18:00",
            #     description="A sample event for testing.",
            #     tag="technical",
            #     category="technical",
            #     venue="Main Hall",
            #     venue_lat=13.085631,
            #     venue_lng=80.219353,
            #     venue_address="123 College Street, Campus Area",  # Not null
            #     image=None,
            #     cover_image=None,
            #     video=None,
            #     brochure=None,
            #     has_exploration=False,
            #     custom_exploration_url=None,
            #     gallery_images=None,
            #     tags="",
            #     schedule=None,
            #     price=0.0,
            #     is_free=True,
            #     seats_total=100,
            #     seats_available=100,
            #     registration_end_date=None,
            #     is_featured=False,
            #     parent_event_id=None,
            #     created_at=datetime.utcnow(),
            #     created_by=1,
            #     organiser_id=2,
            #     custom_data='{"registration_theme": "minimalist"}',
            #     ui_theme='creative',
            # )
            # db.session.add(sample_event)
            # db.session.commit()
            
            print("Sample user accounts added successfully!")
            print("Database tables have been recreated successfully!")
            
        except Exception as e:
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))  # Make sure to re-enable even if there's an error
            print(f"An error occurred: {str(e)}")
            
        finally:
            conn.close()
    else:
        print("Operation cancelled.")