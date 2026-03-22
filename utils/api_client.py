import requests
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message, status_code=None, response=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class BackendAPIClient:
    """Client for connecting to backend HR/Leave APIs with API key"""
    
    def __init__(self, base_url: str, api_key: str = None, auth_type: str = 'Bearer'):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.auth_type = auth_type
        self.session = requests.Session()
        
        # Set up headers with API key
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "LeaveQuerySystem/1.0"
        }
        
        if api_key:
            if auth_type == 'Bearer':
                self.headers["Authorization"] = f"Bearer {api_key}"
            elif auth_type == 'API-Key':
                self.headers["X-API-Key"] = api_key
            elif auth_type == 'Basic':
                # For Basic auth, api_key should be base64 encoded username:password
                self.headers["Authorization"] = f"Basic {api_key}"
        
        logger.info(f"API Client initialized with base_url: {base_url}, auth_type: {auth_type}")
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, retry_count: int = 3) -> Dict:
        """Make HTTP request with retry logic"""
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retry_count):
            try:
                logger.debug(f"API Request: {method} {url} - Attempt {attempt + 1}")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    timeout=30
                )
                
                # Check if rate limited
                if response.status_code == 429:
                    wait_time = int(response.headers.get('Retry-After', 2 ** attempt))
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                # Parse response
                if response.text:
                    return response.json()
                return {}
                
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout: {url}")
                if attempt == retry_count - 1:
                    raise APIError(f"API timeout after {retry_count} attempts", status_code=408)
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP Error: {e}")
                if response.status_code == 401:
                    raise APIError("Invalid API key or authentication failed", status_code=401)
                elif response.status_code == 403:
                    raise APIError("API key does not have permission", status_code=403)
                elif response.status_code == 404:
                    raise APIError(f"Resource not found: {endpoint}", status_code=404)
                else:
                    raise APIError(f"API error: {e}", status_code=response.status_code, response=response.text)
                    
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                if attempt == retry_count - 1:
                    raise APIError(f"Failed to connect to API: {e}", status_code=503)
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise APIError(f"Unexpected error: {e}", status_code=500)
        
        raise APIError("Max retries exceeded", status_code=500)
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """GET request"""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict = None) -> Dict:
        """POST request"""
        return self._make_request('POST', endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict = None) -> Dict:
        """PUT request"""
        return self._make_request('PUT', endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict:
        """DELETE request"""
        return self._make_request('DELETE', endpoint)


class MockAPIClient:
    """Mock API client for development without API key"""
    
    def __init__(self):
        logger.info("Using Mock API Client (no API key required)")
        
        # Mock data
        self.employees = {
            "EMP001": {"id": "EMP001", "name": "Soumya Gorla", "email": "soumya@infoteck.solutions", "department": "Engineering"},
            "EMP002": {"id": "EMP002", "name": "Nitish Kumar", "email": "nitish@infoteck.solutions", "department": "Engineering"},
            "EMP003": {"id": "EMP003", "name": "Pranith Nethikunta", "email": "pranith@infoteck.solutions", "department": "Product"},
            "EMP004": {"id": "EMP004", "name": "Manoj Kumar", "email": "manoj@infoteck.solutions", "department": "HR"},
            "EMP005": {"id": "EMP005", "name": "Kiran Reddy", "email": "kiran@infoteck.solutions", "department": "Sales"}
        }
        
        self.leave_balances = {
            "EMP001": {"casual": 12, "sick": 10, "earned": 15, "compensatory": 5},
            "EMP002": {"casual": 8, "sick": 12, "earned": 12, "compensatory": 3},
            "EMP003": {"casual": 10, "sick": 8, "earned": 20, "compensatory": 4},
            "EMP004": {"casual": 15, "sick": 12, "earned": 10, "compensatory": 2},
            "EMP005": {"casual": 9, "sick": 10, "earned": 14, "compensatory": 3}
        }
        
        self.leave_records = {
            "EMP001": [
                {"id": "L001", "type": "casual", "start_date": "2024-01-10", "end_date": "2024-01-12", "status": "approved", "days": 3, "reason": "Family function"},
                {"id": "L002", "type": "sick", "start_date": "2024-02-05", "end_date": "2024-02-06", "status": "approved", "days": 2, "reason": "Fever"},
                {"id": "L003", "type": "earned", "start_date": "2024-03-15", "end_date": "2024-03-20", "status": "pending", "days": 6, "reason": "Vacation"},
            ],
            "EMP002": [
                {"id": "L004", "type": "casual", "start_date": "2024-01-20", "end_date": "2024-01-22", "status": "approved", "days": 3, "reason": "Personal work"},
                {"id": "L005", "type": "sick", "start_date": "2024-02-15", "end_date": "2024-02-16", "status": "approved", "days": 2, "reason": "Medical appointment"},
                {"id": "L006", "type": "sick", "start_date": "2024-03-10", "end_date": "2024-03-12", "status": "approved", "days": 3, "reason": "Flu"},
                {"id": "L007", "type": "earned", "start_date": "2024-03-25", "end_date": "2024-03-28", "status": "pending", "days": 4, "reason": "Family vacation"},
            ]
        }
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Mock GET request"""
        
        # Employee search
        if "/employees" in endpoint and "search" in params:
            search_term = params["search"].lower()
            results = [e for e in self.employees.values() if search_term in e["name"].lower()]
            return {"data": results, "total": len(results)}
        
        # Get employee by ID
        elif "/employees/" in endpoint:
            emp_id = endpoint.split("/")[-1]
            if emp_id in self.employees:
                return {"data": self.employees[emp_id]}
            return {"error": "Employee not found"}
        
        # Get leave balance
        elif "/leave-balance" in endpoint:
            emp_id = endpoint.split("/")[-2]
            if emp_id in self.leave_balances:
                return {"data": self.leave_balances[emp_id]}
            return {"error": "Employee not found"}
        
        # Get leave history
        elif "/leaves" in endpoint:
            emp_id = params.get("employee_id")
            if emp_id in self.leave_records:
                leaves = self.leave_records[emp_id]
                
                # Filter by date range
                if params.get("start_date") and params.get("end_date"):
                    start = params["start_date"]
                    end = params["end_date"]
                    leaves = [l for l in leaves if start <= l["start_date"] <= end]
                
                # Filter by status (exclude cancelled)
                if params.get("status"):
                    statuses = params["status"] if isinstance(params["status"], list) else [params["status"]]
                    leaves = [l for l in leaves if l["status"] in statuses]
                
                return {"data": leaves, "total": len(leaves)}
            
            return {"data": [], "total": 0}
        
        return {"data": {}}
    
    def post(self, endpoint: str, data: Dict = None) -> Dict:
        """Mock POST request"""
        return {"status": "success", "message": "Request processed successfully"}