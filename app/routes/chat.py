"""
COMPLETE Updated Chat Routes for SafeIndy Assistant
Enhanced to properly handle map responses and hospital location queries
"""

from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import uuid

# Import our AI services
from app.services.rag_service import RAGService
from app.services.notification_service import NotificationService
from app.services.analytics_service import AnalyticsService
from app.utils.rate_limiter import get_rate_limiter, rate_limit
from app.utils.data_validator import validate_chat_input, validate_location_input
from app.utils.cache_manager import get_ai_cache

# Create blueprint
chat_bp = Blueprint('chat', __name__)

# Initialize services (will be created once per app instance)
rag_service = None
notification_service = None
analytics_service = None

def get_rag_service():
    """Get or create RAG service instance"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service

def get_notification_service():
    """Get or create notification service instance"""
    global notification_service
    if notification_service is None:
        notification_service = NotificationService()
    return notification_service

def get_analytics_service():
    """Get or create analytics service instance"""
    global analytics_service
    if analytics_service is None:
        analytics_service = AnalyticsService()
    return analytics_service

@chat_bp.route('/')
def chat_interface():
    """Main chat interface page"""
    
    # Initialize session if needed
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['chat_history'] = []
    
    return render_template('chat.html',
                         session_id=session['session_id'],
                         page_title="Chat - SafeIndy Assistant")

@chat_bp.route('/send', methods=['POST'])
@rate_limit('chat_messages')
def send_message():
    """
    ENHANCED: Handle chat messages with comprehensive map integration
    """
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        location_data = data.get('location')
        
        print(f"📨 Received message: '{user_message[:100]}...' from session {session.get('session_id', 'unknown')[:8]}")
        
        # Validate input
        valid, clean_message, error = validate_chat_input(user_message)
        if not valid:
            return jsonify({'error': error}), 400
        
        # Validate location if provided
        location_context = None
        if location_data:
            loc_valid, clean_location, loc_error = validate_location_input(location_data)
            if loc_valid:
                location_context = clean_location
                print(f"📍 User location received: {clean_location.get('lat')}, {clean_location.get('lng')}")
                
                # Track location usage
                analytics = get_analytics_service()
                analytics.track_location_request(session.get('session_id'), clean_location, 'gps')
        
        # Initialize session if needed
        if 'chat_history' not in session:
            session['chat_history'] = []
            session['session_id'] = str(uuid.uuid4())
        
        print(f"🔄 Processing message from session {session['session_id'][:8]}")
        
        # Initialize RAG service
        rag = get_rag_service()
        
        # Build session context for AI
        session_context = {
            'session_id': session['session_id'],
            'chat_history': session['chat_history'][-10:],  # Last 10 exchanges for context
            'user_preferences': session.get('preferences', {}),
            'location': location_context,
            'timestamp': datetime.now().isoformat()
        }
        
        # Process message through RAG service
        start_time = datetime.now()
        print("🧠 Processing through RAG service...")
        
        ai_result = rag.process_message(clean_message, session_context)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️ Processing completed in {processing_time:.2f}s")
        print(f"🎯 Result - Intent: {ai_result.get('intent')}, Has Map: {bool(ai_result.get('map_html'))}")
        
        # Debug map data if present
        if ai_result.get('map_html'):
            print(f"🗺️ Map HTML length: {len(ai_result['map_html'])} characters")
            print(f"📍 Locations count: {len(ai_result.get('locations', []))}")
            if ai_result.get('locations'):
                first_location = ai_result['locations'][0]
                print(f"🔍 First location: {first_location.get('name')} at {first_location.get('lat')}, {first_location.get('lng')}")
        
        bot_response = ai_result.get('response', 'I apologize, but I encountered an issue processing your message.')
        
        # Store in session with metadata
        chat_entry = {
            'user': clean_message,
            'bot': bot_response,
            'timestamp': datetime.now().isoformat(),
            'intent': ai_result.get('intent', 'unknown'),
            'confidence': ai_result.get('confidence', 0.0),
            'sources': ai_result.get('sources', []),
            'has_location': location_context is not None,
            'has_map': bool(ai_result.get('map_html'))
        }
        
        session['chat_history'].append(chat_entry)
        
        # Limit chat history size to prevent session bloat
        if len(session['chat_history']) > 50:
            session['chat_history'] = session['chat_history'][-40:]  # Keep last 40
        
        # Track analytics
        analytics = get_analytics_service()
        analytics.track_message(
            clean_message, 
            ai_result, 
            processing_time,
            session['session_id']
        )
        
        # ENHANCED: Prepare comprehensive response with map support
        response_data = {
            'response': bot_response,
            'timestamp': chat_entry['timestamp'],
            'session_id': session['session_id'],
            'intent': ai_result.get('intent'),
            'confidence': ai_result.get('confidence'),
            'sources': ai_result.get('sources', []),
            'emergency': ai_result.get('emergency', False),
            'has_map': bool(ai_result.get('map_html'))
        }
        
        # CRITICAL: Add map data if available
        if ai_result.get('map_html'):
            response_data['map_html'] = ai_result['map_html']
            response_data['locations'] = ai_result.get('locations', [])
            response_data['search_location'] = ai_result.get('search_location')
            
            print(f"🗺️ Map included in response:")
            print(f"   - HTML length: {len(ai_result['map_html'])} chars")
            print(f"   - Locations: {len(ai_result.get('locations', []))}")
            print(f"   - Search location: {ai_result.get('search_location')}")
            
            # Additional debug info
            if ai_result.get('locations'):
                location_names = [loc.get('name', 'Unknown') for loc in ai_result['locations'][:3]]
                print(f"   - Location names: {location_names}")
        else:
            print("ℹ️ No map data in AI result")
            
            # Debug: Check if this should have had a map
            message_lower = clean_message.lower()
            if any(word in message_lower for word in ['hospital', 'nearest', 'find', 'where']):
                print("⚠️ This message might have needed a map but didn't get one")
        
        # Add suggestions for next interaction
        if len(session['chat_history']) > 1:
            try:
                suggestions = rag.get_chat_suggestions(session['chat_history'])
                response_data['suggestions'] = suggestions[:3]  # Limit to 3 suggestions
            except Exception as e:
                print(f"⚠️ Error getting suggestions: {e}")
        
        print(f"✅ Message processed successfully")
        print(f"📊 Final response stats:")
        print(f"   - Intent: {ai_result.get('intent')}")
        print(f"   - Confidence: {ai_result.get('confidence')}")
        print(f"   - Has Map: {response_data['has_map']}")
        print(f"   - Sources: {len(response_data.get('sources', []))}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Chat processing error: {e}")
        import traceback
        traceback.print_exc()
        
        # Enhanced fallback response
        error_response = {
            'response': """I apologize, but I'm experiencing technical difficulties right now. 

**For immediate assistance:**
• **Emergencies:** Call 911
• **Police:** 317-327-3811  
• **City Services:** 317-327-4622
• **Online:** Visit indy.gov

Please try again in a moment. Thank you for your patience!""",
            'timestamp': datetime.now().isoformat(),
            'session_id': session.get('session_id', 'unknown'),
            'error': True,
            'has_map': False,
            'sources': [
                {
                    'title': 'Indianapolis Emergency Services',
                    'url': 'https://www.indy.gov',
                    'type': 'fallback'
                }
            ]
        }
        
        return jsonify(error_response), 500

@chat_bp.route('/emergency-alert', methods=['POST'])
def send_emergency_alert():
    """Send emergency alert with user location"""
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        location_data = data.get('location', {})
        session_id = session.get('session_id', 'unknown')
        
        # Validate inputs
        if not user_message:
            return jsonify({'success': False, 'error': 'Message required'}), 400
        
        # Get notification service
        notification = get_notification_service()
        
        # Send emergency alert email
        alert_result = notification.send_emergency_alert(
            user_message, 
            location_data, 
            session_id
        )
        
        # Track emergency alert
        analytics = get_analytics_service()
        analytics.track_emergency_alert(
            session_id, 
            alert_result.get('success', False), 
            bool(location_data)
        )
        
        if alert_result['success']:
            print(f"🚨 Emergency alert sent for session {session_id}")
            return jsonify({
                'success': True,
                'message': 'Emergency alert sent to monitoring team',
                'alert_id': alert_result.get('alert_id'),
                'timestamp': datetime.now().isoformat()
            })
        else:
            print(f"❌ Emergency alert failed: {alert_result.get('error')}")
            return jsonify({
                'success': False,
                'error': 'Failed to send emergency alert',
                'details': alert_result.get('error')
            }), 500
            
    except Exception as e:
        print(f"❌ Emergency alert error: {e}")
        return jsonify({
            'success': False,
            'error': 'Emergency alert system error'
        }), 500

@chat_bp.route('/history')
def chat_history():
    """Get chat history for current session"""
    history = session.get('chat_history', [])
    return jsonify({
        'history': history,
        'session_id': session.get('session_id'),
        'count': len(history),
        'timestamp': datetime.now().isoformat()
    })

@chat_bp.route('/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    try:
        session['chat_history'] = []
        
        # Also clear RAG service session context if available
        rag = get_rag_service()
        rag.clear_session_context(session.get('session_id', ''))
        
        return jsonify({
            'message': 'Chat history cleared successfully',
            'timestamp': datetime.now().isoformat(),
            'session_id': session.get('session_id')
        })
    except Exception as e:
        print(f"❌ Error clearing chat: {e}")
        return jsonify({'error': 'Failed to clear chat history'}), 500

@chat_bp.route('/suggestions')
def get_suggestions():
    """Get contextual chat suggestions"""
    try:
        chat_history = session.get('chat_history', [])
        
        rag = get_rag_service()
        suggestions = rag.get_chat_suggestions(chat_history)
        
        return jsonify({
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ Error getting suggestions: {e}")
        return jsonify({'suggestions': [
            "How do I report a pothole?",
            "Emergency contact numbers", 
            "Find nearest hospital",
            "Weather alerts for Indianapolis"
        ]})

@chat_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback on AI responses"""
    try:
        data = request.get_json()
        message_id = data.get('message_id')
        feedback_type = data.get('feedback_type')  # 'helpful', 'not_helpful', 'incorrect'
        details = data.get('details', '')
        
        if not message_id or not feedback_type:
            return jsonify({'error': 'Missing required feedback data'}), 400
        
        rag = get_rag_service()
        result = rag.process_feedback(message_id, feedback_type, details)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Feedback submission error: {e}")
        return jsonify({'error': 'Failed to submit feedback'}), 500

@chat_bp.route('/system-status')
def system_status():
    """Get AI system status"""
    try:
        rag = get_rag_service()
        status = rag.get_system_status()
        
        return jsonify(status)
        
    except Exception as e:
        print(f"❌ System status error: {e}")
        return jsonify({
            'overall_status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        })

# DEBUG ENDPOINTS for troubleshooting map issues

@chat_bp.route('/debug/test-map', methods=['GET', 'POST'])
def test_map():
    """
    DEBUG: Test map generation functionality
    """
    try:
        # Get test parameters
        if request.method == 'POST':
            data = request.get_json()
            test_message = data.get('message', 'find nearest hospital')
            test_location = data.get('location')
        else:
            test_message = request.args.get('message', 'find nearest hospital')
            test_location = None
        
        print(f"🧪 Testing map generation for: '{test_message}'")
        
        # Initialize RAG service
        rag = get_rag_service()
        
        # Build test session context
        session_context = {
            'session_id': 'test-session',
            'location': test_location,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test map generation debugging
        debug_result = rag.debug_map_generation(test_message, session_context)
        
        return jsonify({
            'success': True,
            'test_message': test_message,
            'debug_info': debug_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@chat_bp.route('/debug/test-hospitals')
def test_hospitals():
    """
    DEBUG: Test hospital search specifically
    """
    try:
        # Get coordinates from query params
        lat = float(request.args.get('lat', 39.7684))
        lng = float(request.args.get('lng', -86.1581))
        
        print(f"🏥 Testing hospital search at {lat}, {lng}")
        
        rag = get_rag_service()
        result = rag.test_hospital_search(lat, lng)
        
        return jsonify({
            'success': True,
            'test_coordinates': {'lat': lat, 'lng': lng},
            'hospital_search_result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_bp.route('/debug/config-check')
def config_check():
    """
    DEBUG: Check API configuration
    """
    config_status = {}
    
    # Check Google Maps API key
    try:
        from flask import current_app
        gmaps_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
        config_status['google_maps'] = {
            'configured': bool(gmaps_key),
            'key_length': len(gmaps_key) if gmaps_key else 0,
            'key_preview': gmaps_key[:10] + '...' if gmaps_key else None
        }
    except Exception as e:
        config_status['google_maps'] = {'configured': False, 'error': str(e)}
    
    # Check other API keys
    try:
        config_status['groq'] = {'configured': bool(current_app.config.get('GROQ_API_KEY'))}
        config_status['perplexity'] = {'configured': bool(current_app.config.get('PERPLEXITY_API_KEY'))}
    except Exception as e:
        config_status['api_check_error'] = str(e)
    
    # Check RAG service status
    try:
        rag = get_rag_service()
        system_status = rag.get_system_status()
        config_status['rag_system'] = system_status
    except Exception as e:
        config_status['rag_system'] = {'error': str(e)}
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'config_status': config_status
    })

@chat_bp.route('/debug/process-message', methods=['POST'])
def debug_process_message():
    """
    DEBUG: Process a message with full debugging output
    """
    try:
        data = request.get_json()
        test_message = data.get('message', 'find nearest hospital')
        test_location = data.get('location')
        
        print(f"🔍 DEBUG: Processing message '{test_message}'")
        
        # Build session context
        session_context = {
            'session_id': 'debug-session',
            'chat_history': [],
            'location': test_location,
            'timestamp': datetime.now().isoformat()
        }
        
        # Process through RAG service
        rag = get_rag_service()
        start_time = datetime.now()
        
        result = rag.process_message(test_message, session_context)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Return comprehensive debug info
        return jsonify({
            'success': True,
            'processing_time': processing_time,
            'input': {
                'message': test_message,
                'location': test_location
            },
            'output': {
                'intent': result.get('intent'),
                'confidence': result.get('confidence'),
                'has_map_html': bool(result.get('map_html')),
                'map_html_length': len(result.get('map_html', '')),
                'locations_count': len(result.get('locations', [])),
                'response_length': len(result.get('response', '')),
                'sources_count': len(result.get('sources', [])),
                'emergency': result.get('emergency', False)
            },
            'debug_data': {
                'result_keys': list(result.keys()),
                'sample_locations': [
                    {
                        'name': loc.get('name'),
                        'lat': loc.get('lat'),
                        'lng': loc.get('lng')
                    }
                    for loc in result.get('locations', [])[:3]
                ] if result.get('locations') else []
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500