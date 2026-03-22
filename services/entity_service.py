import re
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ExtractedEntities:
    employee_name: Optional[str] = None
    date_range_expr: Optional[str] = None
    leave_type: Optional[str] = None
    status: Optional[str] = None
    raw_entities: Dict = field(default_factory=dict)


class EntityExtractor:
    """
    Hybrid entity extraction:
    - Deterministic regex for clear patterns
    - Gemini API for complex extraction
    """
    
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client
        
        # Known employees
        self.known_employees = [
            'soumya', 'soumya gorla', 'gorla',
            'nitish', 'nitish kumar', 'kumar',
            'pranith', 'pranith nethikunta', 'nethikunta',
            'manoj', 'manoj kumar',
            'kiran', 'kiran reddy', 'reddy'
        ]
        
        # Deterministic patterns
        self.employee_patterns = [
            r'(?:for|about|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\'s',
            r'balance\s+([A-Z][a-z]+)',
            r'leaves?\s+([A-Z][a-z]+)'
        ]
        
        self.date_patterns = [
            r'(last|this|next)\s+(month|week|quarter|year)',
            r'year\s+to\s+date',
            r'last\s+\d+\s+days',
            r'([A-Z][a-z]+)\s+\d{1,2}(?:\s*-\s*\d{1,2})?',
            r'Q[1-4]'
        ]
    
    def extract(self, query: str) -> ExtractedEntities:
        """
        Extract entities using deterministic rules first, then Gemini
        """
        query_original = query
        query_lower = query.lower()
        entities = ExtractedEntities()
        
        # Try deterministic extraction first
        entities.employee_name = self._deterministic_employee_extract(query_original, query_lower)
        entities.date_range_expr = self._deterministic_date_extract(query_original, query_lower)
        entities.leave_type = self._deterministic_leave_type_extract(query_lower)
        
        # If we're missing important entities, try Gemini
        if self.gemini_client and (not entities.employee_name or not entities.date_range_expr):
            try:
                logger.info("Using Gemini for entity extraction")
                gemini_entities = self.gemini_client.extract_entities(query)
                
                if not entities.employee_name and gemini_entities.get('employee_name'):
                    entities.employee_name = gemini_entities['employee_name']
                if not entities.date_range_expr and gemini_entities.get('date_range'):
                    entities.date_range_expr = gemini_entities['date_range']
                if not entities.leave_type and gemini_entities.get('leave_type'):
                    entities.leave_type = gemini_entities['leave_type']
                    
            except Exception as e:
                logger.error(f"Gemini entity extraction failed: {e}")
        
        # Store raw data
        entities.raw_entities = {
            'original_query': query,
            'has_my_keyword': 'my' in query_lower,
            'has_employee_name': entities.employee_name is not None,
            'has_date_range': entities.date_range_expr is not None
        }
        
        return entities
    
    def _deterministic_employee_extract(self, query_original: str, query_lower: str) -> Optional[str]:
        """Deterministic employee name extraction"""
        
        if re.search(r'\bmy\b|\bmine\b', query_lower):
            return None
        
        # Check known employees
        for emp in self.known_employees:
            if emp in query_lower:
                return emp.title()
        
        # Try patterns
        for pattern in self.employee_patterns:
            match = re.search(pattern, query_original, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and name.lower() not in ['balance', 'leaves', 'history']:
                    return name
        
        return None
    
    def _deterministic_date_extract(self, query_original: str, query_lower: str) -> Optional[str]:
        """Deterministic date extraction"""
        
        for pattern in self.date_patterns:
            match = re.search(pattern, query_original, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Check for month names
        months = ['january', 'february', 'march', 'april', 'may', 'june', 
                  'july', 'august', 'september', 'october', 'november', 'december']
        for month in months:
            if month in query_lower:
                return month
        
        return None
    
    def _deterministic_leave_type_extract(self, query_lower: str) -> Optional[str]:
        """Deterministic leave type extraction"""
        
        leave_types = ['casual', 'sick', 'earned', 'compensatory', 'annual', 'vacation']
        for lt in leave_types:
            if lt in query_lower:
                if lt == 'annual':
                    return 'earned'
                elif lt == 'vacation':
                    return 'earned'
                return lt
        return None