from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Mock Employee Data (should be in a separate file, but here for clarity)
EMPLOYEES = {
    "EMP001": {"id": "EMP001", "name": "Soumya Gorla", "email": "soumya@infoteck.solutions", "department": "Engineering"},
    "EMP002": {"id": "EMP002", "name": "Nitish Kumar", "email": "nitish@infoteck.solutions", "department": "Engineering"},
    "EMP003": {"id": "EMP003", "name": "Pranith Nethikunta", "email": "pranith@infoteck.solutions", "department": "Product"},
    "EMP004": {"id": "EMP004", "name": "Manoj Kumar", "email": "manoj@infoteck.solutions", "department": "HR"},
    "EMP005": {"id": "EMP005", "name": "Kiran Reddy", "email": "kiran@infoteck.solutions", "department": "Sales"}
}


class EmployeeService:
    """Service for employee-related operations"""
    
    def __init__(self):
        self.employees = EMPLOYEES
        logger.info(f"EmployeeService initialized with {len(self.employees)} employees")
    
    def resolve_employee(self, employee_name: Optional[str], context_user_id: str) -> Tuple[Optional[Dict], str]:
        """
        Resolve employee from name or context.
        Returns (employee, resolution_status)
        """
        
        # Case 1: No employee specified or "my"/"me" - use context user
        if not employee_name or employee_name.lower() in ['my', 'me', 'mine', '']:
            employee = self.employees.get(context_user_id)
            if employee:
                logger.info(f"Using context user: {employee['name']}")
                return employee, 'context'
            return None, 'context_user_not_found'
        
        # Case 2: Try exact match (case insensitive)
        employee_name_lower = employee_name.lower()
        for emp_id, emp in self.employees.items():
            if emp['name'].lower() == employee_name_lower:
                logger.info(f"Exact match found: {emp['name']}")
                return emp, 'success'
        
        # Case 3: Try partial match (name contains the search term)
        matches = []
        for emp_id, emp in self.employees.items():
            if employee_name_lower in emp['name'].lower():
                matches.append(emp)
            # Also check if any part of the name matches (e.g., "Kumar" matches "Nitish Kumar")
            elif any(part.lower() == employee_name_lower for part in emp['name'].lower().split()):
                matches.append(emp)
        
        if len(matches) == 1:
            logger.info(f"Partial match found: {matches[0]['name']} for '{employee_name}'")
            return matches[0], 'partial'
        elif len(matches) > 1:
            logger.warning(f"Multiple matches found for '{employee_name}': {[m['name'] for m in matches]}")
            return None, 'ambiguous'
        
        # Case 4: No matches found
        logger.warning(f"No employee found for: {employee_name}")
        return None, 'not_found'
    
    def get_employee_by_id(self, emp_id: str) -> Optional[Dict]:
        """Get employee by ID"""
        return self.employees.get(emp_id)
    
    def get_all_employees(self) -> List[Dict]:
        """Get all employees"""
        return list(self.employees.values())
    
    def search_employees(self, search_term: str) -> List[Dict]:
        """Search employees by name (partial match)"""
        search_lower = search_term.lower()
        results = []
        for emp in self.employees.values():
            if search_lower in emp['name'].lower():
                results.append(emp)
            elif any(search_lower in part for part in emp['name'].lower().split()):
                results.append(emp)
        return results