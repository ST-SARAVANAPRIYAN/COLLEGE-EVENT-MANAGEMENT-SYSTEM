#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to directly call the UPI ID update function from api_profile.py
"""

from flask import Flask, Request, request
import sys
import os
import json
from unittest.mock import patch
from io import BytesIO

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.models import db, User
from modules.api_profile import update_payment_info, api_profile_bp
from werkzeug.security import generate_password_hash

# Create a test Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_cems.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test_secret_key'
app.register_blueprint(api_profile_bp, url_prefix='/api/profile')

# Initialize the database
db.init_app(app)

def create_test_request(data):
    """Create a test request object with JSON data."""
    environ = {
        'wsgi.input': BytesIO(json.dumps(data).encode('utf-8')),
        'CONTENT_LENGTH': len(json.dumps(data).encode('utf-8')),
        'CONTENT_TYPE': 'application/json',
        'REQUEST_METHOD': 'POST',
    }
    return Request(environ)

def run_direct_function_test():
    """Run a test that directly calls the update_payment_info function."""
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
            
            # Reset UPI ID to make sure our test works
            test_user.upi_id = None
            db.session.commit()
            print(f"Reset UPI ID to: {test_user.upi_id}")
            
            # Payment data with UPI details
            payment_data = {
                "method": "upi",
                "panNumber": "ABCDE1234F",
                "upiDetails": {
                    "upiId": "test.user@upi",
                    "name": "Test User"
                }
            }
            
            # Mock the user_id in session
            with patch('modules.api_profile.session', {'user_id': test_user.id}):
                with patch('modules.api_profile.request') as mock_request:
                    # Mock the request to return our payment data
                    mock_request.json = payment_data
                    
                    print("\nCalling update_payment_info function directly...")
                    # Call the function directly
                    response = update_payment_info()
                    
                    # Print the response
                    print(f"Function response: {response}")
            
            # Verify the UPI ID was saved in the database
            user = User.query.get(test_user.id)
            print(f"UPI ID in database after function call: {user.upi_id}")
            
            if user.upi_id == payment_data['upiDetails']['upiId']:
                print("✅ SUCCESS: UPI ID was successfully saved by the update_payment_info function!")
            else:
                print(f"❌ FAILURE: UPI ID doesn't match. Expected '{payment_data['upiDetails']['upiId']}', got '{user.upi_id}'")
    
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_direct_function_test()
