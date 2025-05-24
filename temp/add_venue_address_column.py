# Migration script to add venue_address column to events table
# Usage: Run this script once with your database connection configured

from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError, OperationalError

# Update this with your actual database URI
DATABASE_URI = 'sqlite:///cems.db'  # Change to your DB URI if not SQLite

def add_venue_address_column():
    engine = create_engine(DATABASE_URI)
    with engine.connect() as conn:
        try:
            conn.execute('ALTER TABLE events ADD COLUMN venue_address VARCHAR(255)')
            print('venue_address column added successfully.')
        except (ProgrammingError, OperationalError) as e:
            if 'duplicate column name' in str(e) or 'already exists' in str(e):
                print('venue_address column already exists.')
            else:
                print('Error:', e)

if __name__ == '__main__':
    add_venue_address_column()
