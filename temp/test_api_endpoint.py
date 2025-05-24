#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for verifying the UPI ID API endpoint functionality.
This script uses Flask's test client with a proper request context.
"""

import os
import sys
import json
from flask import Flask, session

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.models import db, User
from modules.api_profile import api_profile_bp
from werkzeug.security import generate_password_hash

# Create a test Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_cems.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test_secret_key'
app.register_blueprint(api_profile_bp, url_prefix='/api/profile')

# Initialize the database
db.init_app(app)

def run_api_test():
    """Run the UPI ID API endpoint test."""
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
            
            # Reset UPI ID to make sure our test works
            test_user.upi_id = None
            db.session.commit()
            print(f"Reset UPI ID to: {test_user.upi_id}")
            
            # Create a test client
            client = app.test_client()
            
            # Set session before request
            with client.session_transaction() as sess:
                sess['user_id'] = test_user.id
                print(f"Set session user_id to: {test_user.id}")
            
            # Test data with UPI details
            payment_data = {
                "method": "upi",
                "panNumber": "ABCDE1234F",
                "upiDetails": {
                    "upiId": "testuser@okicici",
                    "name": "Test User"
                }
            }
            
            # Make the request to update payment info
            print("\nCalling /api/profile/payment endpoint...")
            response = client.post(
                '/api/profile/payment',
                json=payment_data
            )
            
            # Check the response
            print(f"Response status: {response.status_code}")
            result = json.loads(response.data.decode('utf-8'))
            print(f"Response data: {result}")
            
            # Verify the UPI ID was saved in the database
            user = User.query.get(test_user.id)
            print(f"UPI ID in database after API call: {user.upi_id}")
            
            if user.upi_id == payment_data['upiDetails']['upiId']:
                print("✅ SUCCESS: UPI ID was successfully saved via the API endpoint!")
            else:
                print(f"❌ FAILURE: UPI ID doesn't match. Expected '{payment_data['upiDetails']['upiId']}', got '{user.upi_id}'")
    
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_api_test()
