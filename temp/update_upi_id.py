#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to update a user's UPI ID directly in the database.
This simulates what our API endpoint does, to verify database storage works.
"""

from flask import Flask
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.models import db, User

# Create a Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/cems_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

def update_upi_id(email, upi_id):
    """Update the UPI ID for a user with the given email."""
    try:
        with app.app_context():
            # Find the user
            user = User.query.filter_by(email=email).first()
            
            if not user:
                print(f"No user found with email: {email}")
                return
            
            # Display original info
            print(f"User ID: {user.id}")
            print(f"User Name: {user.name}")
            print(f"Original UPI ID: {user.upi_id}")
            
            # Update UPI ID
            user.upi_id = upi_id
            db.session.commit()
            
            # Verify update
            updated_user = User.query.filter_by(email=email).first()
            print(f"Updated UPI ID: {updated_user.upi_id}")
            
            if updated_user.upi_id == upi_id:
                print("✅ SUCCESS: UPI ID was successfully updated in the database!")
            else:
                print(f"❌ FAILURE: UPI ID doesn't match. Expected '{upi_id}', got '{updated_user.upi_id}'")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if email and UPI ID arguments are provided
    if len(sys.argv) > 2:
        email = sys.argv[1]
        upi_id = sys.argv[2]
    else:
        email = "organiser@example.com"  # Default test email
        upi_id = "test.organiser@ybl"  # Default test UPI ID
        
    print(f"Updating UPI ID to '{upi_id}' for user with email: {email}")
    update_upi_id(email, upi_id)
