"""
Enhanced Search Service for SafeIndy Assistant
Specialized searches for current Indianapolis emergency and safety information
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

class SearchService:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "llama-3.1-sonar-small-128k-online"  # Sonar model for web search
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization - only initialize when needed"""
        if self._initialized:
            return
            
        try:
            from flask import current_app
            self.api_key = current_app.config.get('PERPLEXITY_API_KEY')
            if not self.api_key:
                raise ValueError("PERPLEXITY_API_KEY not found in configuration")
            self._initialized = True
            print("✅ Perplexity Sonar client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Perplexity client: {e}")
            self.api_key = None

    def search_emergency_info(self, emergency_type: str) -> Dict:
        """Search for specific current emergency information"""
        self._ensure_initialized()
        
        emergency_queries = {
            'police': 'Indianapolis IMPD police stations addresses phone numbers districts current contact information 2024',
            'fire': 'Indianapolis Fire Department IFD stations contact information emergency services current 2024',
            'medical': 'Indianapolis hospitals emergency rooms addresses phone numbers current information 2024',
            'poison': 'poison control emergency hotline Indianapolis Indiana current contact information',
            'weather': 'Indianapolis weather alerts emergency notifications severe weather current warnings',
            'general': 'Indianapolis emergency services police fire medical contact numbers current 2024'
        }
        
        query = emergency_queries.get(emergency_type, emergency_queries['general'])
        return self._search_with_focus(query, 'emergency_services')
    
    def search_community_resources(self, resource_type: str) -> Dict:
        """Search for current community resources and services"""
        self._ensure_initialized()
        
        resource_queries = {
            'hospitals': 'Indianapolis hospitals medical centers emergency rooms locations addresses phone numbers current 2024',
            'shelters': 'Indianapolis emergency shelters homeless services current locations contact information',
            'mental_health': 'Indianapolis mental health crisis services hotlines resources current contact information',
            'food': 'Indianapolis food assistance emergency food banks current locations phone numbers',
            'utilities': 'Indianapolis utilities emergency contacts Citizens Energy IPL current phone numbers',
            'general': 'Indianapolis community resources emergency services social services current contact information'
        }
        
        query = resource_queries.get(resource_type, resource_queries['general'])
        return self._search_with_focus(query, 'community_resources')
    
    def search_city_services(self, service_type: str) -> Dict:
        """Search for Indianapolis city services information"""
        self._ensure_initialized()
        
        service_queries = {
            'pothole': 'Indianapolis pothole reporting Mayor Action Center RequestIndy app current process phone number',
            'trash': 'Indianapolis trash collection schedule missed pickup reporting current contact information',
            'street_lights': 'Indianapolis street light repair reporting city services current phone numbers',
            'abandoned_vehicle': 'Indianapolis abandoned vehicle reporting removal process current contact',
            'zoning': 'Indianapolis zoning violations reporting code enforcement current contact information',
            '311': 'Indianapolis 311 services Mayor Action Center contact information hours current phone numbers',
            'general': 'Indianapolis city services Mayor Action Center RequestIndy 311 current contact information 2024'
        }
        
        query = service_queries.get(service_type, service_queries['general'])
        return self._search_with_focus(query, 'city_services')
    
    def search_weather_alerts(self) -> Dict:
        """Search for current Indianapolis weather alerts"""
        self._ensure_initialized()
        query = 'Indianapolis Indiana weather alerts warnings current conditions emergency notifications today'
        return self._search_with_focus(query, 'weather')
    
    def _search_with_focus(self, query: str, focus_area: str) -> Dict:
        """
        Enhanced search with focus on getting current, accurate information
        """
        if not self.api_key:
            return {
                'results': f'Real-time search unavailable. Please visit indy.gov for current {focus_area} information.',
                'sources': [],
                'error': 'API key not configured'
            }
        
        try:
            # Build focused search query
            search_query = self._build_focused_query(query, focus_area)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": f"""You are searching for current, accurate Indianapolis {focus_area} information. 
                        Focus on providing:
                        - Current contact information (phone numbers, addresses)
                        - Official government sources and websites
                        - Emergency contact numbers that are verified and up-to-date
                        - Clear, actionable information for Indianapolis residents
                        
                        Always prioritize official sources like indy.gov, city departments, and verified emergency services.
                        Include phone numbers, addresses, and websites when available.
                        Format the response clearly with proper contact information."""
                    },
                    {
                        "role": "user",
                        "content": search_query
                    }
                ],
                "temperature": 0.1,  # Lower temperature for factual accuracy
                "max_tokens": 1024,
                "top_p": 0.9,
                "return_citations": True,
                "search_domain_filter": self._get_trusted_domains(focus_area),
                "search_recency_filter": "month"  # Prefer recent information
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response and citations
                content = data['choices'][0]['message']['content']
                
                # Safe citation handling
                sources = []
                raw_citations = data.get('citations', [])
                
                if isinstance(raw_citations, list):
                    for i, citation in enumerate(raw_citations):
                        if isinstance(citation, dict):
                            source = {
                                'title': citation.get('title', f'Indianapolis {focus_area.title()} Source {i+1}'),
                                'url': citation.get('url', 'https://www.indy.gov'),
                                'type': 'live_search',
                                'domain': self._extract_domain(citation.get('url', '')),
                                'focus_area': focus_area
                            }
                            sources.append(source)
                
                # Ensure we have at least one official source
                if not sources or not any('indy.gov' in s.get('url', '') for s in sources):
                    sources.append({
                        'title': 'City of Indianapolis Official Website',
                        'url': 'https://www.indy.gov',
                        'type': 'official',
                        'focus_area': focus_area
                    })
                
                return {
                    'results': content,
                    'sources': sources[:3],  # Limit to top 3 sources
                    'timestamp': datetime.now().isoformat(),
                    'query': search_query,
                    'focus_area': focus_area,
                    'model': self.model
                }
            else:
                print(f"❌ Perplexity API error: {response.status_code} - {response.text}")
                return self._get_fallback_search_result(focus_area)
                
        except Exception as e:
            print(f"❌ Search service error: {e}")
            return self._get_fallback_search_result(focus_area)

    def _build_focused_query(self, user_query: str, focus_area: str) -> str:
        """Build optimized search query for specific focus areas"""
        
        # Focus area specific enhancements
        focus_enhancements = {
            'emergency_services': 'current contact information phone numbers addresses official',
            'community_resources': 'current locations contact information phone numbers addresses',
            'city_services': 'current process phone numbers contact information official',
            'weather': 'current alerts warnings today Indianapolis Indiana'
        }
        
        enhancement = focus_enhancements.get(focus_area, 'current information Indianapolis')
        
        # Build enhanced query
        enhanced_query = f"{user_query} {enhancement}"
        
        # Add current year for relevance
        current_year = datetime.now().year
        enhanced_query += f" {current_year}"
        
        return enhanced_query
    
    def _get_trusted_domains(self, focus_area: str) -> List[str]:
        """Get trusted domains for different focus areas"""
        
        base_domains = [
            "indy.gov",
            "indianapolis.gov", 
            "in.gov",
            "ready.gov"
        ]
        
        focus_domains = {
            'emergency_services': base_domains + [
                "redcross.org",
                "weather.gov",
                "cdc.gov"
            ],
            'community_resources': base_domains + [
                "iuhealth.org",
                "eskenazi.edu", 
                "communityhealth.net",
                "stvincent.org"
            ],
            'city_services': base_domains,
            'weather': [
                "weather.gov",
                "ready.gov",
                "indy.gov"
            ]
        }
        
        return focus_domains.get(focus_area, base_domains)
    
    def _get_fallback_search_result(self, focus_area: str) -> Dict:
        """Provide fallback information when search fails"""
        
        fallback_messages = {
            'emergency_services': 'Search temporarily unavailable. For current emergency contact information, visit indy.gov or call 911 for emergencies, 317-327-3811 for police non-emergency.',
            'community_resources': 'Search temporarily unavailable. For current Indianapolis community resources, visit indy.gov or call 2-1-1 for community assistance.',
            'city_services': 'Search temporarily unavailable. For current city services, visit indy.gov, use the RequestIndy app, or call 311 at 317-327-4622.',
            'weather': 'Search temporarily unavailable. For current weather alerts, visit weather.gov or local Indianapolis news sources.'
        }
        
        return {
            'results': fallback_messages.get(focus_area, 'Search temporarily unavailable. Visit indy.gov for current Indianapolis information.'),
            'sources': [
                {
                    'title': 'City of Indianapolis',
                    'url': 'https://www.indy.gov',
                    'type': 'fallback'
                }
            ],
            'error': 'Search service unavailable',
            'focus_area': focus_area
        }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL safely"""
        try:
            if not url or not isinstance(url, str):
                return 'unknown'
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or 'unknown'
        except:
            return 'unknown'
    
    def is_search_needed(self, user_message: str, intent: str) -> bool:
        """
        Determine if real-time search is needed for the query
        """
        
        # Always search for these intents to get current information
        search_required_intents = ['emergency', 'weather', 'city_services', 'medical', 'police', 'location']
        
        if intent in search_required_intents:
            return True
        
        # Search for queries with time-sensitive keywords
        time_sensitive_keywords = [
            'current', 'now', 'today', 'latest', 'recent', 'hours', 'open', 'closed',
            'schedule', 'status', 'alert', 'update', 'available', 'contact', 'phone', 'address'
        ]
        
        message_lower = user_message.lower()
        if any(keyword in message_lower for keyword in time_sensitive_keywords):
            return True
        
        # Search for location-specific queries that need current info
        location_keywords = ['where', 'nearest', 'close to', 'near me', 'address', 'location', 'find']
        if any(keyword in message_lower for keyword in location_keywords):
            return True
        
        return False

    def search_indianapolis_data(self, query: str, intent: str = None) -> Dict:
        """
        General Indianapolis data search with intent awareness
        """
        self._ensure_initialized()
        
        # Route to specialized searches based on intent
        if intent == 'emergency':
            return self.search_emergency_info('general')
        elif intent == 'medical':
            return self.search_community_resources('hospitals')
        elif intent == 'police':
            return self.search_emergency_info('police')
        elif intent == 'city_services':
            return self.search_city_services('general')
        elif intent == 'weather':
            return self.search_weather_alerts()
        else:
            # General search for Indianapolis information
            enhanced_query = f"Indianapolis Indiana {query} current information contact details 2024"
            return self._search_with_focus(enhanced_query, 'general')