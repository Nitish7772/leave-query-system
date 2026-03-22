from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Dict, List
from enum import Enum

class LeaveStatus(Enum):
    """Leave request status"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'
    
    @classmethod
    def valid_statuses(cls) -> List[str]:
        """Get list of valid statuses"""
        return [status.value for status in cls]
    
    @classmethod
    def active_statuses(cls) -> List[str]:
        """Get active (non-cancelled) statuses"""
        return [cls.APPROVED.value, cls.PENDING.value]


class LeaveType(Enum):
    """Leave type"""
    CASUAL = 'casual'
    SICK = 'sick'
    EARNED = 'earned'
    COMPENSATORY = 'compensatory'


@dataclass
class LeaveRecord:
    """Leave record data model"""
    id: str
    employee_id: str
    leave_type: str
    start_date: date
    end_date: date
    status: str
    reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'reason': self.reason,
            'days': self.calculate_days(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_days(self) -> float:
        """Calculate number of leave days"""
        if not self.start_date or not self.end_date:
            return 0
        delta = self.end_date - self.start_date
        return delta.days + 1  # Inclusive count
    
    def is_valid(self) -> bool:
        """Check if leave record is valid"""
        return (
            self.status != LeaveStatus.CANCELLED.value and
            self.start_date <= self.end_date and
            self.leave_type in LeaveType._value2member_map_
        )


class LeaveDatabase:
    """In-memory leave database"""
    
    def __init__(self):
        self._leaves: Dict[str, LeaveRecord] = {}
        self._employee_leaves: Dict[str, List[str]] = {}  # employee_id -> list of leave ids
    
    def add_leave(self, leave: LeaveRecord) -> None:
        """Add or update leave record"""
        self._leaves[leave.id] = leave
        if leave.employee_id not in self._employee_leaves:
            self._employee_leaves[leave.employee_id] = []
        if leave.id not in self._employee_leaves[leave.employee_id]:
            self._employee_leaves[leave.employee_id].append(leave.id)
    
    def get_leaves_by_employee(self, employee_id: str, 
                                start_date: Optional[date] = None,
                                end_date: Optional[date] = None,
                                status_filter: Optional[List[str]] = None) -> List[LeaveRecord]:
        """Get leaves for an employee with filters"""
        leave_ids = self._employee_leaves.get(employee_id, [])
        leaves = [self._leaves[lid] for lid in leave_ids if lid in self._leaves]
        
        # Apply filters
        filtered = []
        for leave in leaves:
            # Status filter
            if status_filter and leave.status not in status_filter:
                continue
            
            # Date range filter
            if start_date and leave.end_date < start_date:
                continue
            if end_date and leave.start_date > end_date:
                continue
            
            filtered.append(leave)
        
        return sorted(filtered, key=lambda x: x.start_date, reverse=True)
    
    def get_balance(self, employee_id: str, leave_type: Optional[str] = None) -> Dict[str, float]:
        """Calculate leave balance for employee"""
        # This would typically query an HR system
        # For demo, returning mock data
        return {
            'casual': 12.0,
            'sick': 10.0,
            'earned': 15.0,
            'compensatory': 5.0
        }