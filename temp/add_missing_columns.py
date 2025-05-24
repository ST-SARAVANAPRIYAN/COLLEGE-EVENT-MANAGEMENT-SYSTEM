from flask import Flask
from models.models import db
from sqlalchemy import text

app = Flask(__name__)
# Using the same database configuration from app.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/cems_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        # Check if custom_data column exists
        result = db.session.execute(text("SHOW COLUMNS FROM events LIKE 'custom_data'"))
        if not result.fetchone():
            # Add custom_data column
            db.session.execute(text("ALTER TABLE events ADD COLUMN custom_data TEXT"))
            db.session.commit()
            print("Added custom_data column to events table")
        else:
            print("custom_data column already exists")
            
        # Check if ui_theme column exists
        result = db.session.execute(text("SHOW COLUMNS FROM events LIKE 'ui_theme'"))
        if not result.fetchone():
            # Add ui_theme column
            db.session.execute(text("ALTER TABLE events ADD COLUMN ui_theme VARCHAR(50) DEFAULT 'minimalistic'"))
            db.session.commit()
            print("Added ui_theme column to events table")
        else:
            print("ui_theme column already exists")
            
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        db.session.rollback()