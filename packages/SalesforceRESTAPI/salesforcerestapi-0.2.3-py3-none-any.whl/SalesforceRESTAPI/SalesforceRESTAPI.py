
import requests
import csv
import io
import time
import os
import datetime
from typing import Optional, Dict, Any, List

class SalesforceRESTAPI:
    instance_url = None
    access_token = None
    headers = None
    last_http_status = None  # Stores the last HTTP status code
    @classmethod
    def get_last_http_status(cls):
        """
        Return the last HTTP status code from any API call (get, post, patch, delete).
        """
        return cls.last_http_status

    @staticmethod
    def authenticate(client_id: str, client_secret: str, login_url: str = 'https://login.salesforce.com') -> Dict[str, Any]:
        """
        Authenticate with Salesforce using OAuth 2.0 Client Credentials Flow and set instance_url and access_token as class variables.
        Returns the full auth response (including access_token and instance_url).
        Note: Your Salesforce org must be configured to support this flow and the connected app must have the correct permissions.
        """
        url = f"{login_url}/services/oauth2/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        auth = response.json()
        SalesforceRESTAPI.instance_url = auth['instance_url'].rstrip('/')
        SalesforceRESTAPI.access_token = auth['access_token']
        SalesforceRESTAPI.headers = {
            'Authorization': f'Bearer {SalesforceRESTAPI.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        return auth

    @staticmethod
    def authenticate_jwt(client_id: str,
                         username: str,
                         private_key: str,
                         login_url: str = 'https://login.salesforce.com',
                         audience: Optional[str] = None,
                         private_key_is_file: bool = True) -> Dict[str, Any]:
        """
        Authenticate with Salesforce using the JWT Bearer Token Flow (external client / connected app).

        Args:
            client_id: Connected App consumer key (iss claim).
            username: The Salesforce username to impersonate (sub claim).
            private_key: Path to the PEM private key file or the PEM string itself.
            login_url: Salesforce login URL (defaults to https://login.salesforce.com).
            audience: Optional audience (defaults to login_url + '/services/oauth2/token').
            private_key_is_file: If True, `private_key` is treated as a file path when it exists.

        Returns:
            Parsed JSON auth response from Salesforce containing `access_token` and optionally `instance_url`.

        Raises:
            RuntimeError: If required dependency `PyJWT` is missing or the auth request fails.

        Example:
            SalesforceRESTAPI.authenticate_jwt(CLIENT_ID, 'user@example.com', '/path/to/key.pem')
        """
        try:
            import jwt
        except Exception:
            raise RuntimeError('PyJWT is required for JWT authentication. Install with `pip install PyJWT cryptography`.')

        token_url = audience or f"{login_url}/services/oauth2/token"

        # Read private key from file if requested and path exists
        key_data = private_key
        if private_key_is_file and isinstance(private_key, str) and os.path.exists(private_key):
            with open(private_key, 'r') as f:
                key_data = f.read()

        now = int(time.time())
        payload = {
            'iss': client_id,
            'sub': username,
            'aud': token_url,
            'iat': now,
            'exp': now + 180
        }

        try:
            assertion = jwt.encode(payload, key_data, algorithm='RS256')
        except Exception as e:
            raise RuntimeError(f'Failed to sign JWT assertion: {e}')

        # PyJWT may return bytes in some versions
        if isinstance(assertion, bytes):
            assertion = assertion.decode('utf-8')

        data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': assertion
        }

        response = requests.post(token_url, data=data)
        try:
            response.raise_for_status()
        except Exception as e:
            # Surface the response body where possible for debugging
            text = getattr(response, 'text', '')
            raise RuntimeError(f'JWT authentication failed: {e} - {text}')

        auth = response.json()
        # Some orgs do not return instance_url for JWT flow (e.g., when using certain endpoints). Only set if present.
        if 'instance_url' in auth and auth['instance_url']:
            SalesforceRESTAPI.instance_url = auth['instance_url'].rstrip('/')
        SalesforceRESTAPI.access_token = auth.get('access_token')
        SalesforceRESTAPI.headers = {
            'Authorization': f"Bearer {SalesforceRESTAPI.access_token}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        return auth

    def delete_record(self, sobject: str, record_id: str) -> requests.Response:
        """
        Delete a Salesforce record by sObject type and record ID.
        Example: delete_record('Account', '001XXXXXXXXXXXXXXX')
        """
        endpoint = f"/services/data/v64.0/sobjects/{sobject}/{record_id}"
        return self.delete(endpoint)

    def update_record(self, sobject: str, record_id: str, **data) -> requests.Response:
        """
        Update a Salesforce record by sObject type and record ID.
        Example: update_record('Account', '001XXXXXXXXXXXXXXX', Name="Updated Name")
        """
        endpoint = f"/services/data/v64.0/sobjects/{sobject}/{record_id}"
        return self.patch(endpoint, data)

    def get_record(self, sobject: str, record_id: str) -> Optional[dict]:
        """
        Retrieve a Salesforce record by sObject type and record ID.
        Returns the record as a dict, or None if not found or error.
        Example: get_record('Account', '001XXXXXXXXXXXXXXX')
        """
        endpoint = f"/services/data/v64.0/sobjects/{sobject}/{record_id}"
        response = self.get(endpoint)
        try:
            return response.json()
        except Exception as e:
            print(f"Failed to parse Salesforce get_record response: {e}")
            return None


    def create_record(self, sobject: str, **data) -> Optional[str]:
        """
        Create a new Salesforce record for the given sObject type and return the new record's ID.
        Example: create_record('Account', Name="Test Account", Industry="Technology")
        Returns the Salesforce object ID if successful, otherwise None.
        """
        endpoint = f"/services/data/v64.0/sobjects/{sobject}"
        response = self.post(endpoint, data)
        try:
            result = response.json()
            return result.get('id')
        except Exception as e:
            print(f"Failed to parse Salesforce create response: {e}")
            return None
        
    def verify_record(self, sobject: str, record_id: str, **data) -> bool:
        """
        Retrieve a Salesforce record and verify that each field in data matches the record's value.
        Raises AssertionError if any field does not match.
        Returns True if all fields match.
        Example: verify_record('Account', '001XXXXXXXXXXXXXXX', Name="Test Account", Industry="Technology")
        """
        record = self.get_record(sobject, record_id)
        if record is None:
            raise AssertionError(f"Record {sobject} with ID {record_id} not found.")
        for key, value in data.items():
            if record.get(key) != value:
                raise AssertionError(f"Field '{key}' mismatch: expected '{value}', got '{record.get(key)}'")
        return True
    
    def queryRecords(self, soql: str) -> dict:
        """
        Run a SOQL query and return the parsed JSON response body.
        Example: queryRecords('SELECT Id, Name FROM Account')
        Returns the response as a dict.
        """
        response = self.run_query(soql)
        try:
            return response.json()
        except Exception as e:
            print(f"Failed to parse Salesforce queryRecords response: {e}")
            return {}
    

    def run_query(self, soql: str) -> requests.Response:
        """
        Execute a SOQL query using the Salesforce REST API.
        Example: run_query('SELECT Id, Name FROM Account')
        """
        endpoint = f"/services/data/v64.0/query"
        params = {"q": soql}
        return self.get(endpoint, params=params)

    def query_all(self, soql: str) -> Dict[str, Any]:
        """
        Execute a SOQL query using the `queryAll` endpoint to include archived and deleted records.
        This method will follow `nextRecordsUrl` until all records are retrieved and return
        a combined result dictionary with keys `totalSize` and `records`.

        Example: query_all('SELECT Id, Name FROM Account')
        """
        # Initial request to queryAll endpoint
        endpoint = f"/services/data/v64.0/queryAll"
        params = {"q": soql}
        response = self.get(endpoint, params=params)
        try:
            result = response.json()
        except Exception as e:
            print(f"Failed to parse queryAll response: {e}")
            return {"totalSize": 0, "records": []}

        records = result.get("records", [])

        # Follow nextRecordsUrl if present to page through results
        next_url = result.get("nextRecordsUrl")
        while next_url:
            # nextRecordsUrl is a path like '/services/data/vXX.X/query/01g.../2'
            response = self.get(next_url)
            try:
                page = response.json()
            except Exception as e:
                print(f"Failed to parse paged queryAll response: {e}")
                break
            records.extend(page.get("records", []))
            next_url = page.get("nextRecordsUrl")

        return {"totalSize": len(records), "records": records}
    
    """
    Simple Salesforce REST API manager for authentication and basic CRUD operations.
    """
    def __init__(self):
        self.instance_url = None
        self.access_token = None
        self.headers = None

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        if not SalesforceRESTAPI.access_token:
            raise RuntimeError("ValueError: Token not set. Please authenticate first.")
        url = f"{SalesforceRESTAPI.instance_url}{endpoint}"
        response = requests.get(url, headers=SalesforceRESTAPI.headers, params=params)
        SalesforceRESTAPI.last_http_status = response.status_code
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(f"GET {url} failed: {e} - {response.text}")
            raise
        return response

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        if not SalesforceRESTAPI.access_token:
            raise RuntimeError("ValueError: Token not set. Please authenticate first.")
        url = f"{SalesforceRESTAPI.instance_url}{endpoint}"
        response = requests.post(url, headers=SalesforceRESTAPI.headers, json=data)
        SalesforceRESTAPI.last_http_status = response.status_code
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            errors = response.json()
            if isinstance(errors, list) and errors:
                error_message = errors[0].get("message", str(e))
                print("Salesforce error:", error_message)
                raise RuntimeError(error_message)
            raise
        return response

    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        if not SalesforceRESTAPI.access_token:
            raise RuntimeError("ValueError: Token not set. Please authenticate first.")
        url = f"{SalesforceRESTAPI.instance_url}{endpoint}"
        response = requests.patch(url, headers=SalesforceRESTAPI.headers, json=data)
        SalesforceRESTAPI.last_http_status = response.status_code
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            errors = response.json()
            if isinstance(errors, list) and errors:
                error_message = errors[0].get("message", str(e))
                print("Salesforce error:", error_message)
                raise RuntimeError(error_message)
            raise
        return response

    def delete(self, endpoint: str) -> requests.Response:
        if not SalesforceRESTAPI.access_token:
            raise RuntimeError("ValueError: Token not set. Please authenticate first.")
        url = f"{SalesforceRESTAPI.instance_url}{endpoint}"
        response = requests.delete(url, headers=SalesforceRESTAPI.headers)
        SalesforceRESTAPI.last_http_status = response.status_code
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(f"DELETE {url} failed: {e} - {response.text}")
            raise
        return response
    
    def execute_apex(self, apex_code: str) -> dict:
        """
        Execute an Apex script using the Salesforce Tooling API's executeAnonymous endpoint.
        Returns the parsed JSON response with execution results.
        Example: run_apex_script('System.debug("Hello World");')
        """
        if not SalesforceRESTAPI.access_token:
            raise RuntimeError("ValueError: Token not set. Please authenticate first.")
        endpoint = "/services/data/v64.0/tooling/executeAnonymous/"
        url = f"{SalesforceRESTAPI.instance_url}{endpoint}"
        params = {"anonymousBody": apex_code}
        response = requests.get(url, headers=SalesforceRESTAPI.headers, params=params)
        try:
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to execute Apex script: {e} - {getattr(response, 'text', '')}")
            return {}

    def revoke(self):
        """
        Clear authentication state (instance_url, access_token, headers) at the class level.
        Use this to de-authenticate the API client.
        """
        SalesforceRESTAPI.instance_url = None
        SalesforceRESTAPI.access_token = None
        SalesforceRESTAPI.headers = None

    def bulk_insert_records(self, sobject: str, records: List[Dict[str, Any]], 
                           wait_for_completion: bool = True, 
                           max_wait_seconds: int = 60) -> Dict[str, Any]:
        """
        Perform a bulk insert operation using Salesforce Bulk API 2.0.
        
        Args:
            sobject: The Salesforce object type (e.g., 'Case', 'Account', 'Contact')
            records: List of dictionaries containing the records to insert
            wait_for_completion: Whether to wait for the job to complete (default: True)
            max_wait_seconds: Maximum time to wait for job completion in seconds (default: 60)
        
        Returns:
            Dictionary containing:
                - job_id: The bulk job ID
                - state: Final job state (JobComplete, InProgress, Failed, etc.)
                - records_processed: Number of records processed
                - records_failed: Number of records that failed
                - successful_results: CSV string of successful records (if completed)
                - failed_results: CSV string of failed records (if completed)
        
        Example:
            records = [
                {'Subject': 'Test Case 1', 'Status': 'New', 'Priority': 'Medium'},
                {'Subject': 'Test Case 2', 'Status': 'New', 'Priority': 'High'}
            ]
            result = sf.bulk_insert_records('Case', records)
            print(f"Job ID: {result['job_id']}")
            print(f"Records processed: {result['records_processed']}")
        """
        if not SalesforceRESTAPI.access_token:
            raise RuntimeError("ValueError: Token not set. Please authenticate first.")
        
        if not records or len(records) == 0:
            raise ValueError("Records list cannot be empty")
        
        # Step 1: Convert list of dictionaries to CSV format
        csv_content = self._convert_records_to_csv(records)
        
        # Step 2: Create bulk job
        job_id = self._create_bulk_job(sobject, "insert")
        
        # Step 3: Upload CSV data to job
        self._upload_bulk_data(job_id, csv_content)
        
        # Step 4: Close the job (mark upload as complete)
        self._close_bulk_job(job_id)
        
        # Step 5: Wait for job completion (if requested)
        result = {
            'job_id': job_id,
            'state': 'UploadComplete',
            'records_processed': 0,
            'records_failed': 0
        }
        
        if wait_for_completion:
            result = self._wait_for_bulk_job_completion(job_id, max_wait_seconds)
            
            # Get successful and failed results
            if result['state'] == 'JobComplete':
                result['successful_results'] = self._get_bulk_job_successful_results(job_id)
                result['failed_results'] = self._get_bulk_job_failed_results(job_id)
        
        return result
    
    def _convert_records_to_csv(self, records: List[Dict[str, Any]]) -> str:
        """
        Convert a list of dictionaries to CSV format string.
        
        Args:
            records: List of dictionaries to convert
            
        Returns:
            CSV formatted string with LF line endings (required by Salesforce Bulk API)
        """
        if not records:
            return ""
        
        # Get all unique field names from all records
        fieldnames = set()
        for record in records:
            fieldnames.update(record.keys())
        fieldnames = sorted(list(fieldnames))
        
        # Create CSV in memory with LF line endings (lineterminator='\n')
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def _create_bulk_job(self, sobject: str, operation: str) -> str:
        """
        Create a bulk API job.
        
        Args:
            sobject: Salesforce object type
            operation: Operation type (insert, update, upsert, delete)
            
        Returns:
            Job ID
        """
        endpoint = "/services/data/v62.0/jobs/ingest"
        job_data = {
            "object": sobject,
            "operation": operation,
            "contentType": "CSV"
        }
        
        response = self.post(endpoint, job_data)
        job_info = response.json()
        return job_info['id']
    
    def _upload_bulk_data(self, job_id: str, csv_content: str):
        """
        Upload CSV data to a bulk job.
        
        Args:
            job_id: The bulk job ID
            csv_content: CSV data as string
        """
        endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}/batches"
        url = f"{SalesforceRESTAPI.instance_url}{endpoint}"
        
        # Create headers for CSV upload
        headers = {
            **SalesforceRESTAPI.headers,
            'Content-Type': 'text/csv'
        }
        
        response = requests.put(url, headers=headers, data=csv_content.encode('utf-8'))
        SalesforceRESTAPI.last_http_status = response.status_code
        
        if response.status_code not in [200, 201]:
            raise RuntimeError(f"Failed to upload bulk data: {response.text}")
    
    def _close_bulk_job(self, job_id: str):
        """
        Close a bulk job to begin processing.
        
        Args:
            job_id: The bulk job ID
        """
        endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}"
        job_update = {"state": "UploadComplete"}
        self.patch(endpoint, job_update)
    
    def _wait_for_bulk_job_completion(self, job_id: str, max_wait_seconds: int) -> Dict[str, Any]:
        """
        Poll bulk job status until completion or timeout.
        
        Args:
            job_id: The bulk job ID
            max_wait_seconds: Maximum seconds to wait
            
        Returns:
            Dictionary with job status information
        """
        endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}"
        start_time = time.time()
        poll_interval = 2  # seconds
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                # Timeout - return current state
                response = self.get(endpoint)
                job_info = response.json()
                return {
                    'job_id': job_id,
                    'state': job_info.get('state', 'Unknown'),
                    'records_processed': job_info.get('numberRecordsProcessed', 0),
                    'records_failed': job_info.get('numberRecordsFailed', 0),
                    'timeout': True
                }
            
            # Check job status
            response = self.get(endpoint)
            job_info = response.json()
            state = job_info.get('state')
            
            # Check if job is in a terminal state
            if state in ['JobComplete', 'Failed', 'Aborted']:
                return {
                    'job_id': job_id,
                    'state': state,
                    'records_processed': job_info.get('numberRecordsProcessed', 0),
                    'records_failed': job_info.get('numberRecordsFailed', 0),
                    'timeout': False
                }
            
            # Wait before next poll
            time.sleep(poll_interval)
    
    def _get_bulk_job_successful_results(self, job_id: str) -> str:
        """
        Get successful results from a completed bulk job.
        
        Args:
            job_id: The bulk job ID
            
        Returns:
            CSV string of successful records
        """
        endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}/successfulResults"
        response = self.get(endpoint)
        return response.text
    
    def _get_bulk_job_failed_results(self, job_id: str) -> str:
        """
        Get failed results from a completed bulk job.
        
        Args:
            job_id: The bulk job ID
            
        Returns:
            CSV string of failed records
        """
        endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}/failedResults"
        response = self.get(endpoint)
        return response.text