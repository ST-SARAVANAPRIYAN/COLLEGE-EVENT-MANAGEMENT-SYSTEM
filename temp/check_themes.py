from app import app
from models.models import Event
import json

with app.app_context():
    events = Event.query.all()
    
    for event in events:
        if event.custom_data:
            try:
                custom_data = json.loads(event.custom_data)
                theme = custom_data.get('registration_theme', 'not set')
                print(f"Event ID: {event.id}, Name: {event.name}, Theme: {theme}")
            except Exception as e:
                print(f"Event ID: {event.id}, Name: {event.name}, Error: {str(e)}")
