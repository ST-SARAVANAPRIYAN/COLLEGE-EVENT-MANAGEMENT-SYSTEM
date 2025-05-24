from flask import Flask
from models.models import db, Registration
import json

# Create a temporary Flask app to verify the migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/cems_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def verify_migration():
    """
    Verify that the transaction fields have been added to the Registration model
    """
    with app.app_context():
        try:
            # Check if the Registration table has the new columns
            print("Verifying database schema...")
            result = db.session.execute("SHOW COLUMNS FROM registrations").fetchall()
            columns = [row[0] for row in result]
            
            required_columns = ['amount', 'transaction_timestamp', 'payee_name', 'additional_data']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if not missing_columns:
                print("SUCCESS: All required columns exist in the Registration table.")
            else:
                print(f"ERROR: Missing columns in Registration table: {', '.join(missing_columns)}")
            
            print("\nCurrent columns in Registration table:")
            for column in columns:
                print(f"- {column}")
            
            # Check if any registrations have transaction data
            registrations = Registration.query.filter(Registration.amount > 0).all()
            print(f"\nFound {len(registrations)} registrations with transaction data.")
            
            # Display some sample data
            if registrations:
                sample = registrations[0]
                print("\nSample registration with transaction data:")
                print(f"Registration ID: {sample.id}")
                print(f"Event ID: {sample.event_id}")
                print(f"Payment ID: {sample.payment_id}")
                print(f"Amount: {sample.amount}")
                print(f"Transaction timestamp: {sample.transaction_timestamp}")
                print(f"Payee name: {sample.payee_name}")
                
                # Display additional data if available
                if sample.additional_data:
                    try:
                        additional_data = json.loads(sample.additional_data)
                        print("Additional data:")
                        for key, value in additional_data.items():
                            print(f"  {key}: {value}")
                    except:
                        print("Additional data (raw):", sample.additional_data)
            
            print("\nMigration verification completed.")
            
        except Exception as e:
            print(f"Error verifying migration: {str(e)}")

if __name__ == "__main__":
    verify_migration()
