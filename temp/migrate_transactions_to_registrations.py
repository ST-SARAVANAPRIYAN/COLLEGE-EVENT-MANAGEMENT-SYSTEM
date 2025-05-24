import os
import sys

def print_banner(message):
    """Print a banner with the given message"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80 + "\n")

def run():
    """Run the complete migration process"""
    # 1. Add transaction fields to the Registration model
    print_banner("Step 1: Adding transaction fields to Registration model")
    print("This step has already been completed manually.\n")
    
    # 2. Modify the database schema and migrate data
    print_banner("Step 2: Updating database schema and migrating data")
    try:
        from add_transaction_fields_to_registration import add_transaction_fields
        add_transaction_fields()
    except Exception as e:
        print(f"Error in database migration: {str(e)}")
        print("Please fix the error and run again.")
        return
        
    # 3. Update code references
    print_banner("Step 3: Updating code references")
    try:
        from update_transaction_references import update_files
        update_files()
    except Exception as e:
        print(f"Error updating code references: {str(e)}")
        print("Please fix the error and run again.")
        return
    
    # 4. Final instructions
    print_banner("Migration completed")
    print("""
The migration process is complete. Here's what has been done:

1. Added new transaction fields to the Registration model
2. Updated the database schema with new columns
3. Migrated data from the Transaction table to the Registration table
4. Updated code references to use Registration instead of Transaction

To complete the migration:

1. Test the application thoroughly to ensure everything works correctly
2. Once confirmed, you can drop the Transaction table with:
   ALTER TABLE transactions DROP FOREIGN KEY transactions_ibfk_1; 
   DROP TABLE transactions;

3. If any issues are found, you can:
   - Fix them manually
   - Or run the recovery script to revert changes (not provided)

Thank you for using this migration tool!
    """)

if __name__ == "__main__":
    run()
