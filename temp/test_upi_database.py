#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to directly verify the UPI ID storage functionality in the database.
This script will:
1. Create a test user with organiser role
2. Update the UPI ID for this user
3. Verify the UPI ID was properly saved in the database
"""

from flask import Flask
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.models import db, User
from werkzeug.security import generate_password_hash

# Create a test Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_cems.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

def run_test():
    """Run the UPI ID storage test."""
    test_user = None
    
    try:
        with app.app_context():
            # Create database tables if they don't exist
            db.create_all()
            
            # Check if test user already exists
            test_email = "test_organiser@example.com"
            test_user = User.query.filter_by(email=test_email).first()
            
            if not test_user:
                # Create a test user
                test_user = User(
                    name="Test Organiser",
                    email=test_email,
                    password=generate_password_hash("password123"),
                    role="organiser"
                )
                db.session.add(test_user)
                db.session.commit()
                print(f"Created test user with ID: {test_user.id}")
            else:
                print(f"Using existing test user with ID: {test_user.id}")
            
            # Display current UPI ID (if any)
            print(f"Current UPI ID: {test_user.upi_id}")
            
            # Update UPI ID
            test_upi_id = "testuser@ybl"
            test_user.upi_id = test_upi_id
            db.session.commit()
            
            # Verify UPI ID was saved
            user = User.query.get(test_user.id)
            print(f"Updated UPI ID in database: {user.upi_id}")
            
            if user.upi_id == test_upi_id:
                print("✅ SUCCESS: UPI ID was successfully saved to the database!")
            else:
                print(f"❌ FAILURE: UPI ID doesn't match. Expected '{test_upi_id}', got '{user.upi_id}'")
    
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Only for verification, we won't clean up the test user
        # so we can verify it in other tests or in the UI
        pass

if __name__ == "__main__":
    run_test()
