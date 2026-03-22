# Leave Query System

A production-ready natural language query system for employee leave management. The system interprets natural language requests and returns accurate leave information using deterministic rules and structured processing.

## Features

- 🎯 **Intent Detection**: Classifies queries into balance, history, status, or request intents
- 🔍 **Entity Extraction**: Extracts employees, dates, leave types from natural language
- 📅 **Date Normalization**: Converts expressions like "last month", "March 15-20" to standardized date ranges
- 👥 **Employee Resolution**: Resolves names to employee records with fuzzy matching
- 🚫 **Exclusion Logic**: Automatically filters out cancelled and invalid leave records
- 📊 **Structured Responses**: Returns clean, consistent JSON responses
- 🧪 **Testable Design**: Deterministic logic makes testing straightforward

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd leave-query-system

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py