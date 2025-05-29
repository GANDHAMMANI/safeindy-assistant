"""
Weather Service for SafeIndy Assistant
Handles OpenWeatherMap API integration for weather alerts and conditions
"""

import requests
from flask import current_app
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class WeatherService:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
        self.indianapolis_coords = {'lat': 39.7684, 'lng': -86.1581}
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize OpenWeatherMap client with API key"""
        try:
            self.api_key = current_app.config.get('OPENWEATHER_API_KEY')
            if not self.api_key:
                print("⚠️ OPENWEATHER_API_KEY not found - weather features will use mock data")
            else:
                print("✅ Weather service initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize weather service: {e}")
    
    def get_current_weather(self, lat: float = None, lng: float = None) -> Dict:
        """
        Get current weather conditions
        
        Args:
            lat: Latitude (defaults to Indianapolis)
            lng: Longitude (defaults to Indianapolis)
            
        Returns:
            Dict with current weather information
        """
        if not self.api_key:
            return self._get_mock_weather()
        
        # Use Indianapolis coordinates if not provided
        if lat is None or lng is None:
            lat = self.indianapolis_coords['lat']
            lng = self.indianapolis_coords['lng']
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'units': 'imperial'  # Fahrenheit for US users
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'location': f"{data['name']}, IN",
                    'temperature': round(data['main']['temp']),
                    'feels_like': round(data['main']['feels_like']),
                    'description': data['weather'][0]['description'].title(),
                    'main': data['weather'][0]['main'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'wind_speed': data.get('wind', {}).get('speed', 0),
                    'wind_direction': data.get('wind', {}).get('deg', 0),
                    'visibility': data.get('visibility', 0) / 1000,  # Convert to km
                    'clouds': data.get('clouds', {}).get('all', 0),
                    'timestamp': datetime.now().isoformat(),
                    'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).strftime('%I:%M %p'),
                    'sunset': datetime.fromtimestamp(data['sys']['sunset']).strftime('%I:%M %p')
                }
            else:
                print(f"Weather API error: {response.status_code} - {data}")
                return self._get_mock_weather()
                
        except Exception as e:
            print(f"❌ Weather service error: {e}")
            return self._get_mock_weather()
    
    def get_weather_alerts(self, lat: float = None, lng: float = None) -> Dict:
        """
        Get weather alerts and warnings
        
        Args:
            lat: Latitude (defaults to Indianapolis)
            lng: Longitude (defaults to Indianapolis)
            
        Returns:
            Dict with weather alerts
        """
        if not self.api_key:
            return self._get_mock_alerts()
        
        # Use Indianapolis coordinates if not provided
        if lat is None or lng is None:
            lat = self.indianapolis_coords['lat']
            lng = self.indianapolis_coords['lng']
        
        try:
            url = f"{self.onecall_url}"
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'exclude': 'minutely,daily',  # We only need alerts and current
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                alerts = []
                
                if 'alerts' in data:
                    for alert in data['alerts']:
                        alerts.append({
                            'title': alert.get('event', 'Weather Alert'),
                            'description': alert.get('description', ''),
                            'severity': self._classify_severity(alert.get('event', '')),
                            'start_time': datetime.fromtimestamp(alert.get('start', 0)).strftime('%I:%M %p %m/%d'),
                            'end_time': datetime.fromtimestamp(alert.get('end', 0)).strftime('%I:%M %p %m/%d'),
                            'sender': alert.get('sender_name', 'National Weather Service'),
                            'tags': alert.get('tags', [])
                        })
                
                return {
                    'success': True,
                    'alerts': alerts,
                    'alert_count': len(alerts),
                    'location': 'Indianapolis, IN',
                    'timestamp': datetime.now().isoformat(),
                    'has_active_alerts': len(alerts) > 0
                }
            else:
                print(f"Alerts API error: {response.status_code}")
                return self._get_mock_alerts()
                
        except Exception as e:
            print(f"❌ Weather alerts error: {e}")
            return self._get_mock_alerts()
    
    def get_forecast(self, lat: float = None, lng: float = None, days: int = 3) -> Dict:
        """
        Get weather forecast
        
        Args:
            lat: Latitude (defaults to Indianapolis)
            lng: Longitude (defaults to Indianapolis)  
            days: Number of days to forecast
            
        Returns:
            Dict with weather forecast
        """
        if not self.api_key:
            return self._get_mock_forecast()
        
        # Use Indianapolis coordinates if not provided
        if lat is None or lng is None:
            lat = self.indianapolis_coords['lat']
            lng = self.indianapolis_coords['lng']
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'units': 'imperial',
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                forecasts = []
                
                for item in data['list'][:days * 2]:  # Limit results
                    forecasts.append({
                        'datetime': datetime.fromtimestamp(item['dt']).strftime('%a %m/%d %I:%M %p'),
                        'temperature': round(item['main']['temp']),
                        'feels_like': round(item['main']['feels_like']),
                        'description': item['weather'][0]['description'].title(),
                        'humidity': item['main']['humidity'],
                        'wind_speed': item.get('wind', {}).get('speed', 0),
                        'precipitation_chance': item.get('pop', 0) * 100
                    })
                
                return {
                    'success': True,
                    'forecasts': forecasts,
                    'location': f"{data['city']['name']}, IN",
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return self._get_mock_forecast()
                
        except Exception as e:
            print(f"❌ Forecast error: {e}")
            return self._get_mock_forecast()
    
    def get_severe_weather_guidance(self, weather_type: str) -> Dict:
        """
        Get safety guidance for severe weather
        
        Args:
            weather_type: Type of severe weather
            
        Returns:
            Dict with safety guidance
        """
        guidance = {
            'tornado': {
                'title': 'Tornado Safety',
                'immediate_actions': [
                    'Seek shelter in a sturdy building immediately',
                    'Go to the lowest floor and interior room',
                    'Stay away from windows',
                    'Get under a sturdy table or desk',
                    'Protect your head and neck with your arms'
                ],
                'avoid': [
                    'Mobile homes, even if tied down',
                    'Vehicles and overpasses',
                    'Wide-span buildings like gymnasiums'
                ],
                'emergency_contact': '911 if immediate danger'
            },
            'thunderstorm': {
                'title': 'Severe Thunderstorm Safety',
                'immediate_actions': [
                    'Stay indoors and away from windows',
                    'Avoid using electrical appliances',
                    'Stay off phones (landlines)',
                    'If outdoors, seek shelter immediately',
                    'Avoid tall objects and open areas'
                ],
                'avoid': [
                    'Swimming or water activities',
                    'Open fields and hilltops',
                    'Isolated trees or structures'
                ],
                'emergency_contact': '911 for emergencies'
            },
            'flood': {
                'title': 'Flood Safety',
                'immediate_actions': [
                    'Move to higher ground immediately',
                    'Avoid walking or driving through flood water',
                    'Turn off utilities if safe to do so',
                    'Listen to emergency broadcasts',
                    'Evacuate if ordered by authorities'
                ],
                'avoid': [
                    'Driving through flooded roads',
                    'Walking in moving water',
                    'Staying in flooded buildings'
                ],
                'emergency_contact': '911 for rescue assistance'
            },
            'winter_storm': {
                'title': 'Winter Storm Safety',
                'immediate_actions': [
                    'Stay indoors if possible',
                    'Dress in layers if you must go out',
                    'Keep emergency supplies available',
                    'Check on neighbors and elderly',
                    'Avoid overexertion when shoveling'
                ],
                'avoid': [
                    'Unnecessary travel',
                    'Carbon monoxide hazards from generators',
                    'Ice-covered surfaces'
                ],
                'emergency_contact': '317-327-4622 for city services'
            }
        }
        
        weather_type_clean = weather_type.lower().replace(' ', '_')
        
        if weather_type_clean in guidance:
            return {
                'success': True,
                'guidance': guidance[weather_type_clean],
                'indianapolis_resources': {
                    'emergency': '911',
                    'non_emergency': '317-327-3811',
                    'city_services': '317-327-4622',
                    'emergency_management': 'Monitor local news and alerts'
                }
            }
        else:
            return {
                'success': True,
                'guidance': {
                    'title': 'General Weather Safety',
                    'immediate_actions': [
                        'Monitor weather conditions closely',
                        'Follow guidance from local authorities',
                        'Have emergency supplies ready',
                        'Stay informed through reliable sources'
                    ],
                    'emergency_contact': '911 for emergencies'
                },
                'indianapolis_resources': {
                    'emergency': '911',
                    'non_emergency': '317-327-3811',
                    'city_services': '317-327-4622'
                }
            }
    
    def _classify_severity(self, event_name: str) -> str:
        """Classify weather alert severity"""
        event_lower = event_name.lower()
        
        if any(word in event_lower for word in ['tornado', 'hurricane', 'blizzard']):
            return 'extreme'
        elif any(word in event_lower for word in ['warning', 'severe', 'flash flood']):
            return 'high'
        elif any(word in event_lower for word in ['watch', 'advisory']):
            return 'moderate'
        else:
            return 'low'
    
    def _get_mock_weather(self) -> Dict:
        """Provide mock weather data when API is unavailable"""
        return {
            'success': True,
            'location': 'Indianapolis, IN',
            'temperature': 72,
            'feels_like': 75,
            'description': 'Partly Cloudy',
            'main': 'Clouds',
            'humidity': 45,
            'pressure': 1013,
            'wind_speed': 8,
            'wind_direction': 180,
            'visibility': 10,
            'clouds': 25,
            'timestamp': datetime.now().isoformat(),
            'sunrise': '7:15 AM',
            'sunset': '6:45 PM',
            'note': 'Mock data - API key not configured'
        }
    
    def _get_mock_alerts(self) -> Dict:
        """Provide mock alert data when API is unavailable"""
        return {
            'success': True,
            'alerts': [],
            'alert_count': 0,
            'location': 'Indianapolis, IN',
            'timestamp': datetime.now().isoformat(),
            'has_active_alerts': False,
            'note': 'Mock data - no active alerts simulated'
        }
    
    def _get_mock_forecast(self) -> Dict:
        """Provide mock forecast data when API is unavailable"""
        forecasts = []
        base_time = datetime.now()
        
        for i in range(6):
            forecast_time = base_time + timedelta(hours=i * 4)
            forecasts.append({
                'datetime': forecast_time.strftime('%a %m/%d %I:%M %p'),
                'temperature': 72 + (i % 3) - 1,
                'feels_like': 75 + (i % 3) - 1,
                'description': ['Partly Cloudy', 'Mostly Sunny', 'Cloudy'][i % 3],
                'humidity': 45 + (i % 2) * 10,
                'wind_speed': 8 + (i % 2) * 2,
                'precipitation_chance': (i % 4) * 15
            })
        
        return {
            'success': True,
            'forecasts': forecasts,
            'location': 'Indianapolis, IN',
            'timestamp': datetime.now().isoformat(),
            'note': 'Mock data - API key not configured'
        }