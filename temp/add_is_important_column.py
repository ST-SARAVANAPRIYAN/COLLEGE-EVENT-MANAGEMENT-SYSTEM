# Add is_important column to notifications table
from app import app, db
from models.models import Notification

def add_is_important_column():
    print("Adding is_important column to notifications table...")
    
    with app.app_context():
        try:
            # Check if the column already exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('notifications')]
            
            if 'is_important' not in columns:
                # Add the column
                db.session.execute('ALTER TABLE notifications ADD COLUMN is_important TINYINT(1) DEFAULT 0')
                db.session.commit()
                print("Successfully added is_important column!")
            else:
                print("Column is_important already exists.")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error adding column: {str(e)}")

if __name__ == '__main__':
    add_is_important_column()
