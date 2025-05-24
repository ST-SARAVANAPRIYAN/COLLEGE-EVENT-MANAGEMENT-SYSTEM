from flask import Flask
from models.models import db, Registration, Transaction
import json
from datetime import datetime

# Create a temporary Flask app to run the migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/cems_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_transaction_fields():
    """
    Add fields from Transaction table to Registration table
    """
    with app.app_context():
        # Add new columns to Registration table
        print("Starting migration - adding transaction fields to registration table...")
        
        # First, check if we need to modify the table schema
        # This would normally be done with Alembic migrations, but for simplicity, we'll use direct SQL
        try:
            db.session.execute("""
                ALTER TABLE registrations 
                ADD COLUMN amount FLOAT DEFAULT 0.0,
                ADD COLUMN transaction_timestamp DATETIME,
                ADD COLUMN payee_name VARCHAR(255),
                ADD COLUMN additional_data TEXT
            """)
            db.session.commit()
            print("Schema updated: Transaction fields added to Registration table.")
        except Exception as e:
            print(f"Error updating schema: {str(e)}")
            print("Schema might already have those columns or there was an error.")
            db.session.rollback()
        
        # Now migrate the data from transactions to registrations
        transactions = Transaction.query.all()
        print(f"Found {len(transactions)} transactions to migrate")
        
        for transaction in transactions:
            try:
                # Get the registration
                registration = Registration.query.get(transaction.registration_id)
                if registration:
                    # Add the transaction data to the registration
                    registration.amount = transaction.amount
                    registration.transaction_timestamp = transaction.timestamp
                    registration.payee_name = transaction.payee_name
                    registration.additional_data = transaction.additional_data
                    
                    print(f"Updated registration {registration.id} with transaction data")
                else:
                    print(f"Registration not found for transaction {transaction.id}")
            except Exception as e:
                print(f"Error updating registration {transaction.registration_id}: {str(e)}")
        
        try:
            # Commit all changes
            db.session.commit()
            print("All transaction data migrated to registrations successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes: {str(e)}")
        
        # IMPORTANT: If this was a complete migration, you would also add code to remove the transactions table
        # However, for safety reasons, we're not including that step in this script
        
        print("Migration completed.")

if __name__ == "__main__":
    add_transaction_fields()
    print("You can now manually update your code to use the Registration table instead of the Transaction table.")
    print("Once you've confirmed everything works correctly, you can remove the Transaction table with:")
    print("ALTER TABLE transactions DROP FOREIGN KEY transactions_ibfk_1; DROP TABLE transactions;")
