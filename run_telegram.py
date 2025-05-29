"""
Standalone Telegram bot runner with Flask context
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app creation
from app import create_app
from app.services.telegram_service import TelegramService

def main():
    """Run the Telegram bot with Flask context"""
    print("🚀 Starting SafeIndy Telegram Bot...")
    
    # Create Flask app and context
    app = create_app()
    
    with app.app_context():
        print("✅ Flask application context created")
        
        telegram_service = TelegramService()
        
        if telegram_service.initialize_bot():
            print("✅ Bot initialized successfully")
            print("🤖 Bot is running at: https://t.me/SafeIndyBot")
            print("📱 Users can now message the bot!")
            print("🔄 All AI services should now work properly!")
            
            # Run with polling for development
            telegram_service.run_polling()
        else:
            print("❌ Failed to initialize bot")

if __name__ == "__main__":
    main()