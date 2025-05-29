"""
SafeIndy Assistant Flask Application Factory

This module creates and configures the Flask application instance.
"""

from flask import Flask
from flask_cors import CORS
from flask_session import Session
from app.config import config
import os

def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Create Flask application instance
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config.get(config_name, config['default']))
    
    # Enable CORS for API endpoints
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/chat/*": {"origins": "*"}
    })
    
    # Initialize session management
    Session(app)
    
    # Initialize extensions here (Qdrant will be initialized in services)
    # No traditional database needed
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add context processors for templates
    register_context_processors(app)
    
    return app

def register_blueprints(app):
    """Register Flask blueprints"""
    
    # Import blueprints
    from app.routes.main import main_bp
    from app.routes.chat import chat_bp
    from app.routes.emergency import emergency_bp
    from app.routes.community import community_bp
    from app.routes.api import api_bp
    from app.routes.telegram import telegram_bp
    # Register blueprints with URL prefixes
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(emergency_bp, url_prefix='/emergency')  
    app.register_blueprint(community_bp, url_prefix='/community')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(telegram_bp, url_prefix='/telegram')

def register_error_handlers(app):
    """Register custom error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {
            'error': 'Page not found',
            'message': 'The requested resource was not found on this server.',
            'status': 404
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.',
            'status': 500
        }, 500
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return {
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again in a moment.',
            'status': 429
        }, 429

def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_config():
        """Inject configuration variables into templates"""
        return {
            'APP_NAME': app.config['APP_NAME'],
            'APP_VERSION': app.config['APP_VERSION'],
            'EMERGENCY_NUMBERS': app.config['EMERGENCY_NUMBERS'],
            'GOOGLE_MAPS_API_KEY': app.config['GOOGLE_MAPS_API_KEY']
        }
    
    @app.context_processor
    def inject_utils():
        """Inject utility functions into templates"""
        from datetime import datetime
        now = datetime.now()
        
        return {
            'now': now,
            'year': now.year,
            'current_time': now.strftime('%I:%M %p')
        }