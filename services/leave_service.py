from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
import logging
from services.date_normalizer import DateRange
from utils.gemini_client import gemini_client

logger = logging.getLogger(__name__)


class LeaveService:
    """Service for leave-related operations with Google Calendar API"""
    
    def __init__(self, google_calendar_client: gemini_client = None):
        self.google_calendar_client = google_calendar_client
        self.cache = {}
    
    def get_leave_history(self, employee_id: str, 
                          date_range: Optional[DateRange] = None,
                          leave_type: Optional[str] = None) -> List[Dict]:
        """
        Get leave history using Google Calendar API
        """
        try:
            if not self.google_calendar_client:
                logger.warning("No Google Calendar client configured, returning mock data")
                return self._get_mock_leave_history(employee_id, date_range, leave_type)
            
            # Get employee email (in real system, fetch from employee service)
            employee_email = self._get_employee_email(employee_id)
            
            # Convert date range to datetime
            start_datetime = datetime.combine(date_range.start_date, datetime.min.time()) if date_range else datetime.now() - timedelta(days=30)
            end_datetime = datetime.combine(date_range.end_date, datetime.max.time()) if date_range else datetime.now()
            
            # Fetch events from Google Calendar
            events = self.google_calendar_client.get_leave_events(
                employee_email,
                start_datetime,
                end_datetime
            )
            
            # Filter by leave type if specified
            if leave_type:
                events = [e for e in events if e.get('leave_type') == leave_type]
            
            # Filter out cancelled (no cancelled events in calendar)
            active_events = [e for e in events if e.get('status') != 'cancelled']
            
            return active_events
            
        except Exception as e:
            logger.error(f"Error fetching leave history: {e}")
            return self._get_mock_leave_history(employee_id, date_range, leave_type)
    
    def get_leave_balance(self, employee_id: str, leave_type: Optional[str] = None) -> Dict:
        """
        Get leave balance from Google Calendar (calculate based on leaves taken)
        """
        try:
            # Mock balance data (in real system, this would come from HR system)
            balances = {
                "EMP001": {"casual": 12, "sick": 10, "earned": 15, "compensatory": 5},
                "EMP002": {"casual": 8, "sick": 12, "earned": 12, "compensatory": 3},
                "EMP003": {"casual": 10, "sick": 8, "earned": 20, "compensatory": 4},
                "EMP004": {"casual": 15, "sick": 12, "earned": 10, "compensatory": 2},
                "EMP005": {"casual": 9, "sick": 10, "earned": 14, "compensatory": 3}
            }
            
            emp_balance = balances.get(employee_id, {})
            
            if leave_type and leave_type in emp_balance:
                return {
                    'employee_id': employee_id,
                    'leave_type': leave_type,
                    'balance': emp_balance[leave_type]
                }
            
            return {
                'employee_id': employee_id,
                'balances': emp_balance
            }
            
        except Exception as e:
            logger.error(f"Error fetching leave balance: {e}")
            return {'employee_id': employee_id, 'balances': {}}
    
    def _get_employee_email(self, employee_id: str) -> str:
        """Get employee email from ID"""
        emails = {
            "EMP001": "soumya@infoteck.solutions",
            "EMP002": "nitish@infoteck.solutions",
            "EMP003": "pranith@infoteck.solutions",
            "EMP004": "manoj@infoteck.solutions",
            "EMP005": "kiran@infoteck.solutions"
        }
        return emails.get(employee_id, f"{employee_id}@infoteck.solutions")
    
    def _get_mock_leave_history(self, employee_id: str, 
                                date_range: Optional[DateRange],
                                leave_type: Optional[str]) -> List[Dict]:
        """Mock leave history for development"""
        
        mock_leaves = {
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
        
        leaves = mock_leaves.get(employee_id, [])
        
        # Filter by date range
        if date_range:
            filtered = []
            for leaf in leaves:
                if date_range.start_date <= date.fromisoformat(leaf['start_date']) <= date_range.end_date:
                    filtered.append(leaf)
            leaves = filtered
        
        # Filter by leave type
        if leave_type:
            leaves = [l for l in leaves if l['type'] == leave_type]
        
        # Exclude cancelled
        leaves = [l for l in leaves if l['status'] != 'cancelled']
        
        return leaves