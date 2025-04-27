from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Increased size to accommodate password hashes
    role = Column(String(20), nullable=False)  # admin, organiser, participant
    created_at = Column(DateTime, default=datetime.utcnow)
    organization = Column(String(255), nullable=True)
    contact_number = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    
    registrations = relationship('Registration', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'organization': self.organization,
            'contact_number': self.contact_number
        }

class Event(db.Model):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    title = Column(String(200), nullable=True)  # For display purposes
    date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    start_time = Column(String(10), nullable=True)  # HH:MM format
    end_time = Column(String(10), nullable=True)  # HH:MM format
    description = Column(Text, nullable=True)
    tag = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    venue = Column(String(255), nullable=True)
    image = Column(String(255), nullable=True)
    cover_image = Column(String(255), nullable=True)
    video = Column(String(255), nullable=True)
    brochure = Column(String(255), nullable=True)
    has_exploration = Column(Boolean, default=False)
    custom_exploration_url = Column(String(255), nullable=True)
    gallery_images = Column(Text, nullable=True)  # Comma-separated image URLs
    tags = Column(String(255), nullable=True)  # Comma-separated tags
    schedule = Column(Text, nullable=True)
    price = Column(Float, default=0)
    is_free = Column(Boolean, default=True)
    seats_total = Column(Integer, default=0)
    seats_available = Column(Integer, default=0)
    registration_end_date = Column(DateTime, nullable=True)
    is_featured = Column(Boolean, default=False)
    parent_event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    organiser_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    custom_data = Column(Text, nullable=True)  # JSON string for additional data including registration theme
    ui_theme = Column(String(50), default='minimalistic')  # UI theme for registration page
    resource_allocations = relationship('ResourceAllocation', backref='event', lazy=True)
    
    sub_events = relationship('Event', backref=db.backref('parent', remote_side=[id]), lazy=True)
    registrations = relationship('Registration', backref='event', lazy=True)
    organiser = relationship('User', foreign_keys=[organiser_id], backref='organised_events')
    
    def to_dict(self):
        custom_data_obj = {}
        if self.custom_data:
            try:
                custom_data_obj = json.loads(self.custom_data)
            except:
                custom_data_obj = {}
                
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title or self.name,
            'date': self.date,
            'start_date': self.start_date.strftime("%Y-%m-%d %H:%M:%S") if self.start_date else None,
            'end_date': self.end_date.strftime("%Y-%m-%d %H:%M:%S") if self.end_date else None,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'description': self.description,
            'tag': self.tag,
            'category': self.category,
            'venue': self.venue,
            'image': self.image,
            'cover_image': self.cover_image,
            'video': self.video,
            'brochure': self.brochure,
            'has_exploration': self.has_exploration,
            'custom_exploration_url': self.custom_exploration_url,
            'gallery_images': self.gallery_images.split(',') if self.gallery_images else [],
            'tags': self.tags.split(',') if self.tags else [],
            'schedule': self.schedule,
            'price': self.price,
            'is_free': self.is_free,
            'seats_total': self.seats_total,
            'seats_available': self.seats_available,
            'registration_end_date': self.registration_end_date.strftime("%Y-%m-%d %H:%M:%S") if self.registration_end_date else None,
            'is_featured': self.is_featured,
            'parent_event_id': self.parent_event_id,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'created_by': self.created_by,
            'organiser_id': self.organiser_id,
            'custom_data': custom_data_obj,
            'ui_theme': self.ui_theme
        }

class Registration(db.Model):
    __tablename__ = 'registrations'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    payment_id = Column(String(100), nullable=True)
    payment_status = Column(String(20), default='pending')
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'registration_date': self.registration_date.strftime("%Y-%m-%d") if self.registration_date else None,
            'payment_id': self.payment_id,
            'payment_status': self.payment_status
        }

class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    total_quantity = Column(Integer, default=0)
    available_quantity = Column(Integer, default=0)
    image = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    allocations = relationship('ResourceAllocation', backref='resource', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'total_quantity': self.total_quantity,
            'available_quantity': self.available_quantity,
            'image': self.image,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'created_by': self.created_by
        }

class ResourceAllocation(db.Model):
    __tablename__ = 'resource_allocations'
    
    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    quantity = Column(Integer, default=0)
    allocated_at = Column(DateTime, default=datetime.utcnow)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='allocated')  # allocated, returned, partial
    
    def to_dict(self):
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'event_id': self.event_id,
            'quantity': self.quantity,
            'allocated_at': self.allocated_at.strftime("%Y-%m-%d %H:%M:%S") if self.allocated_at else None,
            'returned_at': self.returned_at.strftime("%Y-%m-%d %H:%M:%S") if self.returned_at else None,
            'status': self.status
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # If null, it's a broadcast
    is_read = Column(Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'created_by': self.created_by,
            'user_id': self.user_id,
            'is_read': self.is_read
        }

class EventTag(db.Model):
    __tablename__ = 'event_tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'created_by': self.created_by
        }