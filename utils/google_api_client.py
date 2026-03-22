import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

class GoogleAPIClient:
    """Client for Google Calendar API to fetch leave/absence data"""
    
    def __init__(self, api_key: str, calendar_id: str = 'primary'):
        self.api_key = api_key
        self.calendar_id = calendar_id
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar service with API key"""
        try:
            # Build service with API key (for public calendars)
            self.service = build('calendar', 'v3', developerKey=self.api_key)
            logger.info("Google Calendar API initialized with API key")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar API: {e}")
            raise
    
    def get_leave_events(self, employee_email: str, start_date: datetime, 
                         end_date: datetime) -> List[Dict]:
        """
        Fetch leave events from Google Calendar for an employee
        """
        try:
            # Search for events with employee email in attendees or description
            # Convert to RFC3339 format
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # Query events
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                q=employee_email,  # Search by employee email
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Parse events into leave records
            leave_records = []
            for event in events:
                # Check if this is a leave/absence event
                summary = event.get('summary', '').lower()
                description = event.get('description', '').lower()
                
                if any(keyword in summary or keyword in description 
                       for keyword in ['leave', 'vacation', 'sick', 'pto', 'holiday', 'absent']):
                    
                    # Determine leave type
                    leave_type = self._determine_leave_type(summary + " " + description)
                    
                    # Get start and end dates
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    
                    leave_records.append({
                        'id': event.get('id'),
                        'employee_email': employee_email,
                        'leave_type': leave_type,
                        'start_date': start[:10] if len(start) > 10 else start,
                        'end_date': end[:10] if len(end) > 10 else end,
                        'status': 'approved',  # Events on calendar are considered approved
                        'reason': event.get('description', ''),
                        'summary': event.get('summary', ''),
                        'days': self._calculate_days(start, end)
                    })
            
            logger.info(f"Found {len(leave_records)} leave events for {employee_email}")
            return leave_records
            
        except Exception as e:
            logger.error(f"Error fetching Google Calendar events: {e}")
            return []
    
    def _determine_leave_type(self, text: str) -> str:
        """Determine leave type from event text"""
        text_lower = text.lower()
        
        if 'sick' in text_lower or 'medical' in text_lower:
            return 'sick'
        elif 'vacation' in text_lower or 'holiday' in text_lower:
            return 'earned'
        elif 'pto' in text_lower:
            return 'earned'
        elif 'casual' in text_lower:
            return 'casual'
        else:
            return 'casual'  # Default leave type
    
    def _calculate_days(self, start: str, end: str) -> int:
        """Calculate number of days between start and end"""
        try:
            # Parse dates (handle both datetime and date formats)
            if 'T' in start:
                start_date = datetime.fromisoformat(start.replace('Z', '+00:00')).date()
            else:
                start_date = datetime.strptime(start, '%Y-%m-%d').date()
            
            if 'T' in end:
                end_date = datetime.fromisoformat(end.replace('Z', '+00:00')).date()
            else:
                end_date = datetime.strptime(end, '%Y-%m-%d').date()
            
            delta = end_date - start_date
            return delta.days + 1  # Inclusive count
            
        except Exception as e:
            logger.error(f"Error calculating days: {e}")
            return 1
    
    def get_employee_calendar(self, employee_email: str) -> Dict:
        """Get employee's calendar settings"""
        try:
            # This would fetch calendar settings for an employee
            # For now, return mock data
            return {
                'email': employee_email,
                'calendar_id': self.calendar_id,
                'timezone': 'UTC',
                'working_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            }
        except Exception as e:
            logger.error(f"Error fetching employee calendar: {e}")
            return {}


class GoogleWorkspaceAPIClient:
    """Client for Google Workspace APIs (Admin SDK, Directory API)"""
    
    def __init__(self, api_key: str, service_account_file: str = None):
        self.api_key = api_key
        self.service_account_file = service_account_file
        self.credentials = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize credentials for Google Workspace APIs"""
        try:
            if self.service_account_file and os.path.exists(self.service_account_file):
                # Use service account for domain-wide delegation
                self.credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file,
                    scopes=['https://www.googleapis.com/auth/admin.directory.user.readonly',
                           'https://www.googleapis.com/auth/calendar.readonly']
                )
                logger.info("Google Workspace API initialized with service account")
            else:
                # Use API key for public access
                logger.info("Using API key for Google Workspace API")
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Workspace API: {e}")
    
    def search_employees(self, search_term: str) -> List[Dict]:
        """Search employees in Google Workspace Directory"""
        try:
            if not self.credentials:
                # Fallback to mock data if no service account
                return self._mock_employee_search(search_term)
            
            # Build Directory service
            service = build('admin', 'directory_v1', credentials=self.credentials)
            
            # Search users
            results = service.users().list(
                domain='infoteck.solutions',  # Your domain
                query=f"name:{search_term} OR email:{search_term}",
                maxResults=50
            ).execute()
            
            users = results.get('users', [])
            
            return [{
                'id': user.get('id'),
                'name': user.get('name', {}).get('fullName'),
                'email': user.get('primaryEmail'),
                'department': user.get('organizations', [{}])[0].get('department', '')
            } for user in users]
            
        except Exception as e:
            logger.error(f"Error searching employees: {e}")
            return self._mock_employee_search(search_term)
    
    def _mock_employee_search(self, search_term: str) -> List[Dict]:
        """Mock employee search for development"""
        employees = [
            {'id': 'EMP001', 'name': 'Soumya Gorla', 'email': 'soumya@infoteck.solutions', 'department': 'Engineering'},
            {'id': 'EMP002', 'name': 'Nitish Kumar', 'email': 'nitish@infoteck.solutions', 'department': 'Engineering'},
            {'id': 'EMP003', 'name': 'Pranith Nethikunta', 'email': 'pranith@infoteck.solutions', 'department': 'Product'},
            {'id': 'EMP004', 'name': 'Manoj Kumar', 'email': 'manoj@infoteck.solutions', 'department': 'HR'},
            {'id': 'EMP005', 'name': 'Kiran Reddy', 'email': 'kiran@infoteck.solutions', 'department': 'Sales'}
        ]
        
        search_lower = search_term.lower()
        results = [e for e in employees if search_lower in e['name'].lower() or search_lower in e['email'].lower()]
        return results