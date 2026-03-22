import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Gemini API Configuration (Now from .env file)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-pro')
    
    # Use Gemini API for enhanced NLP
    USE_GEMINI_API = os.environ.get('USE_GEMINI_API', 'true').lower() == 'true'
    
    # Backend API Configuration
    BACKEND_API_URL = os.environ.get('BACKEND_API_URL', 'https://your-hr-system.com/api/v1')
    BACKEND_API_KEY = os.environ.get('BACKEND_API_KEY', '')
    BACKEND_API_TIMEOUT = int(os.environ.get('BACKEND_API_TIMEOUT', 30))
    
    # API Authentication
    API_AUTH_TYPE = os.environ.get('API_AUTH_TYPE', 'Bearer')
    API_USERNAME = os.environ.get('API_USERNAME', '')
    API_PASSWORD = os.environ.get('API_PASSWORD', '')
    
    # Use mock API if set to true (overrides API key)
    USE_MOCK_API = os.environ.get('USE_MOCK_API', 'false').lower() == 'true'
    
    # Date formats
    DATE_FORMAT = os.environ.get('DATE_FORMAT', '%Y-%m-%d')
    DATETIME_FORMAT = os.environ.get('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S')
    
    # Leave types - parse comma-separated string
    leave_types_str = os.environ.get('LEAVE_TYPES', 'casual,sick,earned,compensatory,vacation,annual')
    LEAVE_TYPES = [lt.strip() for lt in leave_types_str.split(',')]
    
    # Intent detection thresholds
    INTENT_CONFIDENCE_THRESHOLD = float(os.environ.get('INTENT_CONFIDENCE_THRESHOLD', 0.7))
    
    # Cache settings
    cache_ttl_minutes = int(os.environ.get('CACHE_TTL', 30))
    CACHE_TTL = timedelta(minutes=cache_ttl_minutes)
    
    # Pagination
    DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', 50))
    
    # Date range defaults
    DEFAULT_DATE_RANGE_DAYS = int(os.environ.get('DEFAULT_DATE_RANGE_DAYS', 30))
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration"""
        issues = []
        
        # Check if Gemini API is enabled but key is missing
        if cls.USE_GEMINI_API and not cls.GEMINI_API_KEY:
            issues.append("Gemini API is enabled but GEMINI_API_KEY is not set in .env file")
        
        # Check if using real API but key is missing
        if not cls.USE_MOCK_API and not cls.BACKEND_API_KEY:
            issues.append("Mock API is disabled but BACKEND_API_KEY is not set in .env file")
        
        return issues
    
    @classmethod
    def display_config(cls):
        """Display configuration status (hiding sensitive data)"""
        print("\n" + "="*60)
        print("📋 Configuration Status")
        print("="*60)
        print(f"🔧 Debug Mode: {cls.DEBUG}")
        print(f"🤖 Gemini API: {'✅ ENABLED' if cls.USE_GEMINI_API else '❌ DISABLED'}")
        if cls.GEMINI_API_KEY:
            masked_key = cls.GEMINI_API_KEY[:10] + '...' + cls.GEMINI_API_KEY[-4:] if len(cls.GEMINI_API_KEY) > 14 else '***'
            print(f"   API Key: {masked_key}")
        print(f"📡 Backend API: {'✅ REAL API' if not cls.USE_MOCK_API else '🔷 MOCK API'}")
        if not cls.USE_MOCK_API:
            print(f"   URL: {cls.BACKEND_API_URL}")
            if cls.BACKEND_API_KEY:
                masked_backend = cls.BACKEND_API_KEY[:8] + '...' if len(cls.BACKEND_API_KEY) > 8 else '***'
                print(f"   Key: {masked_backend}")
        print(f"📅 Date Format: {cls.DATE_FORMAT}")
        print(f"💾 Cache TTL: {cls.CACHE_TTL}")
        print("="*60 + "\n")
        
        # Validate configuration
        issues = cls.validate_config()
        if issues:
            print("⚠️ Configuration Issues:")
            for issue in issues:
                print(f"   - {issue}")
            print()