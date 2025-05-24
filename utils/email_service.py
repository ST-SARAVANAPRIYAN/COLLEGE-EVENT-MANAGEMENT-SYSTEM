import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, session

# Email configuration for Gmail
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = "saravanapriyan99940@gmail.com"
EMAIL_PASSWORD = "yzyd rymg hlmd qzqf"  # App password for Gmail

def send_email(to_email, subject, body):
    """Send email using SMTP"""
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email, otp, purpose="verification"):
    """Send OTP verification email"""
    try:
        email_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3e64ff; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                .otp-box {{ font-size: 24px; letter-spacing: 5px; text-align: center; 
                           background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .warning {{ color: #dc3545; font-size: 12px; margin-top: 15px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Your Verification Code</h2>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>You requested a verification code for {purpose}. Please use the following OTP to complete your process:</p>
                    
                    <div class="otp-box">
                        <strong>{otp}</strong>
                    </div>
                    
                    <p>This OTP is valid for 10 minutes.</p>
                    <p class="warning">If you didn't request this OTP, please ignore this email or contact support if you believe this is suspicious activity.</p>
                    <p>Regards,<br>College Event Management System Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {email}. If you prefer not to receive these emails, please contact support.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_email(
            email,
            "Your OTP Verification Code for CEMS",
            email_body
        )
    except Exception as e:
        print(f"OTP email error: {str(e)}")
        return False

def send_payment_verification_email(user, event, registration):
    """
    Send payment verification confirmation email to user
    
    Args:
        user: User object for recipient
        event: Event object that was paid for
        registration: Registration object with payment details
    """
    subject = f"Payment Verified: {event.name}"
    
    # Format the amount with two decimal places
    amount = "{:.2f}".format(registration.amount)
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #1a9be0; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #6c757d; }}
            .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .button {{ display: inline-block; background-color: #1a9be0; color: white; padding: 10px 20px; 
                     text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Payment Successfully Verified</h2>
            </div>
            <div class="content">
                <p>Hi {user.name},</p>
                
                <p>Your payment for <strong>{event.name}</strong> has been verified and your registration is now confirmed.</p>
                
                <div class="details">
                    <h3>Payment Details</h3>
                    <p><strong>Transaction ID:</strong> {registration.payment_id}</p>
                    <p><strong>Amount:</strong> ₹{amount}</p>
                    <p><strong>Payment Method:</strong> {registration.payment_method.upper()}</p>
                    <p><strong>Date:</strong> {registration.transaction_timestamp.strftime('%Y-%m-%d %H:%M:%S') if registration.transaction_timestamp else '-'}</p>
                </div>
                
                <div class="details">
                    <h3>Event Details</h3>
                    <p><strong>Event:</strong> {event.name}</p>
                    <p><strong>Date:</strong> {event.start_date.strftime('%Y-%m-%d') if event.start_date else event.date}</p>
                    <p><strong>Time:</strong> {event.start_time or 'TBA'}</p>
                    <p><strong>Venue:</strong> {event.venue or 'TBA'}</p>
                </div>
                
                <p>Thank you for registering! We look forward to seeing you at the event.</p>
                
                <p>Regards,<br>CEMS Team</p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, body)

def notify_participants_about_exploration(event, db, User, Registration, Notification):
    """Notify registered participants about new exploration experience"""
    try:
        # Find users registered for this event
        registered_users = []
        for reg in Registration.query.filter_by(event_id=event.id).all():
            user = User.query.get(reg.user_id)
            if user:
                registered_users.append(user)
        
        # Send notifications
        for user in registered_users:
            # Create in-app notification
            notification = Notification(
                message=f"New interactive exploration experience is now available for {event.name}!",
                user_id=user.id
            )
            db.session.add(notification)
            
            # Send email with HTML formatting
            email_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #3e64ff; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                    .button {{ display: inline-block; padding: 10px 20px; background-color: #3e64ff; color: white; 
                              text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>New Interactive Experience Available!</h2>
                    </div>
                    <div class="content">
                        <p>Hi {user.name},</p>
                        <p>We're excited to announce that an interactive exploration experience is now available for <strong>{event.name}</strong>!</p>
                        <p>This immersive experience will give you a deeper understanding of the event and its activities.</p>
                        <a href="http://localhost:5000/event_exploration/{event.id}" class="button">Explore Now</a>
                        <p>We hope you enjoy this new feature!</p>
                        <p>Regards,<br>College Event Management System Team</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent to {user.email}. If you prefer not to receive these emails, please contact support.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            send_email(
                user.email,
                f"New Exploration Experience for {event.name}",
                email_body
            )
            
        db.session.commit()
        print(f"Notifications sent to {len(registered_users)} participants about {event.name} exploration")
            
    except Exception as e:
        print(f"Notification error: {str(e)}")

def send_registration_confirmation(user, event, payment_status):
    """Send registration confirmation email to participant"""
    try:
        # Create HTML email with formatting
        email_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3e64ff; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                .details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .success {{ color: #198754; }}
                .pending {{ color: #ffc107; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Event Registration Confirmation</h2>
                </div>
                <div class="content">
                    <p>Hi {user.name},</p>
                    <p>Thank you for registering for <strong>{event.name}</strong>!</p>
                    
                    <div class="details">
                        <h3>Registration Details:</h3>
                        <p><strong>Event:</strong> {event.name}</p>
                        <p><strong>Date:</strong> {event.date}</p>
                        <p><strong>Fee:</strong> ₹{event.fee}</p>
                        <p><strong>Payment Status:</strong> 
                            <span class="{'success' if payment_status == 'completed' else 'pending'}">
                                {payment_status.upper()}
                            </span>
                        </p>
                    </div>
                    
                    <p>We look forward to your participation!</p>
                    <p>Regards,<br>College Event Management System Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {user.email}. If you prefer not to receive these emails, please contact support.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_email(
            user.email,
            f"Registration Confirmation: {event.name}",
            email_body
        )
    except Exception as e:
        print(f"Registration email error: {str(e)}")
        return False

def send_event_notification(event, users, message, sender_name="CEMS Team"):
    """Send event notification to selected users"""
    try:
        count = 0
        for user in users:
            # Create HTML email with formatting
            email_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: {('#3e64ff' if event.tag == 'technical' else '#ff9a3c') if event else '#3e64ff'}; 
                              color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                    .message {{ padding: 15px; background-color: #f9f9f9; border-radius: 5px; margin: 15px 0; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{event.name if event else 'CEMS Notification'}</h2>
                    </div>
                    <div class="content">
                        <p>Hi {user.name},</p>
                        
                        <div class="message">
                            {message}
                        </div>
                        
                        <p>Regards,<br>{sender_name}</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent to {user.email}. If you prefer not to receive these emails, please contact support.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            subject = f"{event.name + ': ' if event else ''}Important Notification"
            if send_email(user.email, subject, email_body):
                count += 1
        
        print(f"Sent event notifications to {count} users")
        return count
    except Exception as e:
        print(f"Event notification email error: {str(e)}")
        return 0