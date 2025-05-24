import os
import re

def update_files():
    """
    Update files that reference the Transaction model to use the Registration model directly
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.join(base_dir, 'modules')
    
    # Update the payment.py file
    payment_py = os.path.join(modules_dir, 'payment.py')
    
    if os.path.exists(payment_py):
        with open(payment_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace import statements
        content = content.replace(
            "from models.models import db, Registration, User, Event, Transaction, Notification",
            "from models.models import db, Registration, User, Event, Notification"
        )
        
        # Replace transaction creation with registration updates
        content = re.sub(
            r"transaction = Transaction\(\s*registration_id=registration_id,\s*transaction_id=registration\.payment_id,\s*payment_method='upi',\s*amount=event\.price,\s*status='completed',\s*payee_name=registration\.user\.name,\s*timestamp=datetime\.utcnow\(\),\s*additional_data=json\.dumps\({[^}]*}\)\s*\)",
            r"# Update registration with transaction data\n                registration.amount = event.price\n                registration.transaction_timestamp = datetime.utcnow()\n                registration.payee_name = registration.user.name\n                registration.additional_data = json.dumps({\n                    'event_id': event.id,\n                    'event_name': event.name,\n                    'verified_by': current_user.name,\n                    'verified_by_id': current_user_id\n                })",
            content
        )
        
        # Replace transaction database operations
        content = re.sub(
            r"db\.session\.add\(transaction\)",
            r"# No need to add registration again, just update it",
            content
        )
        
        # Replace transaction query references
        content = re.sub(
            r"transaction = Transaction\.query\.filter_by\(\s*registration_id=registration_id,\s*status='completed'\s*\)\.first\(\)",
            r"# Use registration directly instead of querying for a transaction\n            transaction = None\n            if registration.payment_status == 'completed':",
            content
        )
        
        # Replace transaction attribute accesses
        content = re.sub(
            r"transaction\.transaction_id",
            r"registration.payment_id",
            content
        )
        content = re.sub(
            r"transaction\.timestamp",
            r"registration.transaction_timestamp",
            content
        )
        content = re.sub(
            r"transaction\.amount",
            r"registration.amount",
            content
        )
        content = re.sub(
            r"transaction\.payee_name",
            r"registration.payee_name",
            content
        )
        
        # Save the modified content
        with open(payment_py, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {payment_py}")
    
    # Update the organiser.py file
    organiser_py = os.path.join(modules_dir, 'organiser.py')
    
    if os.path.exists(organiser_py):
        with open(organiser_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace import statements
        content = content.replace(
            "from models.models import db, User, Event, Registration, Notification, Resource, ResourceAllocation, Transaction",
            "from models.models import db, User, Event, Registration, Notification, Resource, ResourceAllocation"
        )
        
        # Replace transaction join queries with direct registration usage
        content = re.sub(
            r"transactions = db\.session\.query\(\s*Transaction, Registration, Event, User\s*\)\.join\(\s*Registration, Transaction\.registration_id == Registration\.id\s*\)\.join\(\s*Event, Registration\.event_id == Event\.id\s*\)\.join\(\s*User, Registration\.user_id == User\.id\s*\)\.filter\(\s*Transaction\.registration_id\.in_\(registration_ids\)\s*\)\.order_by\(\s*Transaction\.timestamp\.desc\(\)\s*\)\.all\(\)",
            r"# Query registrations directly instead of transactions\n                transactions = db.session.query(\n                    Registration, Event, User\n                ).join(\n                    Event, Registration.event_id == Event.id\n                ).join(\n                    User, Registration.user_id == User.id\n                ).filter(\n                    Registration.id.in_(registration_ids),\n                    Registration.payment_status == 'completed'\n                ).order_by(\n                    Registration.transaction_timestamp.desc()\n                ).all()",
            content
        )
        
        # Replace transaction statistics calculations
        content = re.sub(
            r"total_transactions = len\(transactions\)",
            r"total_transactions = len(transactions)",
            content
        )
        content = re.sub(
            r"total_amount = sum\(t\[0\]\.amount for t in transactions\) if transactions else 0",
            r"total_amount = sum(t[0].amount for t in transactions) if transactions else 0",
            content
        )
        content = re.sub(
            r"upi_transactions = sum\(1 for t in transactions if t\[0\]\.payment_method == 'upi'\) if transactions else 0",
            r"upi_transactions = sum(1 for t in transactions if t[0].payment_method == 'upi') if transactions else 0",
            content
        )
        content = re.sub(
            r"razorpay_transactions = sum\(1 for t in transactions if t\[0\]\.payment_method == 'razorpay'\) if transactions else 0",
            r"razorpay_transactions = sum(1 for t in transactions if t[0].payment_method == 'razorpay') if transactions else 0",
            content
        )
        
        # Save the modified content
        with open(organiser_py, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {organiser_py}")
    
    print("Update completed.")
    print("Note: Some manual adjustments may still be needed in the code.")
    print("You should test thoroughly after these automated changes.")

if __name__ == "__main__":
    update_files()
