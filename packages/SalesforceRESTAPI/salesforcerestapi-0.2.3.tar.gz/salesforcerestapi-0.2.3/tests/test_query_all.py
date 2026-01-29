import os
import sys
from dotenv import load_dotenv

# Ensure the parent directory is in sys.path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env (SF_CLIENT_ID, SF_CLIENT_SECRET, SF_LOGIN_URL)
load_dotenv()

from SalesforceRESTAPI import SalesforceRESTAPI

# Read credentials from environment
CLIENT_ID = os.getenv('SF_CLIENT_ID')
CLIENT_SECRET = os.getenv('SF_CLIENT_SECRET')
LOGIN_URL = os.getenv('SF_LOGIN_URL', 'https://login.salesforce.com')

# Authenticate once (class-level) and create an instance
SalesforceRESTAPI.authenticate(CLIENT_ID, CLIENT_SECRET, LOGIN_URL)
sf = SalesforceRESTAPI()


def test_query_all_cases():
    """
    Example test that uses `query_all` to retrieve all Case records (including deleted/archived).

    Notes:
    - `query_all` wraps the REST API `/queryAll` endpoint and follows pagination using
      the `nextRecordsUrl` field until all pages are retrieved.
    - Use a SOQL query that fits your org schema. This example selects Id and Subject
      from Case. Adjust fields and filters as needed.
    - This is a simple demonstration script — in real unit tests, assert expected values.
    """
    soql = "SELECT Id, Subject FROM Case LIMIT 2000"

    print("Running query_all for Cases...")
    result = sf.query_all(soql)

    total = result.get('totalSize', 0)
    records = result.get('records', [])

    print(f"Total records fetched: {total}")

    # Print first 5 records as a quick sanity check
    for i, rec in enumerate(records[:5], start=1):
        print(f"{i}. Id={rec.get('Id')}, Subject={rec.get('Subject')}")


if __name__ == '__main__':
    test_query_all_cases()
