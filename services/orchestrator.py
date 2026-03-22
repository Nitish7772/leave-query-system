from typing import Dict, Any, Optional
from datetime import date
import logging

from services.intent_service import IntentResult
from services.entity_service import EntityExtractor, ExtractedEntities
from services.date_normalizer import DateNormalizer, DateRange
from services.employee_service import EmployeeService
from services.leave_service import LeaveService
from models.employee import Employee
from utils.formatters import ResponseFormatter
from utils.validators import QueryValidator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """
    Main orchestrator for processing natural language queries.
    Manages the complete flow from input to response.
    """
    
    def __init__(self, intent_service, employee_service: EmployeeService, leave_service: LeaveService):
        self.intent_service = intent_service
        self.entity_extractor = EntityExtractor()
        self.date_normalizer = DateNormalizer()
        self.employee_service = employee_service
        self.leave_service = leave_service
        self.validator = QueryValidator()
        self.formatter = ResponseFormatter()
    
    def process_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """
        Main entry point for processing queries.
        Returns structured response.
        """
        try:
            logger.info(f"Processing query: '{query}' for user: {user_id}")
            
            # Step 1: Validate input
            is_valid, error_msg = self.validator.validate_query(query)
            if not is_valid:
                logger.warning(f"Invalid query: {error_msg}")
                return self.formatter.error_response(error_msg, error_code="INVALID_QUERY")
            
            # Step 2: Detect intent
            intent_result = self.intent_service.detect_intent(query)
            logger.info(f"Detected intent: {intent_result.intent} (confidence: {intent_result.confidence})")
            
            # Step 3: Extract entities
            entities = self.entity_extractor.extract(query)
            logger.info(f"Extracted entities: employee={entities.employee_name}, date_range={entities.date_range_expr}, leave_type={entities.leave_type}")
            
            # Step 4: Resolve employee
            employee, resolution_status = self.employee_service.resolve_employee(
                entities.employee_name, 
                user_id
            )
            
            logger.info(f"Employee resolution status: {resolution_status}, employee: {employee.name if employee else 'None'}")
            
            # Handle different resolution outcomes
            if resolution_status == 'not_found':
                logger.warning(f"Employee not found: {entities.employee_name}")
                # Get list of available employees for helpful error message
                available_employees = self.employee_service.get_all_employees()
                employee_names = [emp.name for emp in available_employees]
                
                return self.formatter.error_response(
                    f"Employee '{entities.employee_name}' not found in the system.",
                    error_code="EMPLOYEE_NOT_FOUND",
                    details={
                        "available_employees": employee_names,
                        "suggestion": "Please use one of the available employee names or ask about 'my' leaves."
                    }
                )
            
            elif resolution_status == 'ambiguous':
                logger.warning(f"Ambiguous employee name: {entities.employee_name}")
                matches = self.employee_service.search_employees(entities.employee_name)
                match_names = [emp.name for emp in matches]
                
                return self.formatter.error_response(
                    f"Multiple employees found matching '{entities.employee_name}'.",
                    error_code="AMBIGUOUS_EMPLOYEE",
                    details={
                        "matches": match_names,
                        "suggestion": "Please specify the full name."
                    }
                )
            
            elif resolution_status == 'context':
                logger.info(f"Using context user: {employee.name}")
            
            elif resolution_status == 'partial_match':
                logger.info(f"Found partial match: {employee.name} for '{entities.employee_name}'")
            
            elif resolution_status == 'success':
                logger.info(f"Found exact match: {employee.name}")
            
            if not employee:
                return self.formatter.error_response(
                    "Unable to identify employee. Please specify a valid employee name.",
                    error_code="EMPLOYEE_RESOLUTION_FAILED"
                )
            
            # Step 5: Normalize date range
            date_range = None
            if entities.date_range_expr:
                date_range = self.date_normalizer.normalize(entities.date_range_expr)
                if date_range:
                    logger.info(f"Normalized date range: {date_range.start_date} to {date_range.end_date}")
                else:
                    logger.warning(f"Could not normalize date expression: {entities.date_range_expr}")
            
            # Step 6: Execute based on intent
            result = self._execute_intent(
                intent=intent_result.intent,
                employee=employee,
                date_range=date_range,
                leave_type=entities.leave_type,
                query=query
            )
            
            # Step 7: Format and return response
            logger.info(f"Query processed successfully, intent: {intent_result.intent}")
            return self.formatter.success_response(result)
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return self.formatter.error_response(
                f"An error occurred while processing your request: {str(e)}",
                error_code="PROCESSING_ERROR"
            )
    
    def _execute_intent(self, intent: str, employee: Employee, 
                        date_range: Optional[DateRange], 
                        leave_type: Optional[str],
                        query: str) -> Dict:
        """Execute the appropriate action based on intent"""
        
        logger.info(f"Executing intent: {intent} for employee: {employee.name}")
        
        if intent == 'leave_balance':
            return self._handle_balance_query(employee, leave_type)
        
        elif intent == 'leave_history':
            return self._handle_history_query(employee, date_range, leave_type)
        
        elif intent == 'leave_status':
            return self._handle_status_query(employee)
        
        elif intent == 'leave_request':
            return self._handle_request_query(employee, query)
        
        else:
            # Fallback with helpful suggestions
            logger.warning(f"Unknown intent: {intent}, providing help")
            return {
                'message': "I understand you're asking about leaves, but I need more specific information.",
                'help': "You can ask about: leave balance, leave history, or leave status",
                'examples': [
                    "Show my leave balance",
                    "What leaves did Soumya take last month?",
                    "Leave history for Nitish Kumar",
                    "How many sick leaves do I have?",
                    "Status of my leave requests"
                ],
                'your_query': query
            }
    
    def _handle_balance_query(self, employee: Employee, leave_type: Optional[str]) -> Dict:
        """Handle leave balance queries"""
        logger.info(f"Handling balance query for {employee.name}, type: {leave_type}")
        
        balance = self.leave_service.get_leave_balance(employee.id, leave_type)
        
        if leave_type:
            return {
                'employee': employee.name,
                'employee_id': employee.id,
                'leave_type': leave_type,
                'balance': balance['balance'],
                'message': f"{employee.name} has {balance['balance']} {leave_type} leaves remaining."
            }
        else:
            # Format balance nicely
            balances = balance['balances']
            balance_text = ", ".join([f"{k}: {v}" for k, v in balances.items()])
            
            return {
                'employee': employee.name,
                'employee_id': employee.id,
                'balances': balances,
                'message': f"Leave balance for {employee.name}: {balance_text}"
            }
    
    def _handle_history_query(self, employee: Employee, 
                               date_range: Optional[DateRange],
                               leave_type: Optional[str]) -> Dict:
        """Handle leave history queries"""
        logger.info(f"Handling history query for {employee.name}, date_range: {date_range}, type: {leave_type}")
        
        leaves = self.leave_service.get_leave_history(
            employee.id, date_range, leave_type
        )
        
        # Filter out cancelled leaves (already handled in service)
        active_leaves = [l for l in leaves if l['status'] != 'cancelled']
        
        # Build response
        response = {
            'employee': employee.name,
            'employee_id': employee.id,
            'total_leaves': len(active_leaves),
            'leaves': active_leaves
        }
        
        if date_range:
            response['date_range'] = date_range.to_dict()
        
        if leave_type:
            response['leave_type'] = leave_type
        
        if active_leaves:
            total_days = sum(l['days'] for l in active_leaves)
            response['total_days'] = total_days
            
            # Create a more descriptive message
            if date_range:
                response['message'] = f"Found {len(active_leaves)} leave records for {employee.name} from {date_range.start_date} to {date_range.end_date}"
            else:
                response['message'] = f"Found {len(active_leaves)} leave records for {employee.name}"
        else:
            if date_range:
                response['message'] = f"No leave records found for {employee.name} in the specified date range"
            else:
                response['message'] = f"No leave records found for {employee.name}"
        
        return response
    
    def _handle_status_query(self, employee: Employee) -> Dict:
        """Handle leave status queries"""
        logger.info(f"Handling status query for {employee.name}")
        
        status = self.leave_service.get_leave_status(employee.id)
        
        if status['pending_count'] > 0:
            message = f"You have {status['pending_count']} pending leave requests."
        elif status['approved_count'] > 0:
            message = f"You have {status['approved_count']} approved leaves."
        else:
            message = "No pending or recent leave requests found."
        
        return {
            'employee': employee.name,
            'employee_id': employee.id,
            'pending_requests': status['pending_count'],
            'approved_requests': status['approved_count'],
            'recent_requests': status['recent_requests'],
            'message': message
        }
    
    def _handle_request_query(self, employee: Employee, query: str) -> Dict:
        """Handle leave request queries"""
        logger.info(f"Handling request query for {employee.name}")
        
        # This would integrate with a leave request system
        return {
            'message': "Leave request functionality is integrated with HR system.",
            'note': "Please use the HR portal to submit leave requests.",
            'employee': employee.name,
            'employee_id': employee.id,
            'your_request': query
        }