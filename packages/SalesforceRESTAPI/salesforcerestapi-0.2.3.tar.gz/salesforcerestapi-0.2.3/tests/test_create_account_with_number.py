import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to sys.path for import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from SalesforceRESTAPI import SalesforceRESTAPI

CLIENT_ID = os.getenv('SF_CLIENT_ID')
CLIENT_SECRET = os.getenv('SF_CLIENT_SECRET')
LOGIN_URL = os.getenv('SF_LOGIN_URL', 'https://login.salesforce.com')

# Authenticate
SalesforceRESTAPI.authenticate(CLIENT_ID, CLIENT_SECRET, LOGIN_URL)
sf = SalesforceRESTAPI()
# Prepare account data with AccountNumber
account_data = {
    "Name": "Test Account With Number",
    "AccountNumber": "1234567890"
}

try:
    account_id = sf.create_record('Account', Name='Test Account With Number', Industry='Technology', AccountNumber='12345678')
    # print last http code with a text message "the last http code is"
    print("The last HTTP code is:", sf.get_last_http_status())
    print("Account created successfully:", account_id)
except Exception as e:
    print("Error creating account:", e)
