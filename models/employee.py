from dataclasses import dataclass
from typing import Optional, Dict
from datetime import date

@dataclass
class Employee:
    """Employee data model"""
    id: str
    name: str
    email: str
    department: str
    join_date: date
    leave_balance: Dict[str, float]
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'join_date': self.join_date.isoformat() if self.join_date else None,
            'leave_balance': self.leave_balance,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Employee':
        """Create employee from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            email=data['email'],
            department=data['department'],
            join_date=date.fromisoformat(data['join_date']) if data.get('join_date') else None,
            leave_balance=data.get('leave_balance', {}),
            is_active=data.get('is_active', True)
        )


class EmployeeDatabase:
    """In-memory employee database with search capabilities"""
    
    def __init__(self):
        self._employees: Dict[str, Employee] = {}
        self._name_index: Dict[str, str] = {}  # name -> id
    
    def add_employee(self, employee: Employee) -> None:
        """Add or update employee"""
        self._employees[employee.id] = employee
        self._name_index[employee.name.lower()] = employee.id
        # Add variations
        name_parts = employee.name.lower().split()
        for part in name_parts:
            if len(part) > 2:  # Index significant name parts
                self._name_index[part] = employee.id
    
    def get_employee_by_id(self, emp_id: str) -> Optional[Employee]:
        """Get employee by ID"""
        return self._employees.get(emp_id)
    
    def find_employee_by_name(self, name: str) -> Optional[Employee]:
        """Find employee by name (fuzzy match)"""
        if not name:
            return None
        
        name_lower = name.lower().strip()
        
        # Exact match on full name
        if name_lower in self._name_index:
            return self._employees[self._name_index[name_lower]]
        
        # Partial match
        for stored_name, emp_id in self._name_index.items():
            if name_lower in stored_name or stored_name in name_lower:
                return self._employees[emp_id]
        
        return None
    
    def get_all_employees(self) -> list:
        """Get all employees"""
        return list(self._employees.values())