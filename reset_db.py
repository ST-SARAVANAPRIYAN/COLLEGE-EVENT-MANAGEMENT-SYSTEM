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
            # Drop all tables
            db.drop_all()
            print("Creating new tables...")
            db.create_all()
            
            # Re-enable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
            
            # Add sample user accounts for testing
            print("Adding sample user accounts...")
            
            # Create sample users with different roles
            users = [
                User(name="System Admin", email="admin@example.com", password=generate_password_hash("admin123"), role="admin"),
                User(name="Organiser User", email="organiser@example.com", password=generate_password_hash("organiser123"), role="organiser"),
                User(name="Student 1", email="student1@example.com", password=generate_password_hash("student123"), role="participant"),
                User(name="Student 2", email="student2@example.com", password=generate_password_hash("student123"), role="participant"),
                User(name="Faculty Member", email="faculty@example.com", password=generate_password_hash("faculty123"), role="participant")
            ]
            db.session.add_all(users)
            db.session.commit()
            
            print("Sample user accounts added successfully!")
            print("Database tables have been recreated successfully!")
            
        except Exception as e:
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))  # Make sure to re-enable even if there's an error
            print(f"An error occurred: {str(e)}")
            
        finally:
            conn.close()
    else:
        print("Operation cancelled.")