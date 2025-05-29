"""
FIXED Telegram Service for SafeIndy Assistant
Handles Telegram Bot API integration with proper formatting
"""

import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime
import json
import re

from .rag_service import RAGService
from .notification_service import NotificationService

class TelegramService:
    def __init__(self):
        self.token = "7513970628:AAHDVuD8kOHQcIr9tyPt52VG5GhF5Sp5vyo"
        self.rag_service = RAGService()
        self.notification_service = NotificationService()
        self.application = None
        self.active_sessions = {}  # Store user sessions
        
    def initialize_bot(self):
        """Initialize the Telegram bot application"""
        try:
            self.application = Application.builder().token(self.token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("emergency", self.emergency_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            self.application.add_handler(MessageHandler(filters.LOCATION, self.handle_location))
            self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            print("✅ Telegram bot initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Telegram bot: {e}")
            return False
    
    def format_for_telegram(self, text: str) -> str:
        """
        Format text for Telegram - remove HTML tags and fix formatting
        """
        if not text:
            return text
        
        # Remove HTML tags that Telegram doesn't support
        text = re.sub(r'<br\s*/?>', '\n', text)  # Convert <br> to newlines
        text = re.sub(r'</?div[^>]*>', '\n', text)  # Convert divs to newlines
        text = re.sub(r'</?p[^>]*>', '\n', text)   # Convert paragraphs to newlines
        
        # Keep only supported HTML tags for Telegram
        # Telegram supports: <b>, <strong>, <i>, <em>, <u>, <s>, <code>, <pre>, <a>
        
        # Convert unsupported tags to Telegram markdown
        text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'*\1*', text)  # Headers to bold
        
        # Remove any other HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up extra newlines
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 consecutive newlines
        text = text.strip()
        
        return text
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = str(user.id)
        
        # Initialize user session
        self.active_sessions[user_id] = {
            'user_id': user_id,
            'username': user.username or user.first_name,
            'chat_history': [],
            'location': None,
            'started_at': datetime.now().isoformat()
        }
        
        welcome_message = """🛡️ *Welcome to SafeIndy Assistant!*

I'm your AI-powered safety companion for Indianapolis. I can help you with:

🚨 *Emergency Services* - Get help and contact information
🏛️ *City Services* - Report issues, find resources  
📍 *Local Information* - Hospitals, police stations, city offices
🌤️ *Weather & Alerts* - Current conditions and warnings

*Quick Commands:*
• Type your question naturally
• Use /emergency for immediate help
• Share your location for better assistance
• Send photos to report hazards

*For life-threatening emergencies, always call 911 first!*

How can I help you today?"""

        # Create quick action keyboard
        keyboard = [
            [KeyboardButton("🚨 Emergency Help"), KeyboardButton("🏥 Find Hospital")],
            [KeyboardButton("👮 Police Services"), KeyboardButton("🌤️ Weather")],
            [KeyboardButton("📍 Share Location"), KeyboardButton("❓ Help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """🆘 *SafeIndy Assistant Help*

*How to Use:*
• Just type your questions naturally
• I understand multiple languages
• Share your location for better help

*Emergency Commands:*
• /emergency - Immediate emergency assistance
• Type "emergency" or "help" - Auto-detected

*What I Can Help With:*
• Emergency contact information
• Reporting city issues (potholes, etc.)
• Finding hospitals, police stations
• Weather alerts and information
• City services and resources

*Examples:*
• "I need help with an emergency"
• "How do I report a pothole?"
• "Where's the nearest hospital?"
• "What's the weather like?"

🚨 *IMPORTANT: For life-threatening emergencies, call 911 immediately!*

Need specific help? Just ask me anything!"""

        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def emergency_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /emergency command"""
        user_id = str(update.effective_user.id)
        
        emergency_message = """🚨 *EMERGENCY ASSISTANCE*

*FOR IMMEDIATE LIFE-THREATENING EMERGENCIES:*
📞 *CALL 911 NOW*

*Indianapolis Emergency Contacts:*
• *Emergency:* 911 (call or text)
• *Police Non-Emergency:* 317-327-3811
• *Poison Control:* 1-800-222-1222

*What's your emergency?*
Type your situation and I'll provide specific guidance and alert authorities if needed.

*Share your location* for faster emergency response."""

        # Emergency action buttons (removed invalid tel: URLs)
        keyboard = [
            [InlineKeyboardButton("📞 Emergency Numbers", callback_data="emergency_numbers")],
            [InlineKeyboardButton("📍 Share My Location", callback_data="share_location")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            emergency_message, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
        # Log emergency command usage
        print(f"🚨 Emergency command used by user {user_id}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            user_message = update.message.text
            
            print(f"📨 Telegram message from {user.first_name}: {user_message[:50]}...")
            
            # Get or create user session
            if user_id not in self.active_sessions:
                self.active_sessions[user_id] = {
                    'user_id': user_id,
                    'username': user.username or user.first_name,
                    'chat_history': [],
                    'location': None,
                    'started_at': datetime.now().isoformat()
                }
            
            session = self.active_sessions[user_id]
            
            # Handle quick action buttons
            if user_message in ["🚨 Emergency Help"]:
                await self.emergency_command(update, context)
                return
            elif user_message == "❓ Help":
                await self.help_command(update, context)
                return
            elif user_message == "📍 Share Location":
                await update.message.reply_text(
                    "📍 Please use the 📎 attachment button and select 'Location' to share your current location for better assistance."
                )
                return
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Build session context for RAG service
            session_context = {
                'session_id': f"telegram_{user_id}",
                'chat_history': session['chat_history'][-10:],  # Last 10 messages
                'location': session.get('location'),
                'platform': 'telegram',
                'user_info': {
                    'id': user_id,
                    'name': user.first_name,
                    'username': user.username
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Process message through RAG service
            ai_result = self.rag_service.process_message(user_message, session_context)
            
            # Update session history
            session['chat_history'].append({
                'user': user_message,
                'bot': ai_result.get('response', ''),
                'timestamp': datetime.now().isoformat(),
                'intent': ai_result.get('intent'),
                'emergency': ai_result.get('emergency', False)
            })
            
            # Limit session history
            if len(session['chat_history']) > 20:
                session['chat_history'] = session['chat_history'][-15:]
            
            # Handle emergency responses
            if ai_result.get('emergency'):
                await self.handle_emergency_response(update, context, ai_result, session)
            
            # Get and format response
            response_text = ai_result.get('response', 'Sorry, I encountered an issue.')
            formatted_response = self.format_for_telegram(response_text)
            
            # Split long messages (Telegram limit: 4096 characters)
            if len(formatted_response) > 4000:
                parts = self.split_message(formatted_response)
                for part in parts:
                    await update.message.reply_text(part)
            else:
                await update.message.reply_text(formatted_response)
            
            # Add quick follow-up actions for certain intents
            await self.add_follow_up_actions(update, context, ai_result)
            
        except Exception as e:
            print(f"❌ Error handling Telegram message: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(
                "I'm experiencing technical difficulties. For emergencies, call 911 directly."
            )
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location sharing"""
        user_id = str(update.effective_user.id)
        location = update.message.location
        
        # Store location in session
        if user_id in self.active_sessions:
            self.active_sessions[user_id]['location'] = {
                'lat': location.latitude,
                'lng': location.longitude,
                'timestamp': datetime.now().isoformat()
            }
        
        await update.message.reply_text(
            f"📍 *Location received!* ({location.latitude:.4f}, {location.longitude:.4f})\n\n"
            "I can now provide more accurate local information and emergency assistance. "
            "Your location will be included in any emergency alerts.\n\n"
            "How can I help you?",
            parse_mode='Markdown'
        )
        
        print(f"📍 Location received from user {user_id}: {location.latitude}, {location.longitude}")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads (for hazard reporting)"""
        user_id = str(update.effective_user.id)
        caption = update.message.caption or "Photo report"
        
        await update.message.reply_text(
            "📸 *Photo received!* Thank you for reporting this.\n\n"
            "I've noted your report. For immediate hazards that need urgent attention:\n"
            "• *Emergency situations:* Call 911\n"
            "• *City issues:* Call 311 (317-327-4622)\n"
            "• *Non-urgent reports:* Use RequestIndy app\n\n"
            "Is this an emergency situation?",
            parse_mode='Markdown'
        )
        
        print(f"📸 Photo received from user {user_id}: {caption}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "share_location":
            await query.edit_message_text(
                "📍 *To share your location:*\n\n"
                "1. Tap the 📎 attachment button\n"
                "2. Select 'Location'\n"
                "3. Choose 'Send My Current Location'\n\n"
                "This helps me provide better emergency assistance!",
                parse_mode='Markdown'
            )
        elif query.data == "emergency_numbers":
            await query.edit_message_text(
                "📞 *Emergency Contact Numbers:*\n\n"
                "🚨 *Emergency:* 911\n"
                "👮 *Police Non-Emergency:* 317-327-3811\n"
                "🏛️ *Mayor's Action Center:* 317-327-4622\n"
                "☠️ *Poison Control:* 1-800-222-1222\n"
                "🆘 *Crisis Text Line:* Text HOME to 741741\n\n"
                "*For life-threatening emergencies, call 911 immediately!*",
                parse_mode='Markdown'
            )
    
    async def handle_emergency_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     ai_result: dict, session: dict):
        """Handle emergency-specific responses"""
        try:
            user_id = session['user_id']
            user_message = update.message.text
            location_data = session.get('location')
            
            # Send emergency alert email
            if self.notification_service:
                alert_result = self.notification_service.send_emergency_alert(
                    user_message,
                    location_data,
                    f"telegram_{user_id}"
                )
                
                if alert_result and alert_result.get('success'):
                    await update.message.reply_text(
                        "🚨 *Emergency alert sent to authorities with your information.*\n\n"
                        "📧 Monitoring team has been notified\n"
                        f"📍 {'Location included' if location_data else 'Please share location for faster response'}\n\n"
                        "*For immediate life-threatening emergencies, still call 911 directly.*",
                        parse_mode='Markdown'
                    )
                    print(f"✅ Emergency alert sent for Telegram user {user_id}")
                else:
                    print(f"❌ Emergency alert failed for user {user_id}")
            
        except Exception as e:
            print(f"❌ Error handling emergency response: {e}")
    
    def split_message(self, text: str) -> list:
        """Split long messages into smaller chunks"""
        max_length = 4000
        parts = []
        
        while len(text) > max_length:
            split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            
            parts.append(text[:split_pos])
            text = text[split_pos:].lstrip()
        
        if text:
            parts.append(text)
        
        return parts
    
    async def add_follow_up_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ai_result: dict):
        """Add relevant follow-up action buttons based on response"""
        intent = ai_result.get('intent', '')
        
        if intent == 'medical':
            keyboard = [
                [InlineKeyboardButton("🚨 Emergency Numbers", callback_data="emergency_numbers")],
                [InlineKeyboardButton("🏥 Hospital Info", callback_data="hospital_info")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "*Need immediate medical help?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif intent == 'city_services':
            await update.message.reply_text(
                "*Need to report a city issue?*\n\n"
                "📞 Call 311: 317-327-4622\n"
                "💻 RequestIndy: request.indy.gov",
                parse_mode='Markdown'
            )
    
    def run_webhook(self, webhook_url: str):
        """Run bot with webhook (for production)"""
        try:
            self.application.run_webhook(
                listen="0.0.0.0",
                port=8443,
                url_path=self.token,
                webhook_url=f"{webhook_url}/{self.token}"
            )
        except Exception as e:
            print(f"❌ Webhook error: {e}")
    
    def run_polling(self):
        """Run bot with polling (for development)"""
        try:
            print("🤖 Starting Telegram bot with polling...")
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            print(f"❌ Polling error: {e}")