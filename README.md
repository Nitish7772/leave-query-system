# Leave Query System

A natural language query system for employee leave management using deterministic rules + Google Gemini API.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Overview

Allows employees to query leave info using natural language:
- "What's my leave balance?"
- "How many sick leaves does Soumya have?"
- "Show leaves taken by Nitish last month"

---

## Architecture

| Component | Deterministic | Gemini AI |
|-----------|--------------|-----------|
| Intent Detection | ✅ Keyword + regex | 🔄 Fallback for ambiguous |
| Entity Extraction | ✅ Pattern matching | 🔄 Complex name variations |
| Date Normalization | ✅ Calendar math (12+ patterns) | 🔄 Novel expressions |
| Employee Resolution | ✅ Fuzzy DB lookup | ❌ Not used |
| Response Generation | ✅ Template-based | 🔄 Natural language |

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3.8+ | Core logic |
| Web Framework | Flask | API & Web UI |
| NLP | Deterministic + Google Gemini | Intent & entity extraction |
| Date Processing | datetime, python-dateutil | Date calculations |
| Frontend | HTML/CSS/JS | User interface |

---

## Query Flow

```
┌─────────────────────────────────────────────────────────────┐
│     INPUT: "What leaves did Soumya take last month?"        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Intent Detection                                   │
│  Keywords: "what leaves", "take", "last month"              │
│  Result: leave_history (confidence: 0.95)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Entity Extraction                                  │
│  Employee: "Soumya" → Pattern: r'for (\w+)'                 │
│  Date Range: "last month" → Date pattern detected           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Employee Resolution                                │
│  "Soumya" → "Soumya Gorla" (EMP001) — exact match          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Date Normalization                                 │
│  "last month" → (2024-02-01, 2024-02-29)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: DB Query & Filter                                  │
│  WHERE employee_id = 'EMP001'                               │
│  AND start_date >= '2024-02-01'                             │
│  AND end_date <= '2024-02-29'                               │
│  AND status NOT IN ('cancelled', 'rejected')                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: Response                                           │
│  { "employee": "Soumya Gorla", "total_leaves": 1,           │
│    "leaves": [{ "type": "sick", "days": 2,                  │
│    "status": "approved" }] }                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

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

## Running

```bash
python app.py