from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, current_user
from models.models import db, User
from utils.email_service import send_email, generate_otp, send_otp_email
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login():
    next_url = request.args.get('next', '')
    return render_template('login.html', next_url=next_url)

@auth_bp.route('/login', methods=['POST'])
def login_submit():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        next_url = request.form.get('next', '')
        
        # Get user by email first
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return render_template('login.html', error='Invalid email or password', next_url=next_url)
        
        # Login user with Flask-Login
        login_user(user)
        
        # Store user info in session
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.name
        session['user_email'] = user.email
        
        # Redirect based on role or next URL
        if next_url:
            return redirect(next_url)
        
        if user.role == 'participant':
            return redirect(url_for('participant.dashboard'))
        elif user.role == 'organiser':
            return redirect(url_for('organiser.dashboard'))
        elif user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        
    except Exception as e:
        print(f"Error in login submit: {e}")
        return render_template('login.html', error=f'An error occurred: {str(e)}')

# Keep the following routes for backward compatibility but they won't be used
@auth_bp.route('/login/request_otp', methods=['POST'])
def login_request_otp():
    # Redirect to new login method
    return redirect(url_for('auth.login_submit'), code=307)  # 307 preserves the POST

@auth_bp.route('/login/verify_otp', methods=['POST'])
def login_verify_otp():
    # Redirect to new login method
    return redirect(url_for('auth.login_submit'), code=307)  # 307 preserves the POST

@auth_bp.route('/login/resend_otp', methods=['POST'])
def login_resend_otp():
    # Return error as this is no longer supported
    return jsonify({'success': False, 'error': 'OTP for login is no longer required'})

@auth_bp.route('/logout')
def logout():
    logout_user()
    # Clear session data
    session.clear()
    return redirect('/')  # Direct URL redirect to homepage instead of using url_for

@auth_bp.route('/signup', methods=['GET'])
def signup():
    next_url = request.args.get('next', '')
    return render_template('signup.html', next_url=next_url)

@auth_bp.route('/signup/request_otp', methods=['POST'])
def signup_request_otp():
    try:
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        next_url = request.form.get('next', '')
        
        # Validate inputs
        if not all([firstname, lastname, email, password]):
            return render_template('signup.html', error='All fields are required')
            
        if len(password) < 8:
            return render_template('signup.html', error='Password must be at least 8 characters')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', error='Email already exists')
        
        # Generate OTP
        otp = generate_otp()
        
        # Store user data and OTP in session
        session['signup_data'] = {
            'name': f"{firstname} {lastname}",
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'password': password,
            'role': 'participant'  # Default role is participant
        }
        session['signup_otp'] = otp
        session['signup_otp_expires'] = (datetime.now() + timedelta(minutes=10)).timestamp()
        session['signup_next_url'] = next_url
        
        # Send OTP email
        send_otp_email(email, otp, purpose="account creation")
        
        # Render the signup template with OTP form
        return render_template('signup.html', otp_sent=True, email=email)
    
    except Exception as e:
        print(f"Error in signup request OTP: {e}")
        return render_template('signup.html', error=f'An error occurred: {str(e)}')

@auth_bp.route('/signup/verify_otp', methods=['POST'])
def signup_verify_otp():
    try:
        entered_otp = request.form.get('otp')
        email = request.form.get('email')
        
        # Check if OTP session data exists
        if not all(key in session for key in ['signup_otp', 'signup_data', 'signup_otp_expires']):
            return render_template('signup.html', error='Registration session expired. Please try again.')
        
        # Verify email matches
        if email != session['signup_data']['email']:
            return render_template('signup.html', error='Email mismatch. Please try again.')
        
        # Check if OTP has expired
        if datetime.now().timestamp() > session['signup_otp_expires']:
            # Clear OTP session data
            for key in ['signup_otp', 'signup_data', 'signup_otp_expires']:
                if key in session:
                    session.pop(key)
            return render_template('signup.html', error='OTP has expired. Please try again.')
        
        # Verify OTP
        if entered_otp != session['signup_otp']:
            return render_template('signup.html', otp_sent=True, email=email, error='Invalid OTP. Please try again.')
        
        # OTP is valid, create the user account
        user_data = session['signup_data']
        
        # Create new user with hashed password
        from werkzeug.security import generate_password_hash
        new_user = User(
            name=user_data['name'],
            email=user_data['email'],
            password=generate_password_hash(user_data['password']),
            role=user_data['role']
        )
        
        # Add user to database
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Send welcome email
            send_email(
                user_data['email'],
                "Welcome to CEMS",
                f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #3e64ff; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                        .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                        .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>Welcome to CEMS!</h2>
                        </div>
                        <div class="content">
                            <p>Hi {user_data['firstname']},</p>
                            <p>Welcome to the College Event Management System! Your account has been created successfully.</p>
                            <p>You can now browse and register for events, track your registrations, and more!</p>
                            <p>Regards,<br>College Event Management System Team</p>
                        </div>
                        <div class="footer">
                            <p>This email was sent to {user_data['email']}. If you prefer not to receive these emails, please contact support.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
            )
            
            # Login user with Flask-Login
            login_user(new_user)
            
            # Store user info in session
            session['user_id'] = new_user.id
            session['user_role'] = new_user.role
            session['user_name'] = new_user.name
            session['user_email'] = new_user.email
            
            # Clear signup session data
            for key in ['signup_otp', 'signup_data', 'signup_otp_expires']:
                if key in session:
                    session.pop(key)
            
            # Redirect based on next URL or to participant dashboard
            next_url = session.pop('signup_next_url', None)
            if next_url:
                return redirect(next_url)
            
            flash('Account created successfully!', 'success')
            return redirect(url_for('participant.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user account: {e}")
            return render_template('signup.html', otp_sent=True, email=email, error=f'Error creating account: {str(e)}')
        
    except Exception as e:
        print(f"Error in signup verify OTP: {e}")
        return render_template('signup.html', error=f'An error occurred: {str(e)}')

@auth_bp.route('/signup/resend_otp', methods=['POST'])
def signup_resend_otp():
    try:
        data = json.loads(request.data)
        email = data.get('email')
        
        # Check if we have this email in the session
        if 'signup_data' not in session or session['signup_data']['email'] != email:
            return jsonify({'success': False, 'error': 'Invalid email or session expired'})
        
        # Generate new OTP
        otp = generate_otp()
        
        # Update OTP and expiration in session
        session['signup_otp'] = otp
        session['signup_otp_expires'] = (datetime.now() + timedelta(minutes=10)).timestamp()
        
        # Send OTP email
        send_otp_email(email, otp, purpose="account creation")
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error in signup resend OTP: {e}")
        return jsonify({'success': False, 'error': str(e)})

@auth_bp.route('/become-organiser', methods=['GET'])
def become_organiser():
    return render_template('become_organiser.html')

@auth_bp.route('/become-organiser/request_otp', methods=['POST'])
def organiser_request_otp():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        organization = request.form.get('organization')
        contact_number = request.form.get('contact_number')
        description = request.form.get('description')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return render_template('become_organiser.html', error='Email already exists')
        
        # Generate OTP
        otp = generate_otp()
        
        # Store organiser data and OTP in session
        session['organiser_data'] = {
            'name': name,
            'email': email,
            'password': password,
            'organization': organization,
            'contact_number': contact_number,
            'description': description,
            'role': 'organiser'
        }
        session['organiser_otp'] = otp
        session['organiser_otp_expires'] = (datetime.now() + timedelta(minutes=10)).timestamp()
        
        # Send OTP email
        send_otp_email(email, otp, purpose="organiser account creation")
        
        # Render the organiser signup template with OTP form
        return render_template('become_organiser.html', otp_sent=True, email=email)
    
    except Exception as e:
        print(f"Error in organiser request OTP: {e}")
        return render_template('become_organiser.html', error=f'An error occurred: {str(e)}')

@auth_bp.route('/become-organiser/verify_otp', methods=['POST'])
def organiser_verify_otp():
    try:
        entered_otp = request.form.get('otp')
        email = request.form.get('email')
        
        # Check if OTP session data exists
        if not all(key in session for key in ['organiser_otp', 'organiser_data', 'organiser_otp_expires']):
            return render_template('become_organiser.html', error='Registration session expired. Please try again.')
        
        # Verify email matches
        if email != session['organiser_data']['email']:
            return render_template('become_organiser.html', error='Email mismatch. Please try again.')
        
        # Check if OTP has expired
        if datetime.now().timestamp() > session['organiser_otp_expires']:
            # Clear OTP session data
            for key in ['organiser_otp', 'organiser_data', 'organiser_otp_expires']:
                if key in session:
                    session.pop(key)
            return render_template('become_organiser.html', error='OTP has expired. Please try again.')
        
        # Verify OTP
        if entered_otp != session['organiser_otp']:
            return render_template('become_organiser.html', otp_sent=True, email=email, error='Invalid OTP. Please try again.')
        
        # OTP is valid, create the organiser account
        organiser_data = session['organiser_data']
        
        # Create new user with organiser role and hashed password
        from werkzeug.security import generate_password_hash
        new_organiser = User(
            name=organiser_data['name'],
            email=organiser_data['email'],
            password=generate_password_hash(organiser_data['password']),
            role='organiser',
            organization=organiser_data.get('organization', ''),
            contact_number=organiser_data.get('contact_number', ''),
            description=organiser_data.get('description', '')
        )
        db.session.add(new_organiser)
        db.session.commit()
        
        # Send welcome email for organiser
        send_email(
            organiser_data['email'],
            "Welcome to CEMS as an Organiser",
            f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #3e64ff; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Welcome to CEMS!</h2>
                    </div>
                    <div class="content">
                        <p>Hi {organiser_data['name']},</p>
                        <p>Welcome to the College Event Management System as an <strong>Organiser</strong>!</p>
                        <p>Your account has been created successfully. You can now create and manage events, track registrations, and more!</p>
                        <p>Regards,<br>College Event Management System Team</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent to {organiser_data['email']}. If you prefer not to receive these emails, please contact support.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
        
        # Set user session
        login_user(new_organiser)
        session['user_id'] = new_organiser.id
        session['user_role'] = new_organiser.role
        session['user_name'] = new_organiser.name
        session['user_email'] = new_organiser.email
        
        # Clear organiser signup session data
        for key in ['organiser_otp', 'organiser_data', 'organiser_otp_expires']:
            if key in session:
                session.pop(key)
        
        flash('Organiser account created successfully!', 'success')
        return redirect(url_for('organiser.dashboard'))
        
    except Exception as e:
        print(f"Error in organiser verify OTP: {e}")
        return render_template('become_organiser.html', error=f'An error occurred: {str(e)}')

@auth_bp.route('/become-organiser/resend_otp', methods=['POST'])
def organiser_resend_otp():
    try:
        data = json.loads(request.data)
        email = data.get('email')
        
        # Check if we have this email in the session
        if 'organiser_data' not in session or session['organiser_data']['email'] != email:
            return jsonify({'success': False, 'error': 'Invalid email or session expired'})
        
        # Generate new OTP
        otp = generate_otp()
        
        # Update OTP and expiration in session
        session['organiser_otp'] = otp
        session['organiser_otp_expires'] = (datetime.now() + timedelta(minutes=10)).timestamp()
        
        # Send OTP email
        send_otp_email(email, otp, purpose="organiser account creation")
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error in organiser resend OTP: {e}")
        return jsonify({'success': False, 'error': str(e)})

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password():
    return render_template('forgot_password.html')

@auth_bp.route('/forgot-password/request_otp', methods=['POST'])
def forgot_password_request_otp():
    try:
        email = request.form.get('email')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template('forgot_password.html', error='No account found with this email address')
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP in session
        session['reset_password_otp'] = otp
        session['reset_password_email'] = email
        session['reset_password_otp_expires'] = (datetime.now() + timedelta(minutes=10)).timestamp()
        
        # Send OTP email
        send_otp_email(email, otp, purpose="password reset")
        
        # Render template with OTP form
        return render_template('forgot_password.html', otp_sent=True, email=email)
    
    except Exception as e:
        print(f"Error in forgot password request OTP: {e}")
        return render_template('forgot_password.html', error=f'An error occurred: {str(e)}')

@auth_bp.route('/forgot-password/verify_otp', methods=['POST'])
def forgot_password_verify_otp():
    try:
        entered_otp = request.form.get('otp')
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if OTP session data exists
        if not all(key in session for key in ['reset_password_otp', 'reset_password_email', 'reset_password_otp_expires']):
            return render_template('forgot_password.html', error='Password reset session expired. Please try again.')
        
        # Verify email matches
        if email != session['reset_password_email']:
            return render_template('forgot_password.html', error='Email mismatch. Please try again.')
        
        # Check if OTP has expired
        if datetime.now().timestamp() > session['reset_password_otp_expires']:
            # Clear OTP session data
            for key in ['reset_password_otp', 'reset_password_email', 'reset_password_otp_expires']:
                if key in session:
                    session.pop(key)
            return render_template('forgot_password.html', error='OTP has expired. Please try again.')
        
        # Verify OTP
        if entered_otp != session['reset_password_otp']:
            return render_template('forgot_password.html', otp_sent=True, email=email, 
                                  error='Invalid OTP. Please try again.')
        
        # Check if passwords match
        if new_password != confirm_password:
            return render_template('forgot_password.html', otp_sent=True, email=email, 
                                  error='Passwords do not match. Please try again.')
        
        # Validate password length
        if len(new_password) < 6:
            return render_template('forgot_password.html', otp_sent=True, email=email, 
                                  error='Password must be at least 6 characters long')
        
        # OTP is valid and passwords match, update the user's password
        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template('forgot_password.html', error='User no longer exists')
        
        # Update password with hash
        from werkzeug.security import generate_password_hash
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        # Send password reset confirmation email
        send_email(
            email,
            "Password Reset Confirmation",
            f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #3e64ff; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>CEMS Password Reset</h2>
                    </div>
                    <div class="content">
                        <p>Hi {user.name},</p>
                        <p>Your password has been reset successfully.</p>
                        <p>If you did not initiate this password reset, please contact support immediately.</p>
                        <p>Regards,<br>College Event Management System Team</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent to {email}. If you prefer not to receive these emails, please contact support.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
        
        # Clear session data for password reset
        for key in ['reset_password_otp', 'reset_password_email', 'reset_password_otp_expires']:
            if key in session:
                session.pop(key)
        
        flash('Your password has been reset successfully. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        print(f"Error in forgot password verify OTP: {e}")
        return render_template('forgot_password.html', error=f'An error occurred: {str(e)}')

@auth_bp.route('/forgot-password/resend_otp', methods=['POST'])
def forgot_password_resend_otp():
    try:
        data = json.loads(request.data)
        email = data.get('email')
        
        # Check if we have this email in the session
        if 'reset_password_email' not in session or session['reset_password_email'] != email:
            return jsonify({'success': False, 'error': 'Invalid email or session expired'})
        
        # Generate new OTP
        otp = generate_otp()
        
        # Update OTP and expiration in session
        session['reset_password_otp'] = otp
        session['reset_password_otp_expires'] = (datetime.now() + timedelta(minutes=10)).timestamp()
        
        # Send OTP email
        send_otp_email(email, otp, purpose="password reset")
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error in forgot password resend OTP: {e}")
        return jsonify({'success': False, 'error': str(e)})