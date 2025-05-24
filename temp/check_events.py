from app import app
from models.models import Event

# Run this script to check if there are any events in the database
with app.app_context():
    events = Event.query.all()
    print(f'Number of events in database: {len(events)}')
    
    if events:
        print("\nFirst 5 events in database:")
        for i, event in enumerate(events[:5]):
            print(f"{i+1}. Event: {event.name}, Date: {event.start_date}, Category: {event.category}")
    else:
        print("\nThere are no events in the database.")