#!/usr/bin/env python3
"""
Simple script to test JWT authentication against Salesforce using
`SalesforceRESTAPI.authenticate_jwt`.

Usage: set environment variables `SF_CLIENT_ID`, `SF_USERNAME`, and either
`SF_PRIVATE_KEY_PATH` (path to PEM) or `SF_PRIVATE_KEY` (PEM contents).

Optional: `SF_LOGIN_URL` to target sandbox (`https://test.salesforce.com`).
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()


# Ensure the parent directory is in sys.path for module import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from SalesforceRESTAPI import SalesforceRESTAPI

CLIENT_ID = os.getenv('SF_CLIENT_ID')
USERNAME = os.getenv('SF_USERNAME')
PRIVATE_KEY_PATH = os.getenv('SF_PRIVATE_KEY_PATH')
PRIVATE_KEY = os.getenv('SF_PRIVATE_KEY')
LOGIN_URL = os.getenv('SF_LOGIN_URL', 'https://login.salesforce.com')
SERVER_KEY_64 = os.getenv('SERVER_KEY_64')
SF_JWT_CLIENT_ID = os.getenv('SF_JWT_CLIENT_ID')
SF_JWT_USERNAME = os.getenv('SF_JWT_USERNAME')
SERVER_KEY_DECODED = None
if SERVER_KEY_64:
    import base64
    import binascii
    # Handle missing padding and urlsafe variants gracefully
    s = SERVER_KEY_64.strip()
    # Add '=' padding to make length a multiple of 4
    if len(s) % 4:
        s += '=' * (4 - (len(s) % 4))
    try:
        SERVER_KEY_DECODED = base64.b64decode(s).decode('utf-8')
        print("Decoded SERVER_KEY_64 using standard base64.")
        print("Length of decoded key:", len(SERVER_KEY_DECODED))
        print(" decoded key:", SERVER_KEY_DECODED)
    except (binascii.Error, ValueError):
        try:
            SERVER_KEY_DECODED = base64.urlsafe_b64decode(s)
        except Exception as e:
            raise RuntimeError('Failed to decode SERVER_KEY_64: {}'.format(e))


def main():
    if not SF_JWT_CLIENT_ID or not SF_JWT_USERNAME or SERVER_KEY_64 is None:
        print('Missing environment variables. Set SF_JWT_CLIENT_ID, SF_JWT_USERNAME and either SF_PRIVATE_KEY_PATH or SF_PRIVATE_KEY')
        sys.exit(2)

    key = PRIVATE_KEY if PRIVATE_KEY else PRIVATE_KEY_PATH
    is_file = False

    try:
        auth = SalesforceRESTAPI.authenticate_jwt(SF_JWT_CLIENT_ID, SF_JWT_USERNAME, SERVER_KEY_DECODED, login_url=LOGIN_URL, private_key_is_file=is_file)
        token = auth.get('access_token')
        print('Authentication successful.')
        if token:
            print('Access token (first 60 chars):', token[:60] + '...')
        if SalesforceRESTAPI.instance_url:
            print('Instance URL:', SalesforceRESTAPI.instance_url)
        else:
            print('Instance URL not returned in response.')
    except Exception as e:
        print('Authentication failed:', e)
        sys.exit(1)

if __name__ == '__main__':
    main()
