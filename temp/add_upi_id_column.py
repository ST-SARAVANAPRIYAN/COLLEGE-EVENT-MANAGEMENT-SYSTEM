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
        # Check if upi_id column exists in the users table
        result = db.session.execute(text("SHOW COLUMNS FROM users LIKE 'upi_id'"))
        if not result.fetchone():
            # Add upi_id column
            db.session.execute(text("ALTER TABLE users ADD COLUMN upi_id VARCHAR(100)"))
            db.session.commit()
            print("Added upi_id column to users table")
        else:
            print("upi_id column already exists")
            
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        db.session.rollback()
