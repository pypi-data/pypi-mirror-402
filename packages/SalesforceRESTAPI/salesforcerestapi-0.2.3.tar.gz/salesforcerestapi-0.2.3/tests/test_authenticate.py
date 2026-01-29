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

def test_authenticate():
    try:
        auth = SalesforceRESTAPI.authenticate(CLIENT_ID, CLIENT_SECRET, LOGIN_URL)
        print('Authentication successful!')
        print('Instance URL:', SalesforceRESTAPI.instance_url)
        print('Access Token:', SalesforceRESTAPI.access_token[:10] + '...')
        print('Headers:', SalesforceRESTAPI.headers)
    except Exception as e:
        print('Authentication failed:', e)

if __name__ == '__main__':
    test_authenticate()
