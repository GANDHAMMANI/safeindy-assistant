#!/usr/bin/env python3
"""
SafeIndy Assistant - Flask Application Runner
Main entry point for the SafeIndy public safety chatbot application.
"""

import os
from flask import Flask
from app import create_app
from app.config import Config

def main():
    """Main function to run the Flask application"""
    
    # Validate configuration before starting
    try:
        Config.validate_config()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please check your .env file and ensure all required API keys are set.")
        return
    
    # Create Flask application
    app = create_app()
    
    # Print startup information
    print(f"\n🚀 Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    print(f"🌍 Environment: {Config.FLASK_ENV}")
    print(f"🔧 Debug Mode: {Config.DEBUG}")
    print(f"📍 Indianapolis coordinates: {Config.INDY_COORDINATES}")
    print(f"🆘 Emergency number: {Config.EMERGENCY_NUMBERS['emergency']}")
    
    # Get host and port from environment or use defaults
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n🌐 Server starting on http://{host}:{port}")
    print("💬 Ready to serve Indianapolis residents!")
    print("=" * 50)
    
    # Run the application
    try:
        app.run(
            host=host,
            port=port,
            debug=Config.DEBUG,
            threaded=True  # Enable threading for better performance
        )
    except KeyboardInterrupt:
        print("\n\n👋 SafeIndy Assistant shutting down...")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")

if __name__ == '__main__':
    main()