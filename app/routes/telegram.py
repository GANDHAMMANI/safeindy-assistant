"""
Telegram webhook route for SafeIndy Assistant
Handles incoming Telegram updates via webhook
"""

from flask import Blueprint, request, jsonify
import json
import asyncio
from telegram import Update

from app.services.telegram_service import TelegramService

# Create blueprint
telegram_bp = Blueprint('telegram', __name__)

# Initialize telegram service
telegram_service = TelegramService()
telegram_service.initialize_bot()

@telegram_bp.route('/webhook/<token>', methods=['POST'])
def telegram_webhook(token):
    """Handle Telegram webhook updates"""
    try:
        # Verify token
        expected_token = "7513970628:AAHDVuD8kOHQcIr9tyPt52VG5GhF5Sp5vyo"
        if token != expected_token:
            return jsonify({'error': 'Invalid token'}), 403
        
        # Get update data
        update_data = request.get_json()
        
        if not update_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Create Telegram Update object
        update = Update.de_json(update_data, telegram_service.application.bot)
        
        # Process update asynchronously
        asyncio.run(telegram_service.application.process_update(update))
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"❌ Telegram webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@telegram_bp.route('/set-webhook', methods=['POST'])
def set_webhook():
    """Set Telegram webhook URL"""
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            return jsonify({'error': 'webhook_url required'}), 400
        
        # Set webhook
        token = "7513970628:AAHDVuD8kOHQcIr9tyPt52VG5GhF5Sp5vyo"
        full_webhook_url = f"{webhook_url}/telegram/webhook/{token}"
        
        # This would set the webhook with Telegram
        # For now, return the URL to set manually
        return jsonify({
            'status': 'success',
            'webhook_url': full_webhook_url,
            'message': 'Use this URL to set webhook with Telegram'
        })
        
    except Exception as e:
        print(f"❌ Set webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@telegram_bp.route('/bot-info', methods=['GET'])
def bot_info():
    """Get bot information and status"""
    try:
        return jsonify({
            'bot_username': '@SafeIndyBot',
            'bot_url': 'https://t.me/SafeIndyBot',
            'status': 'active',
            'features': [
                'Emergency detection and alerts',
                'Location-based assistance',
                'Indianapolis city services',
                'Real-time AI responses',
                'Multilingual support',
                'Photo hazard reporting'
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500