"""
Analytics Service for SafeIndy Assistant
Tracks usage patterns, performance metrics, and user interactions
"""

from flask import current_app, session, request
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter
import time

class AnalyticsService:
    def __init__(self):
        self.enabled = current_app.config.get('ANALYTICS_ENABLED', True)
        self.session_data = {}
        self.metrics = {
            'total_messages': 0,
            'emergency_alerts': 0,
            'user_sessions': 0,
            'api_calls': defaultdict(int),
            'response_times': [],
            'intent_distribution': Counter(),
            'error_count': 0,
            'location_requests': 0
        }
        print("✅ Analytics service initialized")
    
    def track_message(self, user_message: str, ai_response: Dict, processing_time: float, session_id: str):
        """Track individual message interactions"""
        if not self.enabled:
            return
        
        try:
            self.metrics['total_messages'] += 1
            self.metrics['response_times'].append(processing_time)
            
            # Track intent distribution
            intent = ai_response.get('intent', 'unknown')
            self.metrics['intent_distribution'][intent] += 1
            
            # Track emergency events
            if ai_response.get('emergency', False):
                self.metrics['emergency_alerts'] += 1
                self._log_emergency_event(f"Emergency detected in session {session_id}: {user_message[:50]}")
            
            # Track session data
            if session_id not in self.session_data:
                self.metrics['user_sessions'] += 1
                self.session_data[session_id] = {
                    'start_time': datetime.now().isoformat(),
                    'message_count': 0,
                    'intents': [],
                    'location_shared': False,
                    'emergency_triggered': False
                }
            
            session_info = self.session_data[session_id]
            session_info['message_count'] += 1
            session_info['intents'].append(intent)
            session_info['last_activity'] = datetime.now().isoformat()
            
            if ai_response.get('emergency', False):
                session_info['emergency_triggered'] = True
            
            # Log detailed interaction
            self._log_interaction({
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'user_message': user_message[:100],  # Truncate for privacy
                'intent': intent,
                'confidence': ai_response.get('confidence', 0),
                'processing_time': processing_time,
                'sources_used': len(ai_response.get('sources', [])),
                'emergency': ai_response.get('emergency', False),
                'has_location': 'location' in ai_response
            })
            
        except Exception as e:
            print(f"❌ Analytics tracking error: {e}")
    
    def track_api_call(self, service_name: str, success: bool, response_time: float):
        """Track external API calls"""
        if not self.enabled:
            return
        
        try:
            self.metrics['api_calls'][service_name] += 1
            
            if not success:
                self.metrics['error_count'] += 1
                self.metrics['api_calls'][f"{service_name}_errors"] += 1
            
            # Track API performance
            api_key = f"{service_name}_response_times"
            if api_key not in self.metrics:
                self.metrics[api_key] = []
            self.metrics[api_key].append(response_time)
            
        except Exception as e:
            print(f"❌ API tracking error: {e}")
    
    def track_location_request(self, session_id: str, location_data: Dict, source: str):
        """Track location sharing events"""
        if not self.enabled:
            return
        
        try:
            self.metrics['location_requests'] += 1
            
            if session_id in self.session_data:
                self.session_data[session_id]['location_shared'] = True
                self.session_data[session_id]['location_source'] = source
            
            self._log_location_event({
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'source': source,  # 'gps', 'manual', 'extracted'
                'accuracy': location_data.get('accuracy'),
                'has_address': 'address' in location_data
            })
            
        except Exception as e:
            print(f"❌ Location tracking error: {e}")
    
    def track_emergency_alert(self, session_id: str, alert_sent: bool, location_included: bool):
        """Track emergency alert events"""
        if not self.enabled:
            return
        
        try:
            self._log_emergency_event({
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'alert_sent': alert_sent,
                'location_included': location_included,
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.remote_addr
            })
            
        except Exception as e:
            print(f"❌ Emergency tracking error: {e}")
    
    def get_analytics_summary(self) -> Dict:
        """Get comprehensive analytics summary"""
        try:
            now = datetime.now()
            
            # Calculate averages
            avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times']) if self.metrics['response_times'] else 0
            
            # Session analytics
            active_sessions = len([s for s in self.session_data.values() 
                                 if datetime.fromisoformat(s.get('last_activity', s.get('start_time'))) > now - timedelta(hours=1)])
            
            # Top intents
            top_intents = dict(self.metrics['intent_distribution'].most_common(10))
            
            # API performance
            api_performance = {}
            for service, count in self.metrics['api_calls'].items():
                if not service.endswith('_errors'):
                    error_count = self.metrics['api_calls'].get(f"{service}_errors", 0)
                    success_rate = ((count - error_count) / count * 100) if count > 0 else 0
                    api_performance[service] = {
                        'total_calls': count,
                        'errors': error_count,
                        'success_rate': round(success_rate, 2)
                    }
            
            return {
                'overview': {
                    'total_messages': self.metrics['total_messages'],
                    'total_sessions': self.metrics['user_sessions'],
                    'active_sessions': active_sessions,
                    'emergency_alerts': self.metrics['emergency_alerts'],
                    'location_requests': self.metrics['location_requests'],
                    'average_response_time': round(avg_response_time, 3),
                    'error_rate': round((self.metrics['error_count'] / max(self.metrics['total_messages'], 1)) * 100, 2)
                },
                'user_behavior': {
                    'top_intents': top_intents,
                    'messages_per_session': round(self.metrics['total_messages'] / max(self.metrics['user_sessions'], 1), 2),
                    'emergency_rate': round((self.metrics['emergency_alerts'] / max(self.metrics['total_messages'], 1)) * 100, 2),
                    'location_sharing_rate': round((self.metrics['location_requests'] / max(self.metrics['user_sessions'], 1)) * 100, 2)
                },
                'api_performance': api_performance,
                'system_health': {
                    'uptime': 'Available in production',
                    'total_errors': self.metrics['error_count'],
                    'last_updated': now.isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Analytics summary error: {e}")
            return {'error': str(e)}
    
    def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for specific session"""
        if session_id not in self.session_data:
            return {'error': 'Session not found'}
        
        session_info = self.session_data[session_id]
        
        # Calculate session duration
        start_time = datetime.fromisoformat(session_info['start_time'])
        last_activity = datetime.fromisoformat(session_info.get('last_activity', session_info['start_time']))
        duration = (last_activity - start_time).total_seconds()
        
        return {
            'session_id': session_id,
            'start_time': session_info['start_time'],
            'last_activity': session_info.get('last_activity'),
            'duration_seconds': duration,
            'message_count': session_info['message_count'],
            'intents_used': list(set(session_info['intents'])),
            'location_shared': session_info.get('location_shared', False),
            'emergency_triggered': session_info.get('emergency_triggered', False),
            'intent_distribution': dict(Counter(session_info['intents']))
        }
    
    def get_emergency_statistics(self) -> Dict:
        """Get emergency-specific analytics"""
        try:
            emergency_sessions = [s for s in self.session_data.values() if s.get('emergency_triggered', False)]
            
            return {
                'total_emergency_events': self.metrics['emergency_alerts'],
                'emergency_sessions': len(emergency_sessions),
                'emergency_rate': round((len(emergency_sessions) / max(self.metrics['user_sessions'], 1)) * 100, 2),
                'location_provided_rate': round((sum(1 for s in emergency_sessions if s.get('location_shared', False)) / max(len(emergency_sessions), 1)) * 100, 2),
                'response_protocol': {
                    'immediate_911_guidance': True,
                    'location_tracking': True,
                    'email_alerts': True,
                    'contact_prioritization': True
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _log_interaction(self, interaction_data: Dict):
        """Log detailed interaction (in production, this would go to a database)"""
        # In development, just print for monitoring
        if current_app.config.get('FLASK_ENV') == 'development':
            print(f"📊 Interaction: {interaction_data['intent']} | Time: {interaction_data['processing_time']:.2f}s")
    
    def _log_emergency_event(self, event_data):
        """Log emergency events (critical for monitoring)"""
        timestamp = datetime.now().isoformat()
        
        # Handle both string and dict inputs
        if isinstance(event_data, str):
            print(f"🚨 EMERGENCY EVENT: {timestamp} - {event_data}")
        else:
            print(f"🚨 EMERGENCY EVENT: {timestamp} - {event_data}")
        
        # In production, this would be logged to a secure system
        # and potentially trigger additional monitoring alerts
    
    def _log_location_event(self, location_data: Dict):
        """Log location sharing events"""
        print(f"📍 Location Event: {location_data['source']} - Session: {location_data['session_id'][:8]}")
    
    def clear_old_sessions(self, hours_old: int = 24):
        """Clean up old session data to prevent memory bloat"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            
            old_sessions = []
            for session_id, session_info in self.session_data.items():
                last_activity = datetime.fromisoformat(session_info.get('last_activity', session_info.get('start_time')))
                if last_activity < cutoff_time:
                    old_sessions.append(session_id)
            
            for session_id in old_sessions:
                del self.session_data[session_id]
            
            if old_sessions:
                print(f"🧹 Cleaned up {len(old_sessions)} old sessions")
            
        except Exception as e:
            print(f"❌ Session cleanup error: {e}")
    
    def export_analytics(self) -> Dict:
        """Export analytics data for reporting"""
        return {
            'summary': self.get_analytics_summary(),
            'emergency_stats': self.get_emergency_statistics(),
            'export_time': datetime.now().isoformat(),
            'data_retention': '24 hours for sessions, permanent for aggregated metrics'
        }