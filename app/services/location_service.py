"""
FIXED Location Service for SafeIndy Assistant
Handles Google Maps API integration with proper hospital location mapping
"""

import requests
from flask import current_app
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

class LocationService:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.indianapolis_bounds = {
            'northeast': {'lat': 39.9276, 'lng': -85.9383},
            'southwest': {'lat': 39.6344, 'lng': -86.3755}
        }
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Google Maps client with API key"""
        try:
            self.api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
            if not self.api_key:
                raise ValueError("GOOGLE_MAPS_API_KEY not found in configuration")
            print("✅ Google Maps client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Google Maps client: {e}")
    
    def find_nearby_places(self, lat: float, lng: float, place_type: str, radius: int = 10000) -> Dict:
        """
        FIXED: Find nearby places with proper error handling and data formatting
        """
        if not self.api_key:
            return {'error': 'Google Maps API not configured', 'places': []}
        
        try:
            url = f"{self.base_url}/place/nearbysearch/json"
            params = {
                'location': f"{lat},{lng}",
                'radius': radius,
                'type': place_type,
                'key': self.api_key
            }
            
            print(f"🔍 Searching for {place_type} near {lat},{lng} within {radius}m")
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            print(f"📍 Google Places API Status: {data.get('status')}")
            print(f"📍 Found {len(data.get('results', []))} raw results")
            
            if data['status'] == 'OK':
                places = []
                
                for place in data.get('results', []):
                    # Extract coordinates properly
                    geometry = place.get('geometry', {})
                    location_data = geometry.get('location', {})
                    
                    if not location_data.get('lat') or not location_data.get('lng'):
                        print(f"⚠️ Skipping place {place.get('name')} - missing coordinates")
                        continue
                    
                    # Calculate distance
                    distance = self._calculate_distance(
                        lat, lng, 
                        location_data['lat'],
                        location_data['lng']
                    )
                    
                    # Format place data consistently
                    place_info = {
                        'name': place.get('name', 'Unknown Location'),
                        'address': place.get('vicinity', place.get('formatted_address', 'Address unavailable')),
                        'lat': float(location_data['lat']),  # Ensure float type
                        'lng': float(location_data['lng']),  # Ensure float type
                        'coordinates': {
                            'lat': float(location_data['lat']),
                            'lng': float(location_data['lng'])
                        },
                        'place_id': place.get('place_id'),
                        'rating': place.get('rating'),
                        'types': place.get('types', []),
                        'open_now': place.get('opening_hours', {}).get('open_now'),
                        'distance': distance,
                        'type': place_type,  # Add type for marker icon selection
                        'phone': None  # Will be filled by place details if needed
                    }
                    
                    # Get additional details if place_id available
                    if place_info['place_id'] and place_type == 'hospital':
                        details = self.get_place_details(place_info['place_id'])
                        if details.get('success'):
                            place_info['phone'] = details.get('phone')
                            if details.get('address'):
                                place_info['address'] = details['address']
                    
                    places.append(place_info)
                    print(f"✅ Added: {place_info['name']} at {place_info['lat']},{place_info['lng']}")
                
                # Sort by distance
                places.sort(key=lambda x: x['distance'])
                
                print(f"🏥 Successfully processed {len(places)} {place_type} locations")
                
                return {
                    'success': True,
                    'places': places,
                    'total_results': len(places),
                    'search_location': {'lat': lat, 'lng': lng},
                    'search_type': place_type,
                    'radius': radius
                }
            else:
                error_msg = f"Places search failed: {data.get('status', 'Unknown error')}"
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'places': []
                }
                
        except Exception as e:
            print(f"❌ Places search error: {e}")
            return {
                'success': False, 
                'error': str(e),
                'places': []
            }
    
    def get_place_details(self, place_id: str) -> Dict:
        """Get detailed information about a specific place"""
        if not self.api_key:
            return {'success': False, 'error': 'Google Maps API not configured'}
        
        try:
            url = f"{self.base_url}/place/details/json"
            params = {
                'place_id': place_id,
                'fields': 'name,formatted_address,formatted_phone_number,opening_hours,rating,website,geometry',
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == 'OK':
                result = data['result']
                return {
                    'success': True,
                    'name': result.get('name'),
                    'address': result.get('formatted_address'),
                    'phone': result.get('formatted_phone_number'),
                    'website': result.get('website'),
                    'rating': result.get('rating'),
                    'coordinates': result.get('geometry', {}).get('location'),
                    'opening_hours': result.get('opening_hours', {}).get('weekday_text', []),
                    'open_now': result.get('opening_hours', {}).get('open_now')
                }
            else:
                return {
                    'success': False,
                    'error': f"Place details failed: {data.get('status', 'Unknown error')}"
                }
        except Exception as e:
            print(f"❌ Place details error: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_embedded_map(self, locations: List[Dict], center_location: Dict = None, map_type: str = "emergency") -> str:
        """
        FIXED: Generate HTML for embedded Google Map with proper marker handling
        """
        print(f"🗺️ Generating map with {len(locations)} locations")
        
        # Debug: Print first location to verify data structure
        if locations:
            print(f"🔍 Sample location data: {locations[0]}")
        
        # Default center to Indianapolis if not provided
        if not center_location:
            center_location = {'lat': 39.7684, 'lng': -86.1581}
        
        # Validate and clean location data
        valid_locations = []
        for loc in locations:
            if self._validate_location_data(loc):
                valid_locations.append(loc)
            else:
                print(f"⚠️ Invalid location data: {loc}")
        
        if not valid_locations:
            return f'<div class="map-error">No valid locations found for map display</div>'
        
        print(f"✅ {len(valid_locations)} valid locations for map")
        
        # Generate map markers JavaScript
        markers_js = self._generate_markers_javascript(valid_locations)
        
        # Map styling based on type
        map_styles = self._get_map_styles(map_type)
        
        # Generate unique map ID to avoid conflicts
        map_id = f"safeindy-map-{datetime.now().strftime('%H%M%S')}"
        
        map_html = f"""
        <div class="embedded-map-container" style="width: 100%; height: 400px; margin: 15px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div id="{map_id}" style="width: 100%; height: 100%;"></div>
            <div class="map-info" style="background: #e3f2fd; border: 1px solid #bbdefb; padding: 10px; margin: 10px 0; border-radius: 6px; font-size: 14px;">
                📍 Found {len(valid_locations)} locations • Click markers for details and directions
            </div>
        </div>
        
        <script>
            function initSafeIndyMap_{map_id.replace('-', '_')}() {{
                console.log('🗺️ Initializing map with center:', {center_location});
                
                // Initialize map
                const map = new google.maps.Map(document.getElementById('{map_id}'), {{
                    zoom: 12,
                    center: {{ lat: {center_location['lat']}, lng: {center_location['lng']} }},
                    styles: {map_styles},
                    mapTypeControl: true,
                    streetViewControl: false,
                    fullscreenControl: true,
                    zoomControl: true
                }});
                
                console.log('✅ Map initialized successfully');
                
                // Add markers
                {markers_js}
                
                console.log('📍 Added', markers.length, 'markers to map');
                
                // Fit map to show all markers if multiple
                if (markers.length > 1) {{
                    const bounds = new google.maps.LatLngBounds();
                    markers.forEach(marker => bounds.extend(marker.getPosition()));
                    map.fitBounds(bounds);
                    
                    // Ensure minimum zoom level
                    google.maps.event.addListenerOnce(map, 'bounds_changed', function() {{
                        if (map.getZoom() > 15) {{
                            map.setZoom(15);
                        }}
                    }});
                }} else if (markers.length === 1) {{
                    // Single marker - center on it with appropriate zoom
                    map.setCenter(markers[0].getPosition());
                    map.setZoom(14);
                }}
            }}
            
            // Initialize map when ready
            if (typeof google !== 'undefined' && google.maps) {{
                console.log('🗺️ Google Maps API already loaded, initializing...');
                initSafeIndyMap_{map_id.replace('-', '_')}();
            }} else {{
                console.log('🗺️ Loading Google Maps API...');
                const script = document.createElement('script');
                script.src = 'https://maps.googleapis.com/maps/api/js?key={self.api_key}&callback=initSafeIndyMap_{map_id.replace('-', '_')}';
                script.async = true;
                script.defer = true;
                script.onerror = function() {{
                    console.error('❌ Failed to load Google Maps API');
                    document.getElementById('{map_id}').innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Map loading failed. Please refresh the page.</div>';
                }};
                document.head.appendChild(script);
            }}
        </script>
        """
        
        return map_html
    
    def _validate_location_data(self, location: Dict) -> bool:
        """Validate that location has required data for mapping"""
        required_fields = ['lat', 'lng', 'name']
        
        for field in required_fields:
            if field not in location:
                print(f"❌ Missing required field '{field}' in location: {location.get('name', 'Unknown')}")
                return False
        
        # Validate coordinate types and ranges
        try:
            lat = float(location['lat'])
            lng = float(location['lng'])
            
            if not (-90 <= lat <= 90):
                print(f"❌ Invalid latitude {lat} for {location['name']}")
                return False
                
            if not (-180 <= lng <= 180):
                print(f"❌ Invalid longitude {lng} for {location['name']}")
                return False
                
        except (ValueError, TypeError):
            print(f"❌ Invalid coordinate format for {location.get('name', 'Unknown')}")
            return False
        
        return True
    
    def _generate_markers_javascript(self, locations: List[Dict]) -> str:
        """FIXED: Generate JavaScript code for map markers with proper error handling"""
        
        markers_code = """
        const markers = [];
        const infoWindows = [];
        
        console.log('📍 Creating markers for', """ + str(len(locations)) + """ , 'locations');
        """
        
        for i, location in enumerate(locations):
            # Validate location data before processing
            if not self._validate_location_data(location):
                continue
                
            # Get marker icon info
            icon_info = self._get_marker_icon(location.get('type', 'general'))
            
            # Safely escape strings for JavaScript
            name = self._escape_js_string(location.get('name', 'Location'))
            address = self._escape_js_string(location.get('address', ''))
            phone = self._escape_js_string(location.get('phone', ''))
            
            # Create info window content
            info_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 280px; padding: 5px;">
                <h3 style="margin: 0 0 8px 0; color: #1a73e8; font-size: 16px; font-weight: bold;">{name}</h3>
                <p style="margin: 4px 0; color: #5f6368; font-size: 13px; line-height: 1.4;">📍 {address}</p>
                {f'<p style="margin: 4px 0; color: #5f6368; font-size: 13px;"><a href="tel:{phone}" style="color: #1a73e8; text-decoration: none;">📞 {phone}</a></p>' if phone else ''}
                <div style="margin-top: 10px; display: flex; gap: 8px;">
                    <a href="https://www.google.com/maps/dir/?api=1&destination={location['lat']},{location['lng']}" 
                    target="_blank" 
                    style="background: #1a73e8; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-size: 12px; font-weight: bold;">
                    🧭 Directions
                    </a>
                    <a href="https://www.google.com/maps/place/?q=place_id:{location.get('place_id', '')}" 
                    target="_blank" 
                    style="background: #34a853; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-size: 12px; font-weight: bold;">
                    📋 Details
                    </a>
                </div>
            </div>
            """.replace('\n', ' ').strip()
            
            # Escape the info content for JavaScript
            info_content = self._escape_js_string(info_content)
            
            markers_code += f"""
            try {{
                console.log('Creating marker {i + 1}: {name} at', {location['lat']}, {location['lng']});
                
                const marker{i} = new google.maps.Marker({{
                    position: {{ lat: {location['lat']}, lng: {location['lng']} }},
                    map: map,
                    title: '{name}',
                    icon: {{
                        url: '{icon_info['url']}',
                        scaledSize: new google.maps.Size({icon_info['size']}, {icon_info['size']}),
                        origin: new google.maps.Point(0, 0),
                        anchor: new google.maps.Point({icon_info['size']//2}, {icon_info['size']})
                    }},
                    optimized: false
                }});
                
                const infoWindow{i} = new google.maps.InfoWindow({{
                    content: '{info_content}',
                    maxWidth: 300
                }});
                
                marker{i}.addListener('click', function() {{
                    console.log('Marker clicked:', '{name}');
                    
                    // Close all other info windows
                    infoWindows.forEach(function(window) {{
                        window.close();
                    }});
                    
                    infoWindow{i}.open(map, marker{i});
                }});
                
                markers.push(marker{i});
                infoWindows.push(infoWindow{i});
                
                console.log('✅ Marker {i + 1} created successfully');
                
            }} catch (error) {{
                console.error('❌ Error creating marker {i + 1}:', error);
            }}
            """
        
        markers_code += """
        console.log('📍 Total markers created:', markers.length);
        """
        
        return markers_code
    
    def _escape_js_string(self, text: str) -> str:
        """Escape string for safe JavaScript usage"""
        if not text:
            return ''
        
        # Replace problematic characters
        text = str(text)
        text = text.replace('\\', '\\\\')  # Escape backslashes
        text = text.replace("'", "\\'")    # Escape single quotes
        text = text.replace('"', '\\"')    # Escape double quotes
        text = text.replace('\n', '\\n')   # Escape newlines
        text = text.replace('\r', '\\r')   # Escape carriage returns
        text = text.replace('\t', '\\t')   # Escape tabs
        
        return text
    
    def _get_marker_icon(self, location_type: str) -> Dict:
        """Get appropriate marker icon for location type"""
        
        icons = {
            'hospital': {
                'url': 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
                'size': 32
            },
            'police': {
                'url': 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png', 
                'size': 32
            },
            'fire_station': {
                'url': 'https://maps.google.com/mapfiles/ms/icons/orange-dot.png',
                'size': 32
            },
            'emergency': {
                'url': 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
                'size': 32
            },
            'general': {
                'url': 'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
                'size': 32
            }
        }
        
        return icons.get(location_type, icons['general'])

    def _get_map_styles(self, map_type: str) -> str:
        """Get map styling based on map type"""
        
        if map_type in ['emergency', 'hospital', 'police']:
            return """[
                {
                    "featureType": "poi.medical",
                    "stylers": [{"visibility": "on"}, {"color": "#ff4444"}]
                },
                {
                    "featureType": "poi.government", 
                    "stylers": [{"visibility": "on"}, {"color": "#4444ff"}]
                },
                {
                    "featureType": "road.highway",
                    "stylers": [{"color": "#ffaa00"}]
                }
            ]"""
        
        return """[
            {
                "featureType": "poi.business",
                "stylers": [{"visibility": "off"}]
            },
            {
                "featureType": "transit",
                "stylers": [{"visibility": "simplified"}]
            }
        ]"""

    def generate_emergency_map_response(self, user_location: Dict = None, emergency_type: str = "general") -> Dict:
        """
        FIXED: Generate complete response with embedded map for emergency services
        """
        print(f"🗺️ Generating emergency map response for type: {emergency_type}")
        
        # Use user location or default to Indianapolis center
        if user_location and user_location.get('lat') and user_location.get('lng'):
            search_location = user_location
            print(f"📍 Using user location: {search_location['lat']}, {search_location['lng']}")
        else:
            search_location = {'lat': 39.7684, 'lng': -86.1581, 'address': 'Indianapolis, IN'}
            print("📍 Using default Indianapolis location")
        
        # Find emergency services based on type
        places_result = {'success': False, 'places': []}
        
        if emergency_type == 'hospital':
            print("🏥 Searching for hospitals...")
            places_result = self.find_nearby_places(
                search_location['lat'], 
                search_location['lng'], 
                'hospital', 
                radius=15000  # Increased radius to find more hospitals
            )
            service_name = "hospitals"
            
        elif emergency_type == 'police':
            print("👮 Getting police districts...")
            # Use predefined police districts for better coverage
            districts = self.get_indianapolis_districts()
            places_result = {
                'success': True,
                'places': [
                    {
                        'name': d['name'],
                        'address': d['address'],
                        'lat': d['coordinates']['lat'],
                        'lng': d['coordinates']['lng'],
                        'coordinates': d['coordinates'],
                        'phone': d['phone'],
                        'type': 'police',
                        'distance': self._calculate_distance(
                            search_location['lat'], search_location['lng'],
                            d['coordinates']['lat'], d['coordinates']['lng']
                        )
                    } for d in districts
                ]
            }
            service_name = "police stations"
            
        elif emergency_type == 'fire':
            print("🚒 Searching for fire stations...")
            places_result = self.find_nearby_places(
                search_location['lat'], 
                search_location['lng'], 
                'fire_station', 
                radius=15000
            )
            service_name = "fire stations"
            
        else:  # general emergency
            print("🚨 Searching for general emergency services...")
            emergency_services = self.find_emergency_services(
                search_location['lat'], 
                search_location['lng']
            )
            
            # Combine all emergency services
            all_services = []
            if emergency_services.get('success'):
                services = emergency_services['emergency_services']
                for category, places in services.items():
                    for place in places[:2]:  # Limit to 2 per category
                        place['type'] = category.rstrip('s')
                        all_services.append(place)
            
            places_result = {'success': True, 'places': all_services}
            service_name = "emergency services"
        
        print(f"🔍 Places search result: {places_result.get('success')}, found {len(places_result.get('places', []))} places")
        
        if not places_result.get('success') or not places_result.get('places'):
            return {
                'response': f"I couldn't find nearby {service_name} at the moment. For immediate emergencies, call 911.",
                'map_html': '<div class="map-error">Unable to load map at this time. For emergencies, call 911.</div>',
                'locations': []
            }
        
        # Sort by distance and limit results
        locations = sorted(places_result['places'], key=lambda x: x.get('distance', 0))[:5]
        
        print(f"📍 Final locations for map: {len(locations)}")
        for loc in locations:
            print(f"  - {loc['name']}: {loc['lat']},{loc['lng']}")
        
        # Generate embedded map
        map_html = self.generate_embedded_map(locations, search_location, emergency_type)
        
        # Generate response text
        response_text = self._generate_location_response_text(locations, service_name, search_location)
        
        return {
            'response': response_text,
            'map_html': map_html,
            'locations': locations,
            'search_location': search_location,
            'service_type': emergency_type
        }

    def _generate_location_response_text(self, locations: List[Dict], service_name: str, search_location: Dict) -> str:
        """Generate text response for location-based queries"""
        
        if not locations:
            return f"No {service_name} found in your area. For emergencies, call 911 immediately."
        
        # Build response with nearest locations
        response = f"📍 **Nearest {service_name.title()}**\n\n"
        
        for i, location in enumerate(locations[:3], 1):
            name = location.get('name', 'Unknown')
            address = location.get('address', 'Address unavailable')
            phone = location.get('phone', '')
            distance = location.get('distance', 0)
            
            response += f"**{i}. {name}**\n"
            response += f"📍 {address}\n"
            if phone:
                response += f"📞 {phone}\n"
            if distance:
                response += f"🚗 {distance:.1f} km away\n"
            response += "\n"
        
        # Add emergency reminder
        response += "🚨 **For life-threatening emergencies, call 911 immediately**\n\n"
        
        # Add map interaction note
        response += "💡 **Click any marker on the map above for directions and details.**"
        
        return response

    # Add the remaining helper methods...
    def find_emergency_services(self, lat: float, lng: float) -> Dict:
        """Find nearby emergency services"""
        emergency_services = {
            'hospitals': [],
            'police': [],
            'fire_stations': []
        }
        
        service_types = {
            'hospitals': 'hospital',
            'police': 'police',
            'fire_stations': 'fire_station'
        }
        
        for category, place_type in service_types.items():
            try:
                results = self.find_nearby_places(lat, lng, place_type, radius=15000)
                if results.get('success'):
                    emergency_services[category] = results.get('places', [])[:3]
            except Exception as e:
                print(f"❌ Error finding {category}: {e}")
        
        return {
            'success': True,
            'emergency_services': emergency_services,
            'location': {'lat': lat, 'lng': lng},
            'timestamp': datetime.now().isoformat()
        }

    def get_indianapolis_districts(self) -> List[Dict]:
        """Get Indianapolis police districts"""
        districts = [
            {
                'name': 'North District',
                'address': '3120 E 30th St, Indianapolis, IN 46218',
                'phone': '317-327-3811',
                'coordinates': {'lat': 39.8234, 'lng': -86.1281}
            },
            {
                'name': 'East District', 
                'address': '201 N Shadeland Ave, Indianapolis, IN 46219',
                'phone': '317-327-3811',
                'coordinates': {'lat': 39.7756, 'lng': -86.0344}
            },
            {
                'name': 'South District',
                'address': '4930 Shelby St, Indianapolis, IN 46227', 
                'phone': '317-327-3811',
                'coordinates': {'lat': 39.6898, 'lng': -86.1456}
            },
            {
                'name': 'Southwest District',
                'address': '1130 Kentucky Ave, Indianapolis, IN 46221',
                'phone': '317-327-3811', 
                'coordinates': {'lat': 39.7401, 'lng': -86.2108}
            },
            {
                'name': 'Northwest District',
                'address': '5151 W 34th St, Indianapolis, IN 46224',
                'phone': '317-327-3811',
                'coordinates': {'lat': 39.8089, 'lng': -86.2344}
            },
            {
                'name': 'Downtown District',
                'address': '50 N Alabama St, Indianapolis, IN 46204',
                'phone': '317-327-3811',
                'coordinates': {'lat': 39.7684, 'lng': -86.1581}
            }
        ]
        return districts

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance using Haversine formula"""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2) 
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) * math.sin(delta_lng / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return round(distance, 2)