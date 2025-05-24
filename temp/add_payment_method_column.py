#!/usr/bin/env python
# filepath: s:\cems-dup\cems3\cems\add_payment_method_column.py
"""
Migration script to add the payment_method column to the Registration table
"""
from flask import Flask
from models.models import db
from sqlalchemy import text
import os

# Create a Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/cems_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Add payment_method column to Registration table
with app.app_context():
    # Check if the column already exists
    try:
        # Try to select from the column to check if it exists
        result = db.session.execute(text("SELECT payment_method FROM registrations LIMIT 1")).fetchone()
        print("Column 'payment_method' already exists in the registrations table.")
    except Exception as e:
        # If column doesn't exist, add it
        print("Adding 'payment_method' column to registrations table...")
        db.session.execute(text("ALTER TABLE registrations ADD COLUMN payment_method VARCHAR(50) DEFAULT NULL"))
        db.session.commit()
        print("Column 'payment_method' added successfully!")

if __name__ == "__main__":
    print("Run this script to add the payment_method column to the Registration table.")
