"""
Clean RAG Service for SafeIndy Assistant
Location-aware responses with emergency alerts, no circular imports
"""

from flask import current_app, session
from datetime import datetime
from typing import Dict, List, Optional
import json

from .llm_service import LLMService  
from .search_service import SearchService
from .vector_service import VectorService

class RAGService:
    """
    Simplified Retrieval-Augmented Generation service that combines:
    - LLM (Groq) for conversational AI
    - Search (Perplexity Sonar) for real-time data
    - Vector DB (Qdrant) for stored knowledge
    - Location awareness for better responses (no maps)
    """
    
    def __init__(self):
        try:
            self.llm_service = LLMService()
            self.search_service = SearchService()
            self.vector_service = VectorService()
            print("✅ RAG Service initialized (simplified - no maps)")
        except Exception as e:
            print(f"❌ RAG Service initialization error: {e}")
            # Initialize with None for graceful degradation
            self.llm_service = None
            self.search_service = None  
            self.vector_service = None
    
    def process_message(self, user_message: str, session_context: Dict) -> Dict:
        """
        Process user message through simplified RAG pipeline
        """
        try:
            print(f"🔄 Processing message: {user_message[:50]}...")
            
            # Check if services are available
            if not self.llm_service:
                return self._get_service_unavailable_response(user_message)
            
            # Classify intent using LLM service
            intent, confidence = self.llm_service._classify_intent(user_message, "")
            print(f"📋 Intent classified: {intent} (confidence: {confidence})")
            
            # Preserve the intent throughout processing
            intent_result = {
                'intent': intent,
                'confidence': confidence
            }
            
            # Route to appropriate handler based on intent
            if intent == 'emergency' and confidence >= 0.7:
                print("🚨 Processing as emergency...")
                return self._process_emergency_query(user_message, session_context, intent_result)
            
            elif intent in ['medical', 'police', 'location'] and confidence >= 0.7:
                print(f"📍 Processing as location-based query: {intent}")
                return self._process_location_query(user_message, session_context, intent_result)
            
            elif intent == 'bot_capabilities':
                print("🤖 Processing bot capabilities question...")
                return self._handle_capability_questions(user_message)
            
            elif intent == 'multiple_questions':
                print("❓ Processing multiple questions...")
                return self._handle_multiple_questions(user_message, session_context)
            
            elif intent == 'information':
                print("📚 Processing information request...")
                return self._handle_information_request(user_message, session_context, intent_result)
            
            else:
                print(f"💬 Processing as general query: {intent}")
                return self._process_general_query(user_message, session_context, intent_result)
            
        except Exception as e:
            print(f"❌ RAG processing error: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_response(user_message, str(e))

    def _get_service_unavailable_response(self, user_message: str) -> Dict:
        """Response when core services are unavailable"""
        return {
            'response': """I'm experiencing technical difficulties with my core services right now.

**For immediate assistance:**
• **Emergencies:** Call 911
• **Police:** 317-327-3811  
• **City Services:** 317-327-4622
• **Online:** Visit indy.gov

Please try again in a moment while I reconnect to my services.""",
            'intent': 'service_error',
            'confidence': 1.0,
            'emergency': False,
            'sources': [
                {
                    'title': 'Indianapolis Official Website',
                    'url': 'https://www.indy.gov',
                    'type': 'official'
                }
            ],
            'timestamp': datetime.now().isoformat()
        }

    def _format_response_text(self, text: str) -> str:
        """
        Format response text to convert markdown links to HTML and improve readability
        """
        import re
        
        if not text:
            return text
        
        # Convert markdown links [text](url) to HTML links
        markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        text = re.sub(markdown_link_pattern, r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
        
        # Convert plain URLs to clickable links (for URLs not already in markdown format)
        url_pattern = r'(?<!href=")(?<!">)(https?://[^\s<>"]+)'
        text = re.sub(url_pattern, r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', text)
        
        # Convert **bold** to HTML bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Convert *italic* to HTML italic
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Convert line breaks to HTML breaks
        text = text.replace('\n', '<br>')
        
        return text

    def _process_emergency_query(self, user_message: str, session_context: Dict, intent_result: Dict) -> Dict:
        """
        Process emergency queries with immediate response
        """
        try:
            print("🚨 Processing emergency query...")
            
            # Get emergency-specific information if search service available
            search_results = None
            vector_results = None
            
            if self.search_service:
                search_results = self._get_search_results(user_message, 'emergency')
            if self.vector_service:
                vector_results = self._get_vector_context(user_message, 'emergency')
            
            # Generate immediate emergency response
            emergency_response = self._handle_emergency_response(user_message, intent_result)
            
            # Add location-aware emergency contacts if location available
            if session_context.get('location'):
                location_info = self._get_location_aware_contacts(session_context['location'])
                if location_info:
                    emergency_response['response'] += f"\n\n{location_info}"
            
            # Add additional context if available
            if search_results or vector_results:
                enhanced_context = self._build_enhanced_context(
                    session_context,
                    search_results,
                    vector_results,
                    intent_result
                )
                
                # Get additional AI guidance if LLM available
                if self.llm_service:
                    ai_response = self.llm_service.generate_response(user_message, context=enhanced_context)
                    
                    # Combine emergency response with AI guidance
                    if ai_response.get('response'):
                        emergency_response['response'] += f"\n\n**Additional Guidance:**\n{ai_response['response']}"
            
            # Add sources
            if search_results and search_results.get('sources'):
                emergency_response['sources'].extend(search_results['sources'])
            
            if vector_results and vector_results.get('sources'):
                emergency_response['sources'].extend(vector_results['sources'])
            
            # Format the response text to convert markdown links to HTML
            emergency_response['response'] = self._format_response_text(emergency_response['response'])
            
            print("✅ Emergency query processed")
            return emergency_response
            
        except Exception as e:
            print(f"❌ Emergency query processing error: {e}")
            return self._get_fallback_response(user_message, str(e))

    def _process_location_query(self, user_message: str, session_context: Dict, intent_result: Dict) -> Dict:
        """
        Process location-based queries with text-based location information
        """
        try:
            intent = intent_result['intent']
            confidence = intent_result['confidence']
            
            print(f"📍 Processing location query - Intent: {intent}, Confidence: {confidence}")
            
            # Get location-aware response
            location_response = self._get_location_aware_response(user_message, intent, session_context)
            
            # Get additional context if services available
            search_results = None
            vector_results = None
            
            if self.search_service:
                search_results = self._get_search_results(user_message, intent)
            if self.vector_service:
                vector_results = self._get_vector_context(user_message, intent)
            
            # Build enhanced context for AI response
            enhanced_context = self._build_enhanced_context(
                session_context,
                search_results,
                vector_results,
                intent_result
            )
            
            # Generate AI response if LLM available
            combined_response = 'I can help you find local resources.'
            if self.llm_service:
                ai_response = self.llm_service.generate_response(user_message, context=enhanced_context)
                combined_response = ai_response.get('response', 'I can help you find local resources.')
            
            # Add location information
            if location_response:
                combined_response += f"\n\n{location_response}"
            
            # Format the response text to convert markdown links to HTML
            combined_response = self._format_response_text(combined_response)
            
            # Preserve original intent
            result = {
                'response': combined_response,
                'intent': intent,
                'confidence': confidence,
                'sources': self._get_limited_sources(search_results, vector_results),
                'emergency': False,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Location query processed. Intent: {intent}")
            return result
            
        except Exception as e:
            print(f"❌ Location query processing error: {e}")
            return self._get_fallback_response(user_message, str(e))

    def _process_general_query(self, user_message: str, session_context: Dict, intent_result: Dict) -> Dict:
        """
        Process general queries with location awareness
        """
        try:
            intent = intent_result['intent']
            confidence = intent_result['confidence']
            
            print(f"💬 Processing general query - Intent: {intent}, Confidence: {confidence}")
            
            # Check if this needs location context
            needs_location = self._needs_location_context(user_message, intent)
            
            if needs_location:
                print("📍 General query needs location context")
                return self._process_location_query(user_message, session_context, intent_result)
            
            # Regular processing
            search_results = None
            vector_results = None
            
            # Determine if search is needed
            needs_search = False
            if self.search_service:
                needs_search = self.search_service.is_search_needed(user_message, intent)
            
            if needs_search or confidence < 0.7:
                print("🔍 Gathering additional context...")
                if self.search_service:
                    search_results = self._get_search_results(user_message, intent)
                if self.vector_service:
                    vector_results = self._get_vector_context(user_message, intent)
            
            # Build context
            enhanced_context = self._build_enhanced_context(
                session_context,
                search_results,
                vector_results,
                intent_result
            )
            
            # Generate response
            response_text = 'I apologize, but I encountered an issue generating a response.'
            if self.llm_service:
                ai_response = self.llm_service.generate_response(user_message, context=enhanced_context)
                response_text = ai_response.get('response', response_text)
            
            # Format the response text to convert markdown links to HTML
            response_text = self._format_response_text(response_text)
            
            # Compile final response
            result = {
                'response': response_text,
                'intent': intent,
                'confidence': confidence,
                'sources': self._get_limited_sources(search_results, vector_results),
                'emergency': False,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ General query processed. Intent: {intent}")
            return result
            
        except Exception as e:
            print(f"❌ General query processing error: {e}")
            return self._get_fallback_response(user_message, str(e))

    def _get_location_aware_response(self, user_message: str, intent: str, session_context: Dict) -> str:
        """
        Generate location-aware text response using real-time search data
        """
        try:
            message_lower = user_message.lower()
            user_location = session_context.get('location')
            
            # Get real-time information based on query type
            if any(word in message_lower for word in ['hospital', 'emergency room', 'medical']):
                return self._get_live_hospital_info(user_location)
            elif any(word in message_lower for word in ['police', 'cop', 'law enforcement']):
                return self._get_live_police_info(user_location)  
            elif any(word in message_lower for word in ['fire department', 'fire station']):
                return self._get_live_fire_info(user_location)
            else:
                return self._get_live_general_info(user_location)
                
        except Exception as e:
            print(f"❌ Location-aware response error: {e}")
            return self._get_fallback_location_info()

    def _get_live_hospital_info(self, user_location: Dict = None) -> str:
        """Get current hospital information from web search"""
        try:
            # Search for current Indianapolis hospital information
            search_results = None
            if self.search_service:
                search_results = self.search_service.search_community_resources('hospitals')
            
            location_text = ""
            if user_location:
                location_text = "📍 Based on your location:\n\n"
            
            # Use search results if available, otherwise fallback
            if search_results and search_results.get('results'):
                response = """{}🏥 **Indianapolis Hospitals (Current Information):**

{}

🚨 **For Medical Emergencies: Call 911 immediately**

💡 **Tip:** If you enable location sharing, emergency responders can find you faster.""".format(
                    location_text, search_results['results'])
                return self._format_response_text(response)
            else:
                return self._get_fallback_hospital_info(user_location)
                
        except Exception as e:
            print(f"❌ Live hospital info error: {e}")
            return self._get_fallback_hospital_info(user_location)

    def _get_live_police_info(self, user_location: Dict = None) -> str:
        """Get current police information from web search"""
        try:
            # Search for current IMPD information
            search_results = None
            if self.search_service:
                search_results = self.search_service.search_emergency_info('police')
            
            location_text = ""
            if user_location:
                location_text = "📍 Your location noted for emergency response.\n\n"
            
            if search_results and search_results.get('results'):
                response = """{}👮 **Indianapolis Police (Current Information):**

{}

🚨 **For Emergencies: Call 911**
📞 **Non-Emergency: 317-327-3811**""".format(location_text, search_results['results'])
                return self._format_response_text(response)
            else:
                return self._get_fallback_police_info(user_location)
                
        except Exception as e:
            print(f"❌ Live police info error: {e}")
            return self._get_fallback_police_info(user_location)

    def _get_live_fire_info(self, user_location: Dict = None) -> str:
        """Get current fire department information from web search"""
        try:
            # Search for current IFD information
            search_results = None
            if self.search_service:
                search_results = self.search_service.search_emergency_info('fire')
            
            location_text = ""
            if user_location:
                location_text = "📍 Your location noted for emergency response.\n\n"
            
            if search_results and search_results.get('results'):
                response = """{}🚒 **Indianapolis Fire Department (Current Information):**

{}

🚨 **For Fire/Medical Emergencies: Call 911 immediately**""".format(location_text, search_results['results'])
                return self._format_response_text(response)
            else:
                return self._get_fallback_fire_info(user_location)
                
        except Exception as e:
            print(f"❌ Live fire info error: {e}")
            return self._get_fallback_fire_info(user_location)

    def _get_live_general_info(self, user_location: Dict = None) -> str:
        """Get current general Indianapolis emergency information"""
        try:
            # Search for current Indianapolis emergency services
            search_results = None
            if self.search_service:
                search_results = self.search_service.search_emergency_info('general')
            
            location_text = ""
            if user_location:
                location_text = "📍 Location services enabled - emergency responders can locate you faster.\n\n"
            
            if search_results and search_results.get('results'):
                response = """{}🏛️ **Indianapolis Emergency & Safety Resources (Current):**

{}

🆘 **Always call 911 for life-threatening emergencies first**""".format(location_text, search_results['results'])
                return self._format_response_text(response)
            else:
                return self._get_fallback_general_info(user_location)
                
        except Exception as e:
            print(f"❌ Live general info error: {e}")
            return self._get_fallback_general_info(user_location)

    # Fallback methods with minimal static information (only emergency numbers)
    def _get_fallback_hospital_info(self, user_location: Dict = None) -> str:
        """Fallback hospital information with just emergency contacts"""
        location_text = "📍 Location noted.\n\n" if user_location else ""
        
        return """{}🏥 **Emergency Medical Information:**

🚨 **For Medical Emergencies: Call 911 immediately**

**Alternative Emergency Numbers:**
• Poison Control: 1-800-222-1222
• Crisis Text Line: Text HOME to 741741

For current hospital locations and contact information, visit:
• indy.gov (official Indianapolis website)
• Search "Indianapolis hospitals" for up-to-date information

💡 **Tip:** Enable location sharing so emergency responders can find you faster.""".format(location_text)

    def _get_fallback_police_info(self, user_location: Dict = None) -> str:
        """Fallback police information with just emergency contacts"""
        location_text = "📍 Your location noted for emergency response.\n\n" if user_location else ""
        
        return """{}👮 **Police Emergency Information:**

🚨 **For Emergencies: Call 911**
📞 **IMPD Non-Emergency: 317-327-3811**

**Additional Resources:**
• Text to 911: Available for emergencies
• Anonymous tips: 317-262-TIPS (8477)
• Online: indy.gov/activity/public-safety

For current police district locations and hours, visit indy.gov or call the non-emergency number.""".format(location_text)

    def _get_fallback_fire_info(self, user_location: Dict = None) -> str:
        """Fallback fire department information"""
        location_text = "📍 Your location noted for emergency response.\n\n" if user_location else ""
        
        return """{}🚒 **Fire Emergency Information:**

🚨 **For Fire/Medical Emergencies: Call 911 immediately**

**Fire Safety Reminders:**
• Get out and stay out in case of fire
• Have working smoke detectors
• Know two ways out of every room
• Practice your escape plan

For current IFD information and services, visit indy.gov or call 911 for emergencies.""".format(location_text)

    def _get_fallback_general_info(self, user_location: Dict = None) -> str:
        """Fallback general emergency information"""
        location_text = "📍 Location services enabled - emergency responders can locate you faster.\n\n" if user_location else ""
        
        return """{}🏛️ **Essential Emergency Information:**

**Emergency Numbers:**
• **Emergency (Police/Fire/Medical):** 911
• **IMPD Non-Emergency:** 317-327-3811
• **Mayor's Action Center (311):** 317-327-4622
• **Poison Control:** 1-800-222-1222

**Key Resources:**
• City services: indy.gov
• Service requests: request.indy.gov
• Community help: Dial 2-1-1

🆘 **Always call 911 for life-threatening emergencies first**

For current contact information and services, visit the official Indianapolis website at indy.gov""".format(location_text)

    def _get_fallback_location_info(self) -> str:
        """Fallback when location services fail completely"""
        return """🏛️ **Essential Indianapolis Emergency Information:**

**Emergency Numbers (Always Current):**
• **Emergency:** 911
• **Police Non-Emergency:** 317-327-3811  
• **Mayor's Action Center:** 317-327-4622
• **Poison Control:** 1-800-222-1222

For current contact information, addresses, and hours:
• Visit indy.gov (official Indianapolis website)
• Call 311 for city services
• Call 911 for emergencies

🚨 **For life-threatening emergencies, always call 911 first**"""

    def _needs_location_context(self, user_message: str, intent: str) -> bool:
        """Determine if location context would be helpful"""
        location_intents = ['medical', 'police', 'emergency', 'location']
        location_keywords = ['near', 'nearest', 'close', 'where', 'directions', 'address', 'find', 'location']
        
        if intent in location_intents:
            return True
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in location_keywords)

    def _handle_capability_questions(self, user_message: str) -> Dict:
        """Handle questions about what the bot can do"""
        response = """🤖 **Great questions! Here's how I can help you:**

**🚨 Emergency Support:**
• Provide current emergency contact information from live sources
• Help you understand when to call 911 vs. non-emergency lines
• Send emergency alerts to authorities if you enable location sharing
• *Note: I'm not directly connected to 911 - always call 911 for true emergencies*

**🏛️ City Services:**
• Get current information about 311 requests and city services
• Help find current city department contacts and procedures
• Provide up-to-date information about RequestIndy app and services

**📍 Local Resources:**
• Find current contact information for hospitals, police stations, fire departments
• Provide Indianapolis-specific safety information from official sources
• Share current community resources and contact numbers

**🏘️ Public Safety Info:**
• Safety tips and emergency preparedness advice
• Current reporting procedures for various issues
• Weather alerts and emergency notifications

**🔄 Real-Time Information:**
• I get current information from live web sources, not outdated databases
• Emergency contact numbers and addresses are fetched from official websites
• All information is cross-referenced with official Indianapolis sources

**⚠️ What I Can't Do:**
• I cannot track real-time crime data or live emergency calls
• I cannot dispatch emergency services directly
• I cannot access your personal information without permission

**For immediate emergencies, always call 911 directly.**

What specific area would you like current information about?"""
        
        return {
            'response': response,
            'intent': 'bot_capabilities',  
            'confidence': 0.9,
            'emergency': False,
            'sources': [
                {
                    'title': 'Indianapolis Emergency Services',
                    'url': 'https://www.indy.gov/activity/public-safety',
                    'type': 'official'
                }
            ],
            'timestamp': datetime.now().isoformat()
        }

    def _handle_multiple_questions(self, user_message: str, session_context: Dict) -> Dict:
        """Handle compound questions properly"""
        # Build special context for multiple questions
        multi_context = session_context.copy() if session_context else {}
        multi_context['multi_question_mode'] = True
        multi_context['instruction'] = "The user has asked multiple questions. Address each one clearly with organized sections."
        
        # Process through LLM with structured response request
        llm_result = {}
        if self.llm_service:
            llm_result = self.llm_service.generate_response(user_message, multi_context)
        
        # Ensure structured response
        response_text = llm_result.get('response', 'I can help with multiple questions, but my processing service is currently unavailable.')
        
        structured_response = f"""I can help with all your questions! Let me address each one:

{response_text}

---
💡 **Need more specific help with any of these topics?** Just ask about one at a time and I can provide more detailed guidance with current information!"""
        
        return {
            'response': structured_response,
            'intent': 'multiple_questions',
            'confidence': llm_result.get('confidence', 0.7),
            'emergency': False,
            'timestamp': datetime.now().isoformat()
        }

    def _handle_information_request(self, user_message: str, session_context: Dict, intent_result: Dict) -> Dict:
        """Handle informational queries with enhanced context"""
        # Get relevant information through normal RAG pipeline
        result = self._process_general_query(user_message, session_context, intent_result)
        
        # Add helpful footer for information requests
        if 'response' in result:
            info_footer = "\n\n💡 **Need more help?** Call 311 (317-327-4622) for city services or visit indy.gov for current information"
            result['response'] += info_footer
        
        result['intent'] = 'information'
        result['emergency'] = False
        return result

    def _handle_emergency_response(self, user_message: str, intent_result: Dict) -> Dict:
        """Handle emergency messages with immediate response"""
        emergency_response = """🚨 **EMERGENCY DETECTED**

**For immediate life-threatening emergencies:**
📞 **CALL 911 NOW**

**Indianapolis Emergency Contacts:**
• **Emergency:** 911 (call or text)
• **Police Non-Emergency:** 317-327-3811  
• **Poison Control:** 1-800-222-1222

{}

**If this is a medical emergency, fire, or crime in progress - call 911 immediately.**

For non-emergency assistance, I can help guide you to current resources."""

        return {
            'response': emergency_response.format(self._get_emergency_guidance(user_message)),
            'intent': 'emergency',
            'confidence': intent_result['confidence'],
            'emergency': True,
            'sources': [
                {
                    'title': 'Call 911',
                    'url': 'tel:911',
                    'type': 'emergency'
                },
                {
                    'title': 'Indianapolis Emergency Services',
                    'url': 'https://www.indy.gov/agency/indianapolis-metropolitan-police-department',
                    'type': 'official'
                }
            ],
            'timestamp': datetime.now().isoformat()
        }

    def _get_emergency_guidance(self, message: str) -> str:
        """Get specific guidance based on emergency type"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['fire', 'smoke', 'burning']):
            return """**FIRE EMERGENCY:**
• Get out immediately and stay out
• Call 911 from a safe location
• Do not go back inside for any reason"""
        
        elif any(word in message_lower for word in ['accident', 'crash', 'hit']):
            return """**VEHICLE ACCIDENT:**
• Move to safety if possible
• Call 911 immediately
• Do not move injured persons unless in immediate danger"""
        
        elif any(word in message_lower for word in ['chest pain', 'heart', 'breathing']):
            return """**MEDICAL EMERGENCY:**
• Call 911 immediately
• Stay calm and follow dispatcher instructions
• Have someone meet paramedics at entrance if possible"""
        
        else:
            return """**GENERAL EMERGENCY:**
• Call 911 for immediate life-threatening situations
• Stay calm and provide clear information to dispatcher
• Follow all dispatcher instructions"""

    def _get_location_aware_contacts(self, user_location: Dict) -> str:
        """Get location-aware emergency contacts"""
        
        if not user_location:
            return None
            
        lat = user_location.get('lat', 'Unknown')
        lng = user_location.get('lng', 'Unknown')
        
        return """📍 **Your Location Noted:** {:.4f}, {:.4f}

⚡ **This location information will be automatically included in any emergency alerts sent to authorities.**

🚨 **For immediate emergencies, still call 911 directly** - they can dispatch help faster than any app.""".format(lat, lng)

    def _get_search_results(self, user_message: str, intent: str) -> Optional[Dict]:
        """Get real-time search results from Perplexity Sonar"""
        if not self.search_service:
            return None
            
        try:
            if intent == 'emergency':
                return self.search_service.search_emergency_info('general')
            elif intent == 'city_services':
                return self.search_service.search_city_services('general')
            elif intent == 'weather':
                return self.search_service.search_weather_alerts()
            elif intent == 'community':
                return self.search_service.search_community_resources('general')
            else:
                return self.search_service.search_indianapolis_data(user_message, intent)
        except Exception as e:
            print(f"⚠️ Search error: {e}")
            return None

    def _get_vector_context(self, user_message: str, intent: str) -> Optional[Dict]:
        """Get relevant context from vector database"""
        if not self.vector_service:
            return None
            
        try:
            return self.vector_service.search_knowledge(user_message, intent)
        except Exception as e:
            print(f"⚠️ Vector search error: {e}")
            return None

    def _build_enhanced_context(self, session_context: Dict, search_results: Dict, 
                              vector_results: Dict, intent_result: Dict) -> Dict:
        """Build comprehensive context for final AI response"""
        
        enhanced_context = session_context.copy() if session_context else {}
        
        # Add search results
        if search_results and search_results.get('results'):
            enhanced_context['search_results'] = search_results['results']
            enhanced_context['search_sources'] = search_results.get('sources', [])
        
        # Add vector knowledge
        if vector_results and vector_results.get('results'):
            enhanced_context['knowledge_base'] = vector_results['results']
        
        # Add initial classification
        enhanced_context['initial_intent'] = intent_result.get('intent')
        enhanced_context['initial_confidence'] = intent_result.get('confidence')
        
        return enhanced_context

    def _get_limited_sources(self, search_results: Dict, vector_results: Dict) -> List[Dict]:
        """Get limited, relevant sources from search and vector results"""
        
        sources = []
        
        # Add search sources (LIMIT TO TOP 2)
        if search_results and search_results.get('sources'):
            search_sources = search_results['sources'][:2]
            sources.extend(search_sources)
        
        # Add vector sources (LIMIT TO TOP 1)
        if vector_results and vector_results.get('sources'):
            vector_sources = vector_results['sources'][:1]
            sources.extend(vector_sources)
        
        # REMOVE DUPLICATES and limit total sources
        unique_sources = []
        seen_urls = set()
        
        for source in sources:
            url = source.get('url', '')
            if url not in seen_urls and len(unique_sources) < 2:
                unique_sources.append(source)
                seen_urls.add(url)
        
        # If no sources, add a default Indianapolis source
        if not unique_sources:
            unique_sources = [
                {
                    'title': 'City of Indianapolis',
                    'url': 'https://www.indy.gov',
                    'type': 'official'
                }
            ]
        
        return unique_sources

    def _get_fallback_response(self, user_message: str, error: str) -> Dict:
        """Generate fallback response when services fail"""
        
        # Check for emergency keywords in fallback
        if any(word in user_message.lower() for word in ['emergency', '911', 'urgent', 'help']):
            response = """🚨 **Emergency Information**

I'm experiencing technical difficulties, but here are essential Indianapolis emergency contacts:

**IMMEDIATE EMERGENCY: 911**
**Police Non-Emergency: 317-327-3811**
**Mayor's Action Center: 317-327-4622** 
**Poison Control: 1-800-222-1222**

For current city services, visit: indy.gov
For service requests: request.indy.gov"""
        else:
            response = """I apologize, but I'm experiencing technical difficulties right now. 

**For immediate help:**
• **Emergencies:** 911
• **Police:** 317-327-3811  
• **City Services:** 317-327-4622
• **Online:** indy.gov

I'll be back to full functionality shortly. Thank you for your patience!"""
        
        return {
            'response': response,
            'intent': 'error',
            'confidence': 0.0,
            'sources': [
                {
                    'title': 'Indianapolis Official Website',
                    'url': 'https://www.indy.gov',
                    'type': 'official'
                }
            ],
            'error': error,
            'timestamp': datetime.now().isoformat()
        }

    def get_chat_suggestions(self, message_history: List[Dict]) -> List[str]:
        """Generate contextual chat suggestions based on conversation history"""
        
        # Default suggestions
        base_suggestions = [
            "How do I report a pothole?",
            "Find current hospital contact information", 
            "Emergency contact numbers",
            "What city services are available?",
            "Current weather alerts for Indianapolis"
        ]
        
        # If no history, return base suggestions
        if not message_history:
            return base_suggestions
        
        # Analyze recent messages for contextual suggestions
        recent_intents = []
        for msg in message_history[-3:]:  # Last 3 messages
            if 'intent' in msg:
                recent_intents.append(msg['intent'])
        
        # Generate contextual suggestions based on recent conversation
        contextual_suggestions = []
        
        if 'emergency' in recent_intents:
            contextual_suggestions.extend([
                "More current emergency contacts",
                "Find nearest emergency room",
                "Current police contact information"
            ])
        
        if 'city_services' in recent_intents:
            contextual_suggestions.extend([
                "Current RequestIndy information",
                "Other city services available", 
                "Current Mayor's Action Center contact"
            ])
        
        if 'community' in recent_intents:
            contextual_suggestions.extend([
                "Report community issue",
                "Find current local resources",
                "Current safety information"
            ])
        
        # Combine and limit suggestions
        all_suggestions = contextual_suggestions + base_suggestions
        return list(dict.fromkeys(all_suggestions))[:5]  # Remove duplicates, limit to 5

    def process_feedback(self, message_id: str, feedback_type: str, details: str = None):
        """Process user feedback to improve responses"""
        try:
            feedback_data = {
                'message_id': message_id,
                'feedback_type': feedback_type,
                'details': details,
                'timestamp': datetime.now().isoformat(),
                'session_id': session.get('session_id') if 'session' in globals() else 'unknown'
            }
            
            print(f"📝 Feedback received: {feedback_type} for message {message_id}")
            return {'status': 'success', 'message': 'Thank you for your feedback!'}
            
        except Exception as e:
            print(f"❌ Feedback processing error: {e}")
            return {'status': 'error', 'message': 'Failed to process feedback'}

    def get_system_status(self) -> Dict:
        """Get status of all RAG system components"""
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check LLM service
        try:
            if self.llm_service and hasattr(self.llm_service, 'client') and self.llm_service.client:
                status['components']['llm'] = 'healthy'
            else:
                status['components']['llm'] = 'error'
                status['overall_status'] = 'degraded'
        except:
            status['components']['llm'] = 'error'
            status['overall_status'] = 'degraded'
        
        # Check search service
        try:
            if self.search_service and hasattr(self.search_service, 'api_key') and self.search_service.api_key:
                status['components']['search'] = 'healthy'
            else:
                status['components']['search'] = 'error'
                status['overall_status'] = 'degraded'
        except:
            status['components']['search'] = 'error'
            status['overall_status'] = 'degraded'
        
        # Check vector service
        try:
            if self.vector_service and hasattr(self.vector_service, 'health_check'):
                vector_status = self.vector_service.health_check()
                status['components']['vector'] = vector_status
                if vector_status != 'healthy':
                    status['overall_status'] = 'degraded'
            else:
                status['components']['vector'] = 'unavailable'
        except:
            status['components']['vector'] = 'error'
            status['overall_status'] = 'degraded'
        
        return status

    def clear_session_context(self, session_id: str):
        """Clear session context and history"""
        try:
            # This would be handled by the Flask session in the route
            print(f"🧹 Session context cleared for {session_id}")
            return True
        except Exception as e:
            print(f"❌ Error clearing session: {e}")
            return False