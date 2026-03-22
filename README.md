# 🏢 Leave Query System

A natural language query system for employee leave management using deterministic rules + Google Gemini API.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🎯 Overview

Allows employees to query leave info using natural language:
- "What's my leave balance?"
- "How many sick leaves does Soumya have?"
- "Show leaves taken by Nitish last month"

---

## 🏗️ Architecture

| Component | Deterministic | Gemini AI |
|-----------|--------------|-----------|
| Intent Detection | ✅ Keyword + regex | 🔄 Fallback for ambiguous |
| Entity Extraction | ✅ Pattern matching | 🔄 Complex name variations |
| Date Normalization | ✅ Calendar math (12+ patterns) | 🔄 Novel expressions |
| Employee Resolution | ✅ Fuzzy DB lookup | ❌ Not used |
| Response Generation | ✅ Template-based | 🔄 Natural language |

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3.8+ | Core logic |
| Web Framework | Flask | API & Web UI |
| NLP | Deterministic + Google Gemini | Intent & entity extraction |
| Date Processing | datetime, python-dateutil | Date calculations |
| Frontend | HTML/CSS/JS | User interface |

---

## 🔄 Query Flow

```
INPUT: "What leaves did Soumya take last month?"
   │
   ├─ 1. Intent Detection   → leave_history (confidence: 0.95)
   ├─ 2. Entity Extraction  → Employee: "Soumya", Date: "last month"
   ├─ 3. Employee Resolution → "Soumya" → "Soumya Gorla" (EMP001)
   ├─ 4. Date Normalization  → (2024-02-01, 2024-02-29)
   ├─ 5. DB Query           → WHERE employee_id='EMP001' AND date BETWEEN ...
   └─ 6. Response           → { "employee": "Soumya Gorla", "total_leaves": 1, ... }
```

---

## 📦 Installation

```bash
git clone https://github.com/Nitish7772/leave-query-system.git
cd leave-query-system
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Optional — Set Gemini API key:**
```bash
export GEMINI_API_KEY="your-api-key-here"   # Linux/Mac
$env:GEMINI_API_KEY = "your-api-key-here"   # Windows
```

---

## 🚀 Running

```bash
python app.py
```
Visit: **http://localhost:5000**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| POST | `/api/query` | Process natural language query |
| GET | `/api/status` | Health check |
| GET | `/api/employees` | List all employees |

**Request:** `{ "query": "my leave balance", "user_id": "EMP002" }`

**Response:**
```json
{
  "status": "success",
  "data": {
    "employee": "Nitish Kumar",
    "employee_id": "EMP002",
    "balances": { "casual": 8, "sick": 12, "earned": 12, "compensatory": 3 }
  }
}
```

---

## 💬 Example Queries

| Query | Intent |
|-------|--------|
| "my leave balance" | Balance — current user |
| "leave balance soumya" | Balance — specific employee |
| "what leaves did soumya take last month?" | History — filtered by date |
| "status of my leave requests" | Status check |

---

## 📁 Project Structure

```
leave-query-system/
├── app.py
├── requirements.txt
├── services/         # intent, entity, date, employee, leave
├── utils/            # gemini_client, validators
├── models/           # employee, leave
└── tests/            # test_intent, test_dates, test_orchestrator
```

---

## 🧪 Testing

```bash
pytest tests/ -v
pytest --cov=. tests/
```

---

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| Module not found | `pip install -r requirements.txt` |
| Port 5000 in use | `lsof -i :5000` → `kill -9 <PID>` |
| Gemini API failing | Set `USE_GEMINI_API=false` |
| Employee not found | Use full name e.g. `"Soumya Gorla"` |

---

## 📄 License

MIT License — **Author:** Nitish Kumar · [@Nitish7772](https://github.com/Nitish7772)
