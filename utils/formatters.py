from typing import Dict, Any, Optional
from datetime import date, datetime


class ResponseFormatter:
    """Formats responses consistently"""
    
    @staticmethod
    def success_response(data: Any, message: Optional[str] = None) -> Dict:
        """Format success response"""
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'message': message or 'Request processed successfully'
        }
    
    @staticmethod
    def error_response(message: str, error_code: Optional[str] = None, details: Optional[Dict] = None) -> Dict:
        """Format error response with optional details"""
        response = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': {
                'code': error_code or 'UNKNOWN_ERROR',
                'message': message
            }
        }
        
        if details:
            response['error']['details'] = details
        
        return response 