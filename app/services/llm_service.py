"""
LLM Service for SafeIndy Assistant
Handles Groq API integration for conversational AI
"""

from groq import Groq
from flask import current_app
import json
from datetime import datetime
from typing import Dict, List, Optional

class LLMService:
    def __init__(self):
        self.client = None
        self.model = "llama3-8b-8192"
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization - only initialize when needed"""
        if self._initialized:
            return
        
        try:
            from flask import current_app
            api_key = current_app.config.get('GROQ_API_KEY')
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in configuration")
            
            from groq import Groq
            self.client = Groq(api_key=api_key)
            self._initialized = True
            print("✅ Groq client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Groq client: {e}")
            self.client = None
    
    def generate_response(self, user_message: str, context: Dict = None) -> Dict:
        # Initialize only when method is called
        self._ensure_initialized()
        
        if not self.client:
            return {
                'response': 'Sorry, AI service is currently unavailable. For emergencies, call 911.',
                'intent': 'error',
                'confidence': 0.0,
                'sources': []
            }
        
        try:
            # Build system prompt for SafeIndy Assistant
            system_prompt = self._build_system_prompt(context)
            
            # Create messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_message
                }
            ]
            
            # Add chat history if available
            if context and 'chat_history' in context:
                messages = self._add_chat_history(messages, context['chat_history'])
            
            # Generate completion
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more focused responses
                max_tokens=1024,
                top_p=0.9,
                stream=False,  # Non-streaming for now, can add streaming later
                stop=None,
            )
            
            response_text = completion.choices[0].message.content
            
            # Classify intent and extract metadata
            intent, confidence = self._classify_intent(user_message, response_text)
            
            return {
                'response': response_text,
                'intent': intent,
                'confidence': confidence,
                'model': self.model,
                'timestamp': datetime.now().isoformat(),
                'usage': {
                    'prompt_tokens': completion.usage.prompt_tokens,
                    'completion_tokens': completion.usage.completion_tokens,
                    'total_tokens': completion.usage.total_tokens
                }
            }
            
        except Exception as e:
            print(f"❌ Groq API error: {e}")
            return {
                'response': f'I encountered an error processing your request. For emergencies, please call 911 immediately.',
                'intent': 'error',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def generate_streaming_response(self, user_message: str, context: Dict = None):
        """
        Generate streaming AI response for real-time chat
        
        Args:
            user_message: User's input message
            context: Additional context
            
        Yields:
            Streaming response chunks
        """
        self._ensure_initialized()
        if not self.client:
            yield "Sorry, AI service is currently unavailable."
            return
        
        try:
            system_prompt = self._build_system_prompt(context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                top_p=0.9,
                stream=True,
                stop=None,
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def _build_system_prompt(self, context: Dict = None) -> str:
        """Build system prompt for SafeIndy Assistant"""
        
        base_prompt = """You are SafeIndy Assistant, an AI-powered public safety companion for Indianapolis residents. Your primary mission is to help with:

🚨 EMERGENCY SERVICES: Police, Fire, Medical emergencies
🏛️ CITY SERVICES: 311 requests, utilities, city departments  
🏘️ COMMUNITY SAFETY: Neighborhood resources, anonymous reporting
📍 LOCAL RESOURCES: Finding nearby services and facilities

CRITICAL EMERGENCY PROTOCOL:
- For life-threatening emergencies, ALWAYS direct users to call 911 IMMEDIATELY
- Never delay emergency responses with conversation
- Provide emergency numbers prominently: 911, Police: 317-327-3811, City: 317-327-4622

INDIANAPOLIS SPECIFIC INFORMATION:
- Emergency: 911 (text to 911 also available)
- IMPD Non-Emergency: 317-327-3811
- Mayor's Action Center (311): 317-327-4622
- RequestIndy app and request.indy.gov for city services
- Poison Control: 1-800-222-1222

RESPONSE GUIDELINES:
- Be helpful, accurate, and safety-focused
- Use clear, actionable language
- Provide specific Indianapolis resources and contacts
- Always prioritize user safety over convenience
- Be empathetic and supportive, especially for safety concerns
- Keep responses concise but complete
- Use emojis and formatting to improve readability

CURRENT CONTEXT:"""
        
        # Add current date/time
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        base_prompt += f"\n- Current time: {current_time}"
        
        # Add location context if available
        if context and 'location' in context:
            base_prompt += f"\n- User location: {context['location']}"
        
        # Add any recent search results or data
        if context and 'search_results' in context:
            base_prompt += f"\n- Recent Indianapolis data: {context['search_results']}"
        
        base_prompt += "\n\nRespond as SafeIndy Assistant with helpful, accurate Indianapolis public safety guidance."
        
        return base_prompt
    
    def _add_chat_history(self, messages: List, chat_history: List) -> List:
        """Add recent chat history to messages for context"""
        
        # Add last 3 exchanges for context (to avoid token limits)
        recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
        
        history_messages = []
        for exchange in recent_history:
            if 'user' in exchange:
                history_messages.append({"role": "user", "content": exchange['user']})
            if 'bot' in exchange:
                history_messages.append({"role": "assistant", "content": exchange['bot']})
        
        # Insert history before the current user message
        return messages[:-1] + history_messages + [messages[-1]]
    
    # UPDATE: Replace the _classify_intent method in your app/services/llm_service.py

    def _classify_intent(self, user_message: str, ai_response: str) -> tuple:
        """
        IMPROVED: Classify user intent with location queries prioritized
        
        Returns:
            tuple: (intent, confidence_score)
        """
        message_lower = user_message.lower().strip()
        
        # FIRST PRIORITY: Location-based queries (highest priority)
        location_patterns = [
            'find nearest', 'nearest', 'find closest', 'closest', 'near me', 'close to me',
            'where is', 'where can i find', 'directions to', 'how to get to'
        ]
        
        if any(pattern in message_lower for pattern in location_patterns):
            # Determine specific location intent with high confidence
            if any(word in message_lower for word in ['hospital', 'medical center', 'emergency room', 'clinic', 'doctor']):
                return 'medical', 0.9  # This will trigger map generation
            elif any(word in message_lower for word in ['police', 'police station', 'cop', 'officer']):
                return 'police', 0.9   # This will trigger map generation
            elif any(word in message_lower for word in ['fire station', 'fire department', 'firefighter']):
                return 'emergency', 0.9  # This will trigger map generation
            elif any(word in message_lower for word in ['pharmacy', 'drug store', 'cvs', 'walgreens']):
                return 'medical', 0.8
            else:
                return 'location', 0.8
        
        # SECOND: Check for informational queries (NOT emergencies)
        informational_patterns = [
            'what is', 'how to', 'tips for', 'how can i', 'what should i',
            'how do i prepare', 'what items', 'danger level', 'fire danger',
            'tell me about', 'information about', 'advice for',
            'staying safe during', 'safety tips', 'winter storm prep',
            'what are the', 'how do you', 'can you tell me'
        ]
        
        if any(pattern in message_lower for pattern in informational_patterns):
            return 'information', 0.8
        
        # Check for capability questions about the bot
        capability_patterns = [
            'what do you do', 'how do you work', 'what are your features',
            'are you connected to 911', 'can you help with', 'what kind of',
            'what can you do', 'how can you help'
        ]
        
        # Special case: "What kind of emergencies can you help with?"
        if 'what kind of emergencies can you' in message_lower:
            return 'bot_capabilities', 0.9
        
        if any(pattern in message_lower for pattern in capability_patterns):
            return 'bot_capabilities', 0.9
        
        # Multiple questions
        if user_message.count('?') > 1:
            return 'multiple_questions', 0.9
        
        # TRUE EMERGENCIES - Active, immediate danger requiring 911
        true_emergency_phrases = [
            'there is a fire', 'house is on fire', 'building on fire',
            'car accident happened', 'car accident just happened', 'just crashed',
            'gas leak happening', 'smell gas leak', 'gas emergency now',
            'someone shooting', 'shots fired', 'gunshots now',
            'someone attacking me', 'being attacked', 'help me now',
            'breaking in now', 'burglar in house', 'intruder here',
            'someone is breaking in', 'breaking in help',
            
            # Medical emergencies
            'having heart attack', 'chest pain now', 'cant breathe',
            'overdosed', 'took too many pills', 'poisoning',
            'unconscious person', 'not breathing', 'no pulse',
            'bleeding badly', 'severe bleeding', 'choking now',
            
            # Direct emergency calls
            'call 911 now', 'need ambulance', 'need police now',
            'emergency happening', 'urgent help', 'need help urgent'
        ]
        
        if any(phrase in message_lower for phrase in true_emergency_phrases):
            return 'emergency', 0.9
        
        # Special cases for common emergency patterns
        if 'accident just happened' in message_lower:
            return 'emergency', 0.9
        
        if 'breaking in' in message_lower and 'help' in message_lower:
            return 'emergency', 0.9
        
        if 'need help' in message_lower and 'urgent' in message_lower:
            return 'emergency', 0.8
        
        # Gas leak emergency
        if 'gas leak' in message_lower and any(word in message_lower for word in ['emergency', 'call 911', 'urgent']):
            return 'emergency', 0.9
        
        # Emergency keywords with urgency context
        emergency_keywords = ['fire', 'accident', 'crash', 'shooting', 'attack', 'gas leak', 'breaking in']
        urgency_words = ['right now', 'happening', 'just', 'help me', 'emergency', 'urgent', 'call 911', 'just happened']
        
        has_emergency_keyword = any(word in message_lower for word in emergency_keywords)
        has_urgency = any(word in message_lower for word in urgency_words)
        
        if has_emergency_keyword and has_urgency:
            return 'emergency', 0.8
        
        # General help requests with emergency context
        if ('help' in message_lower or 'emergency' in message_lower) and any(word in message_lower for word in [
            'me', 'someone', 'person', 'now', 'urgent', 'quick', 'immediate'
        ]):
            return 'emergency', 0.7
        
        # Non-emergency classifications (but check for location context first)
        
        # Medical/health (but not active emergencies) - HIGH PRIORITY
        if any(word in message_lower for word in ['hospital', 'medical center', 'poison control', 'health', 'doctor', 'clinic']):
            return 'medical', 0.8
        
        # Police services (but not active crimes)
        if any(word in message_lower for word in ['police', 'report crime', 'theft', 'stolen property']):
            return 'police', 0.8
        
        # City services  
        if any(word in message_lower for word in ['pothole', 'trash', 'street light', '311', 'city service', 'mayor']):
            return 'city_services', 0.8
        
        # Community/neighborhood
        if any(word in message_lower for word in ['neighborhood', 'community', 'suspicious activity', 'safety']):
            return 'community', 0.7
        
        # Weather/alerts
        if any(word in message_lower for word in ['weather', 'storm', 'tornado', 'alert', 'warning']):
            return 'weather', 0.7
        
        # General location/directions (lower priority than specific services)
        if any(word in message_lower for word in ['where', 'directions', 'address', 'location']):
            return 'location', 0.7
        
        # General information
        if any(word in message_lower for word in ['what', 'how', 'when', 'info', 'information']):
            return 'information', 0.6
        
        # Greeting/general
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'thanks', 'goodbye']):
            return 'greeting', 0.9
        
        return 'general', 0.5

    def is_emergency(self, message: str) -> bool:
        """FIXED: More accurate emergency detection"""
        intent, confidence = self._classify_intent(message, "")
        return intent == 'emergency' and confidence >= 0.7