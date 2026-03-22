import google.generativeai as genai
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        self.api_key = api_key
        self.model_name = model_name
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        logger.info(f"Gemini API initialized with model: {model_name}")
    
    def detect_intent(self, query: str) -> Dict:
        """
        Use Gemini to detect intent from natural language query
        Returns structured intent information
        """
        try:
            prompt = f"""
            Analyze this leave management query and return ONLY a JSON object with:
            - intent: one of ["leave_balance", "leave_history", "leave_status", "leave_request", "unknown"]
            - confidence: number between 0 and 1
            - entities: {{employee_name, date_range, leave_type, status}}
            
            Query: "{query}"
            
            Return only JSON, no other text.
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            logger.info(f"Gemini intent detection: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {
                'intent': 'unknown',
                'confidence': 0,
                'entities': {}
            }
    
    def extract_entities(self, query: str) -> Dict:
        """
        Use Gemini to extract entities from query
        """
        try:
            prompt = f"""
            Extract the following entities from this leave management query:
            - employee_name: name of the employee (if specified, otherwise null)
            - date_range: date expression (e.g., "last month", "March 15-20", null if not specified)
            - leave_type: type of leave (casual, sick, earned, compensatory, null if not specified)
            - status: leave status (pending, approved, cancelled, null if not specified)
            
            Query: "{query}"
            
            Return only a JSON object with these fields, no other text.
            """
            
            response = self.model.generate_content(prompt)
            entities = json.loads(response.text)
            
            logger.info(f"Gemini entity extraction: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {
                'employee_name': None,
                'date_range': None,
                'leave_type': None,
                'status': None
            }
    
    def normalize_date(self, date_expression: str, reference_date: datetime) -> Dict:
        """
        Use Gemini to normalize date expressions
        """
        try:
            prompt = f"""
            Convert this date expression to a date range.
            Reference date: {reference_date.strftime('%Y-%m-%d')}
            Date expression: "{date_expression}"
            
            Return JSON with:
            - start_date: YYYY-MM-DD format
            - end_date: YYYY-MM-DD format
            - description: human-readable explanation
            
            Return only JSON.
            """
            
            response = self.model.generate_content(prompt)
            date_range = json.loads(response.text)
            
            logger.info(f"Gemini date normalization: {date_expression} -> {date_range}")
            return date_range
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {
                'start_date': None,
                'end_date': None,
                'description': 'Failed to parse date'
            }
    
    def generate_response(self, query: str, data: Dict, intent: str) -> str:
        """
        Use Gemini to generate natural language response
        """
        try:
            prompt = f"""
            Generate a friendly, natural language response for this leave query.
            
            Query: "{query}"
            Intent: {intent}
            Data: {json.dumps(data, indent=2)}
            
            Create a conversational response that clearly presents the information.
            Be helpful and concise.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"Found {len(data.get('leaves', []))} leave records."