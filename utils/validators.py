import re
from typing import Tuple, Optional


class QueryValidator:
    """Validates incoming queries"""
    
    def __init__(self):
        self.min_query_length = 3
        self.max_query_length = 500
        
        # Blocked patterns (injection attempts)
        self.blocked_patterns = [
            r';\s*(DROP|DELETE|UPDATE|INSERT)',
            r'--',
            r'/\*.*\*/',
            r'exec\s*\(',
        ]
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate query.
        Returns (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        if len(query) < self.min_query_length:
            return False, f"Query must be at least {self.min_query_length} characters"
        
        if len(query) > self.max_query_length:
            return False, f"Query exceeds maximum length of {self.max_query_length} characters"
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Query contains invalid characters"
        
        return True, None
    
    def sanitize_query(self, query: str) -> str:
        """Sanitize query by removing dangerous characters"""
        # Remove control characters
        query = re.sub(r'[\x00-\x1f\x7f]', '', query)
        # Trim whitespace
        return query.strip()