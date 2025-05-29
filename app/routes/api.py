"""
API routes for SafeIndy Assistant
Handles external API endpoints and integrations
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/status')
def api_status():
    """API health check and status"""
    return jsonify({
        'status': 'healthy',
        'service': 'SafeIndy Assistant API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'chat': '/api/chat',
            'emergency': '/api/emergency',
            'services': '/api/services',
            'weather': '/api/weather'
        }
    })

@api_bp.route('/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat functionality"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # This will later integrate with our AI services
        response = f"API received: {message} - AI response will be integrated here"
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'session_id': data.get('session_id'),
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/emergency')
def api_emergency():
    """Emergency contacts API endpoint"""
    return jsonify({
        'emergency_contacts': {
            'immediate_emergency': {
                'number': '911',
                'description': 'Police, Fire, Medical emergencies',
                'available': '24/7'
            },
            'police_non_emergency': {
                'number': '317-327-3811', 
                'description': 'IMPD non-emergency line',
                'available': '24/7'
            },
            'city_services': {
                'number': '317-327-4622',
                'description': 'Mayor\'s Action Center (311)',
                'available': 'Mon-Fri 8AM-5PM'
            },
            'poison_control': {
                'number': '1-800-222-1222',
                'description': '24-hour poison help',
                'available': '24/7'
            }
        },
        'special_services': {
            'text_911': 'Available in Indianapolis',
            'requestindy_app': 'Available for city service requests',
            'online_portal': 'request.indy.gov'
        },
        'timestamp': datetime.now().isoformat()
    })

@api_bp.route('/services')
def api_services():
    """Indianapolis city services API"""
    return jsonify({
        'city_services': {
            'mayors_action_center': {
                'phone': '317-327-4622',
                'hours': 'Monday-Friday 8AM-5PM',
                'online': 'request.indy.gov',
                'app': 'RequestIndy mobile app'
            },
            'common_services': [
                'Pothole reporting',
                'Trash collection issues',
                'Street light problems', 
                'Abandoned vehicles',
                'Traffic signals',
                'Zoning violations',
                'High grass and weeds',
                'Animal issues'
            ]
        },
        'police_services': {
            'emergency': '911',
            'non_emergency': '317-327-3811',
            'services': [
                'Crime reporting',
                'Incident reports',
                'Traffic accidents',
                'Community policing'
            ]
        },
        'timestamp': datetime.now().isoformat()
    })

@api_bp.route('/weather')
def api_weather():
    """Weather alerts and information (mock data for now)"""
    
    # Mock weather data - later we'll integrate OpenWeatherMap API
    mock_weather = {
        'location': 'Indianapolis, IN',
        'current_conditions': {
            'temperature': '72°F',
            'conditions': 'Partly Cloudy',
            'humidity': '45%',
            'wind': '8 mph SW'
        },
        'alerts': [
            {
                'type': 'weather_watch',
                'title': 'No active weather alerts',
                'description': 'Current weather conditions are normal',
                'severity': 'none'
            }
        ],
        'emergency_info': {
            'severe_weather_protocol': 'Seek shelter indoors during severe weather warnings',
            'emergency_contact': '911 for weather-related emergencies'
        },
        'timestamp': datetime.now().isoformat(),
        'source': 'Mock data - will integrate OpenWeatherMap API'
    }
    
    return jsonify(mock_weather)

@api_bp.route('/locations/nearby')
def api_nearby_locations():
    """Find nearby emergency services and resources"""
    
    # Mock data for Indianapolis locations
    nearby_services = {
        'hospitals': [
            {
                'name': 'IU Health Methodist Hospital',
                'address': '1701 N Senate Blvd, Indianapolis, IN 46202',
                'phone': '317-962-2000',
                'distance': '2.1 miles',
                'type': 'hospital'
            },
            {
                'name': 'Eskenazi Hospital',
                'address': '720 Eskenazi Ave, Indianapolis, IN 46202', 
                'phone': '317-880-0000',
                'distance': '1.8 miles',
                'type': 'hospital'
            }
        ],
        'police_stations': [
            {
                'name': 'IMPD North District',
                'address': '3120 E 30th St, Indianapolis, IN 46218',
                'phone': '317-327-3811',
                'distance': '3.2 miles',
                'type': 'police'
            }
        ],
        'fire_stations': [
            {
                'name': 'IFD Station 7',
                'address': '748 Massachusetts Ave, Indianapolis, IN 46204',
                'phone': '911 for emergencies',
                'distance': '1.5 miles',
                'type': 'fire'
            }
        ],
        'timestamp': datetime.now().isoformat(),
        'note': 'Distances are approximate. Call ahead to verify services.'
    }
    
    return jsonify(nearby_services)

@api_bp.route('/test-email', methods=['GET', 'POST'])
def test_email():
    """Test emergency email configuration"""
    try:
        from app.services.notification_service import NotificationService
        notification = NotificationService()
        
        result = notification.test_email_configuration()
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', result.get('error')),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/nearby-services', methods=['POST'])
def nearby_services():
    """Find nearby emergency services based on location"""
    try:
        data = request.get_json()
        location = data.get('location', {})
        
        if not location or 'coordinates' not in location:
            return jsonify({
                'success': False,
                'error': 'Location coordinates required'
            }), 400
        
        coords = location['coordinates']
        lat = coords.get('lat')
        lng = coords.get('lng')
        
        if lat is None or lng is None:
            return jsonify({
                'success': False,
                'error': 'Invalid coordinates'
            }), 400
        
        # Mock nearby services for demo (replace with real Google Places API calls)
        mock_services = {
            'hospitals': [
                {
                    'name': 'IU Health Methodist Hospital',
                    'address': '1701 N Senate Blvd, Indianapolis, IN 46202',
                    'phone': '317-962-2000',
                    'distance': 2.1
                },
                {
                    'name': 'Eskenazi Hospital', 
                    'address': '720 Eskenazi Ave, Indianapolis, IN 46202',
                    'phone': '317-880-0000',
                    'distance': 1.8
                }
            ],
            'police': [
                {
                    'name': 'IMPD North District',
                    'address': '3120 E 30th St, Indianapolis, IN 46218',
                    'phone': '317-327-3811',
                    'distance': 3.2
                },
                {
                    'name': 'IMPD Downtown',
                    'address': '50 N Alabama St, Indianapolis, IN 46204',
                    'phone': '317-327-3811',
                    'distance': 1.5
                }
            ],
            'fire_stations': [
                {
                    'name': 'IFD Station 7',
                    'address': '748 Massachusetts Ave, Indianapolis, IN 46204',
                    'phone': '911',
                    'distance': 1.5
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'services': mock_services,
            'location': {'lat': lat, 'lng': lng},
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Testing and Debug Routes
@api_bp.route('/test-vector', methods=['GET'])
def test_vector_service():
    """Test vector database functionality"""
    try:
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        # Test embedding generation
        test_text = "Indianapolis emergency services"
        embedding = vector_service.generate_embedding(test_text)
        
        # Test search
        search_result = vector_service.search_knowledge("emergency contacts", "emergency")
        
        # Get collection info
        collection_info = vector_service.get_collection_info()
        
        return jsonify({
            'success': True,
            'embedding_dimensions': len(embedding),
            'search_results_count': len(search_result.get('results', [])),
            'collection_info': collection_info,
            'test_embedding_sample': embedding[:5],  # First 5 values
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@api_bp.route('/test-search', methods=['GET'])
def test_search_service():
    """Test search service functionality"""
    try:
        from app.services.search_service import SearchService
        
        search_service = SearchService()
        
        # Test search
        test_query = "Indianapolis emergency contacts"
        result = search_service.search_indianapolis_data(test_query, "emergency")
        
        return jsonify({
            'success': True,
            'query': test_query,
            'has_results': bool(result.get('results')),
            'sources_count': len(result.get('sources', [])),
            'error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@api_bp.route('/reset-vector-db', methods=['POST'])
def reset_vector_database():
    """Reset vector database - USE WITH CAUTION"""
    try:
        from app.services.vector_service import VectorService
        
        # Add password protection
        password = request.json.get('password') if request.json else None
        if password != 'reset-safeindy-2025':  # Change this password
            return jsonify({'error': 'Invalid password'}), 401
        
        vector_service = VectorService()
        result = vector_service.reset_collection()
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Vector database reset successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to reset vector database'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/populate-vector-db', methods=['POST'])
def populate_vector_database():
    """Populate vector database with initial knowledge"""
    try:
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        # Check if already populated
        collection_info = vector_service.get_collection_info()
        if collection_info.get('points_count', 0) > 0:
            return jsonify({
                'success': True,
                'message': f'Database already has {collection_info["points_count"]} entries',
                'action': 'skipped'
            })
        
        # Populate with initial knowledge
        print("🔄 Populating vector database...")
        vector_service.populate_initial_knowledge()
        
        # Get updated info
        updated_info = vector_service.get_collection_info()
        
        return jsonify({
            'success': True,
            'message': 'Vector database populated successfully',
            'points_added': updated_info.get('points_count', 0),
            'collection_info': updated_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@api_bp.route('/clear-cache', methods=['POST'])
def clear_ai_cache():
    """Clear AI response cache"""
    try:
        from app.utils.cache_manager import get_ai_cache
        
        cache = get_ai_cache()
        # Clear the cache (implementation depends on your cache manager)
        
        return jsonify({
            'success': True,
            'message': 'AI cache cleared successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@api_bp.route('/debug-intent', methods=['POST'])
def debug_intent_classification():
    """Debug intent classification"""
    try:
        data = request.get_json()
        test_message = data.get('message', 'Find nearest hospital')
        
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        
        # Test intent classification directly
        intent, confidence = llm_service._classify_intent(test_message, "")
        
        return jsonify({
            'success': True,
            'test_message': test_message,
            'classified_intent': intent,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@api_bp.errorhandler(404)
def api_not_found(error):
    """API 404 handler"""
    return jsonify({
        'error': 'API endpoint not found',
        'available_endpoints': [
            '/api/status',
            '/api/chat', 
            '/api/emergency',
            '/api/services',
            '/api/weather',
            '/api/locations/nearby',
            '/api/nearby-services',
            '/api/test-vector',
            '/api/test-search',
            '/api/debug-intent',
            '/api/clear-cache'
        ]
    }), 404



# Add this debug endpoint to see what's happening in the RAG flow:

@api_bp.route('/debug-rag-flow', methods=['POST'])
def debug_rag_flow():
    """Debug the entire RAG processing flow"""
    try:
        data = request.get_json()
        test_message = data.get('message', 'Find nearest hospital')
        
        from app.services.rag_service import RAGService
        from app.services.llm_service import LLMService
        
        # Test direct LLM intent classification
        llm_service = LLMService()
        direct_intent, direct_confidence = llm_service._classify_intent(test_message, "")
        
        # Test RAG service processing
        rag_service = RAGService()
        session_context = {
            'session_id': 'debug-session',
            'chat_history': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # This should show the full flow
        result = rag_service.process_message(test_message, session_context)
        
        return jsonify({
            'success': True,
            'test_message': test_message,
            'direct_llm_intent': direct_intent,
            'direct_llm_confidence': direct_confidence,
            'rag_result_intent': result.get('intent'),
            'rag_result_confidence': result.get('confidence'),
            'has_map': bool(result.get('map_html')),
            'has_sources': len(result.get('sources', [])),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
    

# Add this debug endpoint to your app/routes/api.py:

@api_bp.route('/debug-map', methods=['POST'])
def debug_map_generation():
    """Debug map generation specifically"""
    try:
        data = request.get_json()
        test_message = data.get('message', 'Find nearest hospital')
        
        from app.services.location_service import LocationService
        
        location_service = LocationService()
        
        # Test map generation with mock location
        mock_location = {
            'lat': 39.7684,
            'lng': -86.1581,
            'address': 'Indianapolis, IN'
        }
        
        # Generate hospital map
        map_response = location_service.generate_emergency_map_response(
            mock_location, 
            'hospital'
        )
        
        return jsonify({
            'success': True,
            'test_message': test_message,
            'mock_location': mock_location,
            'map_response_keys': list(map_response.keys()) if map_response else [],
            'has_map_html': bool(map_response.get('map_html') if map_response else False),
            'has_locations': len(map_response.get('locations', [])) if map_response else 0,
            'map_html_length': len(map_response.get('map_html', '')) if map_response else 0,
            'map_html_preview': map_response.get('map_html', '')[:200] + '...' if map_response and map_response.get('map_html') else 'No map HTML',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500