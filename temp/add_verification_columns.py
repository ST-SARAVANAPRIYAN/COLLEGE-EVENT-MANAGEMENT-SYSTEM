#!/usr/bin/env python
# filepath: s:\cems-dup\cems3\cems\add_verification_columns.py
"""
Migration script to add verification columns to the Registration table
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

# Add verification columns to Registration table
with app.app_context():
    try:
        print("Adding verification columns to Registration table...")
        
        # Check and add verification_notes column
        try:
            db.session.execute(text("SELECT verification_notes FROM registrations LIMIT 1"))
            print("- verification_notes column already exists")
        except Exception:
            db.session.execute(text("ALTER TABLE registrations ADD COLUMN verification_notes TEXT"))
            print("- Added verification_notes column")
            
        # Check and add verification_date column
        try:
            db.session.execute(text("SELECT verification_date FROM registrations LIMIT 1"))
            print("- verification_date column already exists")
        except Exception:
            db.session.execute(text("ALTER TABLE registrations ADD COLUMN verification_date DATETIME"))
            print("- Added verification_date column")
            
        # Check and add verified_by column
        try:
            db.session.execute(text("SELECT verified_by FROM registrations LIMIT 1"))
            print("- verified_by column already exists")
        except Exception:
            db.session.execute(text("ALTER TABLE registrations ADD COLUMN verified_by INT, ADD FOREIGN KEY (verified_by) REFERENCES users(id)"))
            print("- Added verified_by column with foreign key")
            
        db.session.commit()
        print("All verification columns added successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding verification columns: {str(e)}")

if __name__ == "__main__":
    print("Starting migration script to add verification columns...")
    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    print("Run this script to add verification columns to the Registration table.")
