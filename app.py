from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime, date, timedelta
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['DEBUG'] = True
CORS(app)

# ============= MOCK DATA =============
EMPLOYEES = {
    "EMP001": {"id": "EMP001", "name": "Soumya Gorla", "email": "soumya@infoteck.solutions", "department": "Engineering"},
    "EMP002": {"id": "EMP002", "name": "Nitish Kumar", "email": "nitish@infoteck.solutions", "department": "Engineering"},
    "EMP003": {"id": "EMP003", "name": "Pranith Nethikunta", "email": "pranith@infoteck.solutions", "department": "Product"},
    "EMP004": {"id": "EMP004", "name": "Manoj Kumar", "email": "manoj@infoteck.solutions", "department": "HR"},
    "EMP005": {"id": "EMP005", "name": "Kiran Reddy", "email": "kiran@infoteck.solutions", "department": "Sales"}
}

LEAVE_BALANCES = {
    "EMP001": {"casual": 12, "sick": 10, "earned": 15, "compensatory": 5},
    "EMP002": {"casual": 8, "sick": 12, "earned": 12, "compensatory": 3},
    "EMP003": {"casual": 10, "sick": 8, "earned": 20, "compensatory": 4},
    "EMP004": {"casual": 15, "sick": 12, "earned": 10, "compensatory": 2},
    "EMP005": {"casual": 9, "sick": 10, "earned": 14, "compensatory": 3}
}

LEAVE_HISTORY = {
    "EMP001": [
        {"id": "L001", "type": "casual", "start_date": "2024-01-10", "end_date": "2024-01-12", "status": "approved", "days": 3, "reason": "Family function"},
        {"id": "L002", "type": "sick", "start_date": "2024-02-05", "end_date": "2024-02-06", "status": "approved", "days": 2, "reason": "Fever"},
    ],
    "EMP002": [
        {"id": "L004", "type": "casual", "start_date": "2024-01-20", "end_date": "2024-01-22", "status": "approved", "days": 3, "reason": "Personal work"},
        {"id": "L005", "type": "sick", "start_date": "2024-02-15", "end_date": "2024-02-16", "status": "approved", "days": 2, "reason": "Medical appointment"},
    ],
    "EMP003": [
        {"id": "L008", "type": "casual", "start_date": "2024-01-05", "end_date": "2024-01-08", "status": "cancelled", "days": 4, "reason": "Plan changed"},
        {"id": "L009", "type": "earned", "start_date": "2024-02-10", "end_date": "2024-02-15", "status": "approved", "days": 6, "reason": "Long weekend"},
    ],
    "EMP004": [
        {"id": "L010", "type": "casual", "start_date": "2024-02-20", "end_date": "2024-02-22", "status": "approved", "days": 3, "reason": "Wedding"},
    ],
    "EMP005": [
        {"id": "L011", "type": "sick", "start_date": "2024-01-15", "end_date": "2024-01-17", "status": "approved", "days": 3, "reason": "Cold and fever"},
    ]
}

# ============= SERVICES =============

class IntentService:
    def detect_intent(self, query):
        query_lower = query.lower()
        if any(word in query_lower for word in ['balance', 'remaining', 'left', 'available']):
            return 'leave_balance'
        elif any(word in query_lower for word in ['history', 'taken', 'previous', 'past']):
            return 'leave_history'
        elif any(word in query_lower for word in ['status', 'pending', 'approved']):
            return 'leave_status'
        return 'unknown'


class EntityExtractor:
    def extract(self, query):
        entities = {
            'employee_name': None,
            'date_range_expr': None,
            'leave_type': None,
            'status': None
        }
        
        query_original = query
        query_lower = query.lower()
        
        # ============= EXTRACT EMPLOYEE NAME =============
        # Known employees (case-insensitive)
        known_employees = {
            'soumya': 'Soumya Gorla',
            'soumya gorla': 'Soumya Gorla',
            'gorla': 'Soumya Gorla',
            'nitish': 'Nitish Kumar',
            'nitish kumar': 'Nitish Kumar',
            'pranith': 'Pranith Nethikunta',
            'pranith nethikunta': 'Pranith Nethikunta',
            'manoj': 'Manoj Kumar',
            'manoj kumar': 'Manoj Kumar',
            'kiran': 'Kiran Reddy',
            'kiran reddy': 'Kiran Reddy'
        }
        
        # Common words to ignore
        common_words = {'my', 'me', 'leave', 'balance', 'history', 'status', 'show', 
                       'list', 'get', 'for', 'the', 'what', 'how', 'many', 'does', 
                       'have', 'last', 'month', 'week', 'year', 'this', 'next', 
                       'march', 'january', 'february', 'casual', 'sick', 'earned', 
                       'compensatory', 'pending', 'approved', 'take', 'taken', 'in',
                       'from', 'to', 'on', 'at', 'by', 'of', 'and', 'or'}
        
        # First, check if query is about "my" leaves
        if re.search(r'\bmy\b|\bmine\b|\bme\b', query_lower):
            entities['employee_name'] = None
        else:
            # Check for known employee names first
            found = False
            for name_key, full_name in known_employees.items():
                if name_key in query_lower:
                    entities['employee_name'] = full_name
                    found = True
                    break
            
            # If not found, look for any word that might be a name
            if not found:
                words = query_lower.split()
                potential_names = []
                
                for word in words:
                    # Clean the word
                    clean_word = word.strip('.,!?;:')
                    
                    # Check if it could be a name
                    if (len(clean_word) > 2 and 
                        clean_word not in common_words and
                        not clean_word.isdigit()):
                        potential_names.append(clean_word)
                
                # If we found potential names, take the first one
                if potential_names:
                    # Capitalize it for display
                    entities['employee_name'] = potential_names[0].capitalize()
        
        logger.info(f"Extracted employee name: '{entities['employee_name']}'")
        
        # ============= EXTRACT DATE RANGE =============
        if 'last month' in query_lower:
            entities['date_range_expr'] = 'last month'
        elif 'this month' in query_lower:
            entities['date_range_expr'] = 'this month'
        elif 'last week' in query_lower:
            entities['date_range_expr'] = 'last week'
        elif 'this week' in query_lower:
            entities['date_range_expr'] = 'this week'
        elif 'march' in query_lower:
            entities['date_range_expr'] = 'march'
        
        # ============= EXTRACT LEAVE TYPE =============
        leave_types = ['casual', 'sick', 'earned', 'compensatory']
        for lt in leave_types:
            if lt in query_lower:
                entities['leave_type'] = lt
                break
        
        return entities


class DateNormalizer:
    def __init__(self):
        self.reference_date = date.today()
    
    def normalize(self, date_expr):
        if not date_expr:
            return None
        
        class DateRange:
            def __init__(self, start, end):
                self.start_date = start
                self.end_date = end
            def to_dict(self):
                return {'start_date': self.start_date.isoformat(), 'end_date': self.end_date.isoformat()}
        
        if date_expr == 'last month':
            first_day = (self.reference_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_day = self.reference_date.replace(day=1) - timedelta(days=1)
            return DateRange(first_day, last_day)
        
        elif date_expr == 'this month':
            first_day = self.reference_date.replace(day=1)
            if self.reference_date.month == 12:
                last_day = self.reference_date.replace(year=self.reference_date.year+1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = self.reference_date.replace(month=self.reference_date.month+1, day=1) - timedelta(days=1)
            return DateRange(first_day, last_day)
        
        elif date_expr == 'last week':
            end_date = self.reference_date - timedelta(days=self.reference_date.weekday() + 1)
            start_date = end_date - timedelta(days=6)
            return DateRange(start_date, end_date)
        
        elif date_expr == 'this week':
            start_date = self.reference_date - timedelta(days=self.reference_date.weekday())
            end_date = start_date + timedelta(days=6)
            return DateRange(start_date, end_date)
        
        elif date_expr == 'march':
            start_date = date(self.reference_date.year, 3, 1)
            end_date = date(self.reference_date.year, 3, 31)
            return DateRange(start_date, end_date)
        
        return None


class EmployeeService:
    def __init__(self):
        self.employees = EMPLOYEES
    
    def resolve_employee(self, employee_name, context_user_id):
        # Case 1: No employee specified
        if not employee_name or employee_name.lower() in ['my', 'me', 'mine', '']:
            employee = self.employees.get(context_user_id)
            if employee:
                return employee, 'context'
            return None, 'context_user_not_found'
        
        # Case 2: Try exact match (case-insensitive)
        employee_name_lower = employee_name.lower()
        for emp_id, emp in self.employees.items():
            if emp['name'].lower() == employee_name_lower:
                return emp, 'success'
        
        # Case 3: Try partial match
        for emp_id, emp in self.employees.items():
            if employee_name_lower in emp['name'].lower():
                return emp, 'partial'
            elif any(employee_name_lower == part.lower() for part in emp['name'].split()):
                return emp, 'partial'
        
        # Case 4: No matches
        return None, 'not_found'
    
    def get_all_employees(self):
        return list(self.employees.values())


class LeaveService:
    def __init__(self):
        self.balances = LEAVE_BALANCES
        self.history = LEAVE_HISTORY
    
    def get_leave_balance(self, employee_id, leave_type=None):
        balances = self.balances.get(employee_id, {})
        if leave_type:
            return {
                'employee_id': employee_id,
                'leave_type': leave_type,
                'balance': balances.get(leave_type, 0)
            }
        return {
            'employee_id': employee_id,
            'balances': balances
        }
    
    def get_leave_history(self, employee_id, date_range=None, leave_type=None):
        leaves = self.history.get(employee_id, [])
        
        if date_range:
            filtered = []
            for leaf in leaves:
                try:
                    leaf_date = date.fromisoformat(leaf['start_date'])
                    if date_range.start_date <= leaf_date <= date_range.end_date:
                        filtered.append(leaf)
                except:
                    filtered.append(leaf)
            leaves = filtered
        
        if leave_type:
            leaves = [l for l in leaves if l['type'] == leave_type]
        
        leaves = [l for l in leaves if l['status'] != 'cancelled']
        return leaves


# Initialize services
intent_service = IntentService()
entity_extractor = EntityExtractor()
date_normalizer = DateNormalizer()
employee_service = EmployeeService()
leave_service = LeaveService()


# ============= ROUTES =============

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Leave Query System</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                width: 100%;
                max-width: 700px;
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 { font-size: 28px; margin-bottom: 10px; }
            .header p { opacity: 0.9; font-size: 14px; }
            .content { padding: 30px; }
            .query-section { margin-bottom: 30px; }
            .input-group { display: flex; gap: 10px; margin-bottom: 10px; }
            .query-input {
                flex: 1;
                padding: 12px 16px;
                font-size: 16px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                outline: none;
                transition: border-color 0.3s;
            }
            .query-input:focus { border-color: #667eea; }
            .submit-btn {
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .result-section {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                min-height: 200px;
            }
            .result-title {
                font-weight: 600;
                margin-bottom: 15px;
                color: #333;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .result-content {
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 13px;
                line-height: 1.6;
                color: #333;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .loading {
                color: #667eea;
                text-align: center;
                padding: 40px;
                animation: pulse 1.5s ease-in-out infinite;
            }
            .error {
                color: #dc3545;
                background: #ffe6e6;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #dc3545;
            }
            .success {
                color: #28a745;
                background: #e6ffe6;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #28a745;
            }
            .footer {
                background: #f8f9fa;
                padding: 15px 30px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-top: 1px solid #e0e0e0;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1> Leave Query System</h1>
                <p>Natural language leave management</p>
            </div>
            <div class="content">
                <div class="query-section">
                    <div class="input-group">
                        <input type="text" id="query" class="query-input" 
                               placeholder="e.g., leave balance soumya, leave balance dheeraj, my leave balance"
                               autofocus>
                        <button id="submitBtn" class="submit-btn">Ask</button>
                    </div>
                </div>
                <div class="result-section">
                    <div class="result-title">Response</div>
                    <div id="result" class="result-content">
                        <div style="color: #999; text-align: center; padding: 40px;">
                            Enter a query to get started
                        </div>
                    </div>
                </div>
            </div>
            <div class="footer">
                Powered by Deterministic NLP
            </div>
        </div>
        
        <script>
            const DEFAULT_USER_ID = 'EMP002';
            
            async function submitQuery() {
                const query = document.getElementById('query').value.trim();
                if (!query) {
                    alert('Please enter a query');
                    return;
                }
                
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<div class="loading"> Processing your query...</div>';
                document.getElementById('submitBtn').disabled = true;
                
                try {
                    const response = await fetch('/api/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query, user_id: DEFAULT_USER_ID })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        resultDiv.innerHTML = `
                            <div class="success"> Query processed successfully</div>
                            <pre style="background: white; padding: 15px; border-radius: 8px; margin-top: 15px; overflow-x: auto;">${escapeHtml(JSON.stringify(data.data, null, 2))}</pre>
                        `;
                    } else {
                        let errorHtml = `<div class="error"> ${escapeHtml(data.error.message)}</div>`;
                        if (data.error.details) {
                            errorHtml += `<pre style="background: white; padding: 15px; border-radius: 8px; margin-top: 15px;">${escapeHtml(JSON.stringify(data.error.details, null, 2))}</pre>`;
                        }
                        resultDiv.innerHTML = errorHtml;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="error"> Error: ${escapeHtml(error.message)}</div>`;
                } finally {
                    document.getElementById('submitBtn').disabled = false;
                }
            }
            
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            document.getElementById('submitBtn').addEventListener('click', submitQuery);
            document.getElementById('query').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') submitQuery();
            });
            
            document.getElementById('query').focus();
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/api/query', methods=['POST'])
def process_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        user_id = data.get('user_id', 'EMP002')
        
        logger.info(f"Processing query: '{query}'")
        
        # Step 1: Detect intent
        intent = intent_service.detect_intent(query)
        logger.info(f"Intent: {intent}")
        
        # Step 2: Extract entities
        entities = entity_extractor.extract(query)
        
        # Step 3: Resolve employee
        employee, resolution_status = employee_service.resolve_employee(entities['employee_name'], user_id)
        
        if not employee:
            available = employee_service.get_all_employees()
            employee_names = [e['name'] for e in available]
            
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'EMPLOYEE_NOT_FOUND',
                    'message': f"Employee '{entities['employee_name']}' not found in the system.",
                    'details': {
                        'available_employees': employee_names,
                        'suggestion': 'Please use one of the available employee names or ask about "my" leaves.'
                    }
                }
            })
        
        logger.info(f"Resolved employee: {employee['name']}")
        
        # Step 4: Normalize date range
        date_range = None
        if entities['date_range_expr']:
            date_range = date_normalizer.normalize(entities['date_range_expr'])
        
        # Step 5: Execute based on intent
        if intent == 'leave_balance':
            result = leave_service.get_leave_balance(employee['id'], entities['leave_type'])
            result['employee'] = employee['name']
            result['employee_id'] = employee['id']
            
            if 'leave_type' in result:
                result['message'] = f"{employee['name']} has {result['balance']} {result['leave_type']} leaves remaining."
            else:
                balances = result['balances']
                balance_text = ", ".join([f"{k}: {v}" for k, v in balances.items()])
                result['message'] = f"Leave balance for {employee['name']}: {balance_text}"
        
        elif intent == 'leave_history':
            leaves = leave_service.get_leave_history(employee['id'], date_range, entities['leave_type'])
            result = {
                'employee': employee['name'],
                'employee_id': employee['id'],
                'total_leaves': len(leaves),
                'leaves': leaves
            }
            if date_range:
                result['date_range'] = date_range.to_dict()
            
            if leaves:
                result['message'] = f"Found {len(leaves)} leave records for {employee['name']}"
            else:
                result['message'] = f"No leave records found for {employee['name']}"
        
        else:
            result = {
                'message': "I understand you're asking about leaves, but I need more specific information.",
                'help': "You can ask about: leave balance, leave history, or leave status"
            }
        
        return jsonify({'status': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': {'message': str(e)}
        }), 500


@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        'status': 'healthy',
        'employees': len(EMPLOYEES),
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print(" Leave Query System Starting...")
    print("="*60)
    print(f" Available Employees: {len(EMPLOYEES)}")
    for emp in EMPLOYEES.values():
        print(f"   - {emp['name']}")
    print("\n Test Queries:")
    print("   - leave balance soumya (uppercase) - should work")
    print("   - leave balance soumya (lowercase) - should work")
    print("   - leave balance dheeraj (uppercase) - should show error")
    print("   - leave balance dheeraj (lowercase) - should show error")
    print("   - my leave balance - shows Nitish's balance")
    print("\n System ready! Visit http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)