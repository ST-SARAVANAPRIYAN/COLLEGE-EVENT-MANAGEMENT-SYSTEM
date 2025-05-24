from flask import Blueprint, jsonify, session, request
from models.models import db, User, Event, Registration
from functools import wraps
import traceback
import json

api_profile_bp = Blueprint('api_profile', __name__, url_prefix='/api/profile')

# Utility function to check if user is logged in
def check_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return user_id

@api_profile_bp.route('', methods=['GET'])
def get_profile():
    """
    Get the profile of the currently logged-in user.
    """
    try:
        user_id = check_auth()
        if not user_id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        
        # Get user data
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get events created by this user
        events_created = Event.query.filter_by(created_by=user_id).count()
        
        # Get total participants across all events
        events = Event.query.filter_by(created_by=user_id).all()
        total_participants = 0
        total_revenue = 0
        
        for event in events:
            registrations = Registration.query.filter_by(event_id=event.id).all()
            total_participants += len(registrations)
            
            # Calculate revenue
            if not event.is_free:
                for reg in registrations:
                    if reg.payment_status == 'completed':
                        total_revenue += event.price
        
        # Get average rating (if available)
        average_rating = 4.5  # Placeholder, replace with actual calculation if available
        
        # Social links and other data (placeholder, should come from database)
        # This data structure would ideally be stored in user.description as a JSON string
        # or in a separate profile table
        
        # Assuming user.description can contain JSON data
        social_links = {}
        documents = {
            'idProof': False,
            'addressProof': False,
            'organizationProof': False,
            'otherDocument': False
        }
        payment_info = None
        verification_status = "pending"
        
        # In a real implementation, parse these from user.description or get from appropriate tables
        
        profile_data = {
            'id': user.id,
            'name': user.name,
            'organizationName': user.organization or user.name,
            'email': user.email,
            'phone': user.contact_number,
            'profilePictureUrl': None,  # Placeholder for profile picture URL
            'biography': user.description or '',
            'address': '',
            'city': '',
            'state': '',
            'verificationStatus': verification_status,
            'stats': {
                'eventsCreated': events_created,
                'totalParticipants': total_participants,
                'averageRating': average_rating,
                'totalRevenue': total_revenue
            },
            'socialLinks': social_links,
            'documents': documents,
            'paymentInfo': payment_info,
            'upi_id': user.upi_id
        }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
@api_profile_bp.route('', methods=['POST'])
def update_profile():
    """
    Update the profile of the currently logged-in user.
    """
    try:
        user_id = check_auth()
        if not user_id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        
        # Get user data
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
        # Get data from request
        data = request.json
          # Update user data
        if 'name' in data:
            user.name = data['name']
            
        if 'phone' in data:
            user.contact_number = data['phone']
            
        if 'organizationName' in data:
            user.organization = data['organizationName']
            
        if 'biography' in data:
            user.description = data['biography']
            
        if 'address' in data:
            # Check if User model has address field
            if hasattr(user, 'address'):
                user.address = data['address']
            
        if 'city' in data:
            # Check if User model has city field
            if hasattr(user, 'city'):
                user.city = data['city']
                
        if 'state' in data:
            # Check if User model has state field
            if hasattr(user, 'state'):
                user.state = data['state']
              
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
@api_profile_bp.route('/verification', methods=['POST'])
def submit_verification():
    """
    Submit verification documents for the currently logged-in user.
    """
    try:
        user_id = check_auth()
        if not user_id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        
        # This endpoint would handle document uploads and verification status
        # For now, we'll just return a success response
        
        return jsonify({
            'success': True,
            'message': 'Verification documents submitted successfully'
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_profile_bp.route('/payment', methods=['POST'])
def update_payment_info():
    """
    Update payment information including UPI ID for the currently logged-in user.
    """
    try:
        user_id = check_auth()
        if not user_id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        
        # Get user data
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
        # Get data from request
        data = request.json
        
        # Update UPI ID if provided
        if data.get('method') == 'upi' and 'upiDetails' in data and 'upiId' in data['upiDetails']:
            user.upi_id = data['upiDetails']['upiId']
        else:
            # Clear UPI ID if payment method is not UPI
            user.upi_id = None
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment information updated successfully'
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
