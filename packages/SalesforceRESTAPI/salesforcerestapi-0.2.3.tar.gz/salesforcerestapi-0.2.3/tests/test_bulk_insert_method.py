import os
import sys
from dotenv import load_dotenv

# Ensure the parent directory is in sys.path for module import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

from SalesforceRESTAPI import SalesforceRESTAPI

CLIENT_ID = os.getenv('SF_CLIENT_ID')
CLIENT_SECRET = os.getenv('SF_CLIENT_SECRET')
LOGIN_URL = os.getenv('SF_LOGIN_URL', 'https://login.salesforce.com')

# Authenticate with Salesforce
SalesforceRESTAPI.authenticate(CLIENT_ID, CLIENT_SECRET, LOGIN_URL)
sf = SalesforceRESTAPI()

def test_bulk_insert_cases():
    """
    Test the bulk_insert_records method with a list of Case records.
    This demonstrates the simple API that accepts a list of dictionaries.
    """
    print("=== Testing bulk_insert_records Method ===\n")
    
    # Create a list of records (similar to Robot Framework example)
    records = [
        {'Subject': 'Test Case 1', 'Status': 'New', 'Priority': 'Medium', 'Origin': 'Email'},
        {'Subject': 'Test Case 2', 'Status': 'New', 'Priority': 'High', 'Origin': 'Phone'},
        {'Subject': 'Test Case 3', 'Status': 'New', 'Priority': 'Low', 'Origin': 'Web'}
    ]
    
    try:
        # Call the bulk insert method
        print(f"Inserting {len(records)} Case records...")
        result = sf.bulk_insert_records('Case', records)
        
        # Display results
        print(f"\n✓ Bulk insert completed!")
        print(f"  Job ID: {result['job_id']}")
        print(f"  State: {result['state']}")
        print(f"  Records Processed: {result['records_processed']}")
        print(f"  Records Failed: {result['records_failed']}")
        
        # Show successful records if available
        if 'successful_results' in result and result['successful_results'].strip():
            print(f"\n--- Successful Records ---")
            print(result['successful_results'])
        
        # Show failed records if any
        if 'failed_results' in result and result['failed_results'].strip():
            print(f"\n--- Failed Records ---")
            print(result['failed_results'])
        
        # Check HTTP status code
        print(f"\nLast HTTP Status: {SalesforceRESTAPI.get_last_http_status()}")
        
    except Exception as e:
        print(f"\n✗ Error during bulk insert: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_bulk_insert_cases()
