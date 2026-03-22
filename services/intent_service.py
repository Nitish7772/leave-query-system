import re
import logging
from typing import Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IntentResult:
    intent: str
    confidence: float
    raw_text: str


class IntentService:
    """
    Hybrid intent detection:
    - Deterministic rules for common patterns (fast, reliable)
    - Gemini API for complex/ambiguous queries (enhanced understanding)
    """
    
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client
        
        # Deterministic patterns for common queries
        self.deterministic_patterns = {
            'leave_balance': [
                r'balance', r'remaining', r'left', r'available', r'how many',
                r'leave balance', r'leaves remaining'
            ],
            'leave_history': [
                r'history', r'taken', r'previous', r'past', r'what leaves',
                r'leave history', r'leaves taken'
            ],
            'leave_status': [
                r'status', r'pending', r'approved', r'check', r'track'
            ]
        }
    
    def detect_intent(self, query: str) -> IntentResult:
        """
        Detect intent using deterministic rules first, fallback to Gemini
        """
        query_lower = query.lower()
        
        # First try deterministic matching (fast path)
        for intent, patterns in self.deterministic_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.info(f"Deterministic match: {intent}")
                    return IntentResult(intent, 0.85, query)
        
        # If deterministic fails and Gemini is available, use it
        if self.gemini_client:
            try:
                logger.info("Using Gemini for intent detection")
                result = self.gemini_client.detect_intent(query)
                return IntentResult(
                    result.get('intent', 'unknown'),
                    result.get('confidence', 0.5),
                    query
                )
            except Exception as e:
                logger.error(f"Gemini intent detection failed: {e}")
        
        # Fallback
        return IntentResult('unknown', 0.0, query)