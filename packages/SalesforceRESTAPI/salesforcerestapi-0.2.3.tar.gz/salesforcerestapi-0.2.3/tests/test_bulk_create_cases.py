import os
import sys
import csv
import time
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

def test_bulk_create_cases():
    """
    Test the bulk_insert_records method to create multiple Case records.
    This demonstrates using the simplified bulk insert API that accepts a list of dictionaries.
    """
    try:
        print("=== Salesforce Bulk API - Create Cases using bulk_insert_records ===\n")
        
        # Sample case data - modify as needed for your Salesforce org
        # Each dictionary represents one Case record to be created
        cases_data = [
            {
                'Subject': 'Website login issue',
                'Description': 'Customer cannot log in to the website',
                'Status': 'New',
                'Priority': 'High',
                'Origin': 'Email'
            },
            {
                'Subject': 'Product inquiry',
                'Description': 'Customer requesting information about pricing',
                'Status': 'New',
                'Priority': 'Medium',
                'Origin': 'Phone'
            },
            {
                'Subject': 'Technical support needed',
                'Description': 'Software installation problem',
                'Status': 'New',
                'Priority': 'High',
                'Origin': 'Web'
            },
            {
                'Subject': 'Billing question',
                'Description': 'Customer has questions about invoice',
                'Status': 'New',
                'Priority': 'Low',
                'Origin': 'Email'
            }
        ]
        
        print(f"Inserting {len(cases_data)} Case records using bulk_insert_records method...\n")
        
        # Call the bulk_insert_records method
        # This method handles all the Bulk API workflow internally:
        # - Converts records to CSV format
        # - Creates the bulk job
        # - Uploads the data
        # - Closes the job
        # - Waits for completion (optional)
        # - Returns results
        result = sf.bulk_insert_records('Case', cases_data, wait_for_completion=True, max_wait_seconds=60)
        
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
        print(f"\n✗ Error during bulk operation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_bulk_create_cases()
