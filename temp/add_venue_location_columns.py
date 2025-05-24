import sqlite3
import os

def add_venue_location_columns():
    """
    Add venue_lat and venue_lng columns to the events table if they don't exist
    """
    # Path to the database file
    db_path = os.path.join('cems', 'cems.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if venue_lat column exists
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Add venue_lat column if it doesn't exist
        if 'venue_lat' not in column_names:
            print("Adding venue_lat column to events table...")
            cursor.execute("ALTER TABLE events ADD COLUMN venue_lat FLOAT")
        else:
            print("venue_lat column already exists")
        
        # Add venue_lng column if it doesn't exist
        if 'venue_lng' not in column_names:
            print("Adding venue_lng column to events table...")
            cursor.execute("ALTER TABLE events ADD COLUMN venue_lng FLOAT")
        else:
            print("venue_lng column already exists")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully")
    
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    add_venue_location_columns()
