from flask import Blueprint, request, jsonify, session
from models.models import db, Registration, User, Event
from utils.email_service import send_email
import uuid

payment_bp = Blueprint('payment', __name__)

# Razorpay configuration (replace with actual API keys in production)
RAZORPAY_KEY_ID = "rzp_test_12345678"
RAZORPAY_KEY_SECRET = "secret_12345678"

@payment_bp.route('/api/payments/verify', methods=['POST'])
def verify_payment():
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        registration_id = data.get('registration_id')
        
        # In production, verify with Razorpay
        # For demo, assume payment is successful
        
        # Update registration
        registration = Registration.query.get(registration_id)
        if registration:
            registration.payment_id = payment_id
            registration.payment_status = 'completed'
            db.session.commit()
            
            # Send confirmation email
            user = User.query.get(registration.user_id)
            event = Event.query.get(registration.event_id)
            
            if user and event:
                send_email(
                    user.email,
                    f"Payment Confirmation: {event.name}",
                    f"Hi {user.name},\n\nYour payment for {event.name} has been received. Your registration is now confirmed.\n\nPayment ID: {payment_id}\nAmount: ₹{event.fee}\n\nRegards,\nCEMS Team"
                )
            
            return jsonify({"success": True, "message": "Payment verified successfully"})
        else:
            return jsonify({"error": "Registration not found"}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500