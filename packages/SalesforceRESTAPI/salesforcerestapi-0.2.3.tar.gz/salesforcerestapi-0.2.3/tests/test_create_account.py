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

# Authenticate
SalesforceRESTAPI.authenticate(CLIENT_ID, CLIENT_SECRET, LOGIN_URL)
sf = SalesforceRESTAPI()

def test_create_account():
    try:
        account_id = sf.create_record('Account', Name='Test Account', Industry='Technology')
        print('Account created successfully!')
        print('Account ID:', account_id)
    except Exception as e:
        print('Account creation failed:', e)

if __name__ == '__main__':
    test_create_account()
