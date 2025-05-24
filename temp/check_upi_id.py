#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to check UPI ID storage in the database.
This will print the current UPI ID for a given user.
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

def check_upi_id(email):
    """Check the UPI ID for a user with the given email."""
    try:
        with app.app_context():
            # Find the user
            user = User.query.filter_by(email=email).first()
            
            if not user:
                print(f"No user found with email: {email}")
                return
            
            # Display user info and UPI ID
            print(f"User ID: {user.id}")
            print(f"User Name: {user.name}")
            print(f"User Role: {user.role}")
            print(f"UPI ID: {user.upi_id}")
            
            return user.upi_id
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if email argument is provided
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = "organiser@example.com"  # Default test email
        
    print(f"Checking UPI ID for user with email: {email}")
    check_upi_id(email)
