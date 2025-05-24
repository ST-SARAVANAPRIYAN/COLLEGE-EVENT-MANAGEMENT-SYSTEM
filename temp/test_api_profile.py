#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for verifying UPI ID storage functionality in the profile API.
This script simulates a user updating their UPI ID and then verifies it was saved properly.
"""

import os
import sys
import json
import traceback
from flask import Flask, request, jsonify, session

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.models import db, User
from modules.api_profile import api_profile_bp

# Create a test Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_cems.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test_secret_key'
app.register_blueprint(api_profile_bp, url_prefix='/api/profile')

# Initialize the database
db.init_app(app)

class TestApiProfile:
    """
    Test class for API profile functionality related to UPI ID storage.
    """

    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.test_user_id = None

    def setup(self):
        """Create the database and test user."""
        with self.app.app_context():
            db.create_all()
            
            # Create a test user
            user = User(
                name="Test User",
                email="test@example.com",
                password="password",
                role="organiser"
            )
            db.session.add(user)
            db.session.commit()
            
            self.test_user_id = user.id
            print(f"Created test user with ID: {user.id}")

    def test_update_upi_id(self):
        """Test updating the UPI ID for a user."""
        with self.app.app_context():
            # Simulate login by setting the user ID in session
            with self.client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
            
            # Test data with UPI details
            payment_data = {
                "method": "upi",
                "panNumber": "ABCDE1234F",
                "upiDetails": {
                    "upiId": "testuser@bankname",
                    "name": "Test User"
                }
            }
            
            # Make the request to update payment info
            response = self.client.post(
                '/api/profile/payment',
                data=json.dumps(payment_data),
                content_type='application/json'
            )
            
            # Check the response
            result = json.loads(response.data.decode('utf-8'))
            print("API Response:", result)
            
            # Verify the UPI ID was saved in the database
            user = User.query.get(self.test_user_id)
            print(f"User UPI ID in database: {user.upi_id}")
            
            assert user.upi_id == "testuser@bankname"
            print("UPI ID was successfully saved to the database!")

    def teardown(self):
        """Clean up the test database."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

def run_tests():
    """Run the profile API tests."""
    test_runner = TestApiProfile(app)
    
    try:
        print("=== Setting up test environment ===")
        test_runner.setup()
        
        print("\n=== Running UPI ID update test ===")
        test_runner.test_update_upi_id()
        
        print("\n=== Test completed successfully! ===")
    except Exception as e:
        print(f"Test failed: {e}")
        traceback.print_exc()
    finally:
        print("\n=== Cleaning up test environment ===")
        test_runner.teardown()

if __name__ == "__main__":
    run_tests()
