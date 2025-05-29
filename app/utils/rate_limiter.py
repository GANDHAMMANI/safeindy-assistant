"""
Rate Limiter for SafeIndy Assistant
Prevents abuse and manages API usage limits
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from flask import request, session
import hashlib

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)  # Track requests per identifier
        self.blocked_ips = {}  # Temporarily blocked IPs
        self.request_counts = defaultdict(int)  # Total request counts
        
        # Rate limiting rules
        self.rules = {
            'chat_messages': {
                'limit': 30,  # 30 messages
                'window': 300,  # per 5 minutes
                'block_duration': 600  # 10 minute block
            },
            'api_calls': {
                'limit': 100,  # 100 API calls
                'window': 3600,  # per hour
                'block_duration': 1800  # 30 minute block
            },
            'emergency_alerts': {
                'limit': 5,  # 5 emergency alerts
                'window': 1800,  # per 30 minutes
                'block_duration': 3600  # 1 hour block
            },
            'location_requests': {
                'limit': 20,  # 20 location requests
                'window': 600,  # per 10 minutes
                'block_duration': 1200  # 20 minute block
            }
        }
        
        print("✅ Rate limiter initialized")
    
    def get_client_identifier(self) -> str:
        """Get unique identifier for client (IP + session)"""
        try:
            # Combine IP and session for more accurate limiting
            ip_address = request.remote_addr or 'unknown'
            session_id = session.get('session_id', 'no_session')
            
            # Create hash for privacy
            identifier = f"{ip_address}_{session_id}"
            return hashlib.md5(identifier.encode()).hexdigest()[:16]
            
        except Exception as e:
            print(f"❌ Client identifier error: {e}")
            return 'unknown'
    
    def is_allowed(self, rule_name: str, identifier: str = None) -> Tuple[bool, Dict]:
        """
        Check if request is allowed under rate limit
        
        Args:
            rule_name: Name of the rate limiting rule
            identifier: Client identifier (auto-generated if None)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            if identifier is None:
                identifier = self.get_client_identifier()
            
            # Check if IP is currently blocked
            if self._is_blocked(identifier):
                return False, self._get_block_info(identifier)
            
            # Get rate limiting rule
            if rule_name not in self.rules:
                return True, {'error': f'Unknown rule: {rule_name}'}
            
            rule = self.rules[rule_name]
            current_time = time.time()
            window_start = current_time - rule['window']
            
            # Get request history for this identifier and rule
            key = f"{identifier}_{rule_name}"
            request_times = self.requests[key]
            
            # Remove old requests outside the window
            while request_times and request_times[0] < window_start:
                request_times.popleft()
            
            # Check if limit exceeded
            if len(request_times) >= rule['limit']:
                self._block_client(identifier, rule_name, rule['block_duration'])
                
                return False, {
                    'rate_limited': True,
                    'rule': rule_name,
                    'limit': rule['limit'],
                    'window_seconds': rule['window'],
                    'retry_after': rule['block_duration'],
                    'requests_made': len(request_times),
                    'window_reset': window_start + rule['window']
                }
            
            # Request is allowed
            request_times.append(current_time)
            self.request_counts[key] += 1
            
            return True, {
                'rate_limited': False,
                'rule': rule_name,
                'limit': rule['limit'],
                'window_seconds': rule['window'],
                'requests_made': len(request_times),
                'requests_remaining': rule['limit'] - len(request_times),
                'window_reset': window_start + rule['window']
            }
            
        except Exception as e:
            print(f"❌ Rate limit check error: {e}")
            # Allow request if rate limiter fails
            return True, {'error': str(e)}
    
    def record_request(self, rule_name: str, identifier: str = None):
        """Record a request for rate limiting purposes"""
        try:
            if identifier is None:
                identifier = self.get_client_identifier()
            
            # This is called by is_allowed, but can be used independently
            key = f"{identifier}_{rule_name}"
            self.requests[key].append(time.time())
            self.request_counts[key] += 1
            
        except Exception as e:
            print(f"❌ Request recording error: {e}")
    
    def _is_blocked(self, identifier: str) -> bool:
        """Check if identifier is currently blocked"""
        if identifier not in self.blocked_ips:
            return False
        
        block_info = self.blocked_ips[identifier]
        if time.time() > block_info['expires_at']:
            del self.blocked_ips[identifier]
            return False
        
        return True
    
    def _block_client(self, identifier: str, rule_name: str, duration: int):
        """Block a client for specified duration"""
        try:
            self.blocked_ips[identifier] = {
                'blocked_at': time.time(),
                'expires_at': time.time() + duration,
                'rule': rule_name,
                'duration': duration
            }
            
            print(f"🚫 Blocked client {identifier[:8]} for {duration}s (rule: {rule_name})")
            
        except Exception as e:
            print(f"❌ Client blocking error: {e}")
    
    def _get_block_info(self, identifier: str) -> Dict:
        """Get information about why client is blocked"""
        if identifier not in self.blocked_ips:
            return {}
        
        block_info = self.blocked_ips[identifier]
        remaining_time = max(0, block_info['expires_at'] - time.time())
        
        return {
            'blocked': True,
            'rule': block_info['rule'],
            'blocked_at': datetime.fromtimestamp(block_info['blocked_at']).isoformat(),
            'expires_at': datetime.fromtimestamp(block_info['expires_at']).isoformat(),
            'retry_after': int(remaining_time),
            'message': f"Too many requests. Try again in {int(remaining_time)} seconds."
        }
    
    def unblock_client(self, identifier: str) -> bool:
        """Manually unblock a client"""
        try:
            if identifier in self.blocked_ips:
                del self.blocked_ips[identifier]
                print(f"✅ Unblocked client {identifier[:8]}")
                return True
            return False
        except Exception as e:
            print(f"❌ Unblock error: {e}")
            return False
    
    def get_client_stats(self, identifier: str = None) -> Dict:
        """Get rate limiting statistics for a client"""
        if identifier is None:
            identifier = self.get_client_identifier()
        
        try:
            stats = {
                'identifier': identifier[:8],  # Partial for privacy
                'is_blocked': self._is_blocked(identifier),
                'rules': {}
            }
            
            # Add block info if blocked
            if stats['is_blocked']:
                stats['block_info'] = self._get_block_info(identifier)
            
            # Get stats for each rule
            for rule_name, rule in self.rules.items():
                key = f"{identifier}_{rule_name}"
                request_times = self.requests[key]
                
                # Count requests in current window
                current_time = time.time()
                window_start = current_time - rule['window']
                recent_requests = [t for t in request_times if t > window_start]
                
                stats['rules'][rule_name] = {
                    'limit': rule['limit'],
                    'window_seconds': rule['window'],
                    'requests_in_window': len(recent_requests),
                    'requests_remaining': max(0, rule['limit'] - len(recent_requests)),
                    'total_requests': self.request_counts[key],
                    'next_reset': window_start + rule['window']
                }
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_global_stats(self) -> Dict:
        """Get global rate limiting statistics"""
        try:
            current_time = time.time()
            
            # Count active blocks
            active_blocks = sum(1 for block_info in self.blocked_ips.values() 
                              if block_info['expires_at'] > current_time)
            
            # Count total requests per rule
            rule_totals = defaultdict(int)
            for key, count in self.request_counts.items():
                if '_' in key:
                    rule_name = key.split('_', 1)[1]
                    rule_totals[rule_name] += count
            
            return {
                'active_blocks': active_blocks,
                'total_blocked_clients': len(self.blocked_ips),
                'total_requests_by_rule': dict(rule_totals),
                'rules_configured': list(self.rules.keys()),
                'rate_limiter_uptime': 'Active'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_old_data(self):
        """Clean up old request data to prevent memory bloat"""
        try:
            current_time = time.time()
            cleanup_count = 0
            
            # Clean up old requests (keep only last 24 hours)
            cutoff_time = current_time - 86400  # 24 hours
            
            for key in list(self.requests.keys()):
                request_times = self.requests[key]
                original_length = len(request_times)
                
                # Remove old requests
                while request_times and request_times[0] < cutoff_time:
                    request_times.popleft()
                
                # Remove empty deques
                if not request_times:
                    del self.requests[key]
                    if key in self.request_counts:
                        del self.request_counts[key]
                
                cleanup_count += original_length - len(request_times)
            
            # Clean up expired blocks
            expired_blocks = []
            for identifier, block_info in self.blocked_ips.items():
                if current_time > block_info['expires_at']:
                    expired_blocks.append(identifier)
            
            for identifier in expired_blocks:
                del self.blocked_ips[identifier]
            
            if cleanup_count > 0 or expired_blocks:
                print(f"🧹 Rate limiter cleanup: {cleanup_count} old requests, {len(expired_blocks)} expired blocks")
            
        except Exception as e:
            print(f"❌ Rate limiter cleanup error: {e}")

# Decorators for easy integration

def rate_limit(rule_name: str):
    """Decorator to apply rate limiting to routes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            allowed, rate_info = limiter.is_allowed(rule_name)
            
            if not allowed:
                from flask import jsonify
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'rate_limit_info': rate_info
                }), 429
            
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter():
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter