import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Application Info
    APP_NAME = os.environ.get('APP_NAME') or 'SafeIndy Assistant'
    APP_VERSION = os.environ.get('APP_VERSION') or '1.0.0'
    
    # API Keys - Core Services
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY') 
    COHERE_API_KEY = os.environ.get('COHERE_API_KEY')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    
    # Qdrant Vector Database Configuration
    QDRANT_URL = os.environ.get('QDRANT_URL') or 'http://localhost:6333'
    QDRANT_API_KEY = os.environ.get('QDRANT_API_KEY')
    QDRANT_COLLECTION_NAME = 'safeindy_knowledge'
    
    # Session Configuration (in-memory)
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
    # Indianapolis Specific Configuration
    INDY_TIMEZONE = 'America/Indiana/Indianapolis'
    INDY_COORDINATES = {'lat': 39.7684, 'lng': -86.1581}
    
    # Rate Limiting (to manage API costs)
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_CHAT_MESSAGES_PER_SESSION = 50
    
    # Emergency Contact Configuration
    EMERGENCY_NUMBERS = {
        'emergency': '911',
        'police_non_emergency': '317-327-3811',
        'mayors_action_center': '317-327-4622',
        'poison_control': '1-800-222-1222'
    }
    
    # Email Configuration for Emergency Alerts
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('EMERGENCY_EMAIL')  # Your Gmail address
    MAIL_PASSWORD = os.environ.get('EMERGENCY_EMAIL_PASSWORD')  # Your app password
    EMERGENCY_ALERT_EMAIL = os.environ.get('EMERGENCY_ALERT_EMAIL')  # Where to send alerts
    
    # Analytics Configuration
    ANALYTICS_ENABLED = os.environ.get('ANALYTICS_ENABLED', 'True').lower() == 'true'
    
    # Cache Configuration
    CACHE_TYPE = 'simple'  # In-memory cache
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    def validate_config():
        """Validate that required environment variables are set"""
        required_vars = [
            'GROQ_API_KEY',
            'PERPLEXITY_API_KEY', 
            'COHERE_API_KEY',
            'GOOGLE_MAPS_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    # Add production-specific settings here

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}