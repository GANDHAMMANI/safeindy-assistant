"""
Cache Manager for SafeIndy Assistant
Implements intelligent caching for API responses and AI generations
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from flask import current_app
import pickle

class CacheManager:
    def __init__(self):
        self.cache = {}  # In-memory cache
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        self.max_cache_size = 1000  # Maximum number of cached items
        self.default_ttl = 300  # 5 minutes default TTL
        print("✅ Cache manager initialized")
    
    def get_cache_key(self, data: Any, prefix: str = '') -> str:
        """Generate cache key from data"""
        try:
            # Convert data to string and create hash
            if isinstance(data, dict):
                # Sort dict for consistent hashing
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            hash_obj = hashlib.md5(data_str.encode())
            cache_key = f"{prefix}_{hash_obj.hexdigest()}" if prefix else hash_obj.hexdigest()
            
            return cache_key
            
        except Exception as e:
            print(f"❌ Cache key generation error: {e}")
            return f"{prefix}_{int(time.time())}"
    
    def get(self, key: str) -> Optional[Dict]:
        """Retrieve item from cache"""
        try:
            self.cache_stats['total_requests'] += 1
            
            if key not in self.cache:
                self.cache_stats['misses'] += 1
                return None
            
            cache_item = self.cache[key]
            
            # Check if expired
            if cache_item['expires_at'] < time.time():
                del self.cache[key]
                self.cache_stats['misses'] += 1
                return None
            
            # Update access time for LRU
            cache_item['last_accessed'] = time.time()
            self.cache_stats['hits'] += 1
            
            return cache_item['data']
            
        except Exception as e:
            print(f"❌ Cache get error: {e}")
            self.cache_stats['misses'] += 1
            return None
    
    def set(self, key: str, data: Any, ttl: int = None) -> bool:
        """Store item in cache"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            # Check cache size and evict if necessary
            if len(self.cache) >= self.max_cache_size:
                self._evict_lru()
            
            cache_item = {
                'data': data,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'expires_at': time.time() + ttl,
                'ttl': ttl
            }
            
            self.cache[key] = cache_item
            return True
            
        except Exception as e:
            print(f"❌ Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        try:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
        except Exception as e:
            print(f"❌ Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache"""
        try:
            self.cache.clear()
            self.cache_stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'total_requests': 0
            }
            print("✅ Cache cleared")
            return True
        except Exception as e:
            print(f"❌ Cache clear error: {e}")
            return False
    
    def _evict_lru(self):
        """Evict least recently used item"""
        try:
            if not self.cache:
                return
            
            # Find LRU item
            lru_key = min(self.cache.keys(), 
                         key=lambda k: self.cache[k]['last_accessed'])
            
            del self.cache[lru_key]
            self.cache_stats['evictions'] += 1
            
        except Exception as e:
            print(f"❌ Cache eviction error: {e}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        hit_rate = 0
        if self.cache_stats['total_requests'] > 0:
            hit_rate = (self.cache_stats['hits'] / self.cache_stats['total_requests']) * 100
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_cache_size,
            'hit_rate': round(hit_rate, 2),
            'total_requests': self.cache_stats['total_requests'],
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'memory_usage': self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> str:
        """Estimate cache memory usage"""
        try:
            total_size = 0
            for item in self.cache.values():
                # Rough estimate using pickle
                total_size += len(pickle.dumps(item))
            
            if total_size < 1024:
                return f"{total_size} bytes"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            else:
                return f"{total_size / (1024 * 1024):.1f} MB"
                
        except Exception as e:
            return "Unknown"
    
    def cleanup_expired(self):
        """Remove expired items from cache"""
        try:
            current_time = time.time()
            expired_keys = []
            
            for key, item in self.cache.items():
                if item['expires_at'] < current_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                print(f"🧹 Cleaned up {len(expired_keys)} expired cache items")
            
        except Exception as e:
            print(f"❌ Cache cleanup error: {e}")

# Specialized cache classes for different types of data

class AIResponseCache(CacheManager):
    """Specialized cache for AI responses"""
    
    def __init__(self):
        super().__init__()
        self.default_ttl = 600  # 10 minutes for AI responses
    
    def cache_ai_response(self, user_message: str, intent: str, response_data: Dict) -> str:
        """Cache AI response with intelligent key generation"""
        try:
            # Don't cache emergency responses
            if response_data.get('emergency', False):
                return None
            
            # Create cache key from message and intent
            cache_data = {
                'message_normalized': user_message.lower().strip(),
                'intent': intent
            }
            
            cache_key = self.get_cache_key(cache_data, 'ai_response')
            
            # Add metadata to cached response
            cached_data = response_data.copy()
            cached_data['cached_at'] = datetime.now().isoformat()
            cached_data['cache_key'] = cache_key
            
            self.set(cache_key, cached_data, ttl=self.default_ttl)
            return cache_key
            
        except Exception as e:
            print(f"❌ AI response caching error: {e}")
            return None
    
    def get_ai_response(self, user_message: str, intent: str) -> Optional[Dict]:
        """Retrieve cached AI response"""
        try:
            cache_data = {
                'message_normalized': user_message.lower().strip(),
                'intent': intent
            }
            
            cache_key = self.get_cache_key(cache_data, 'ai_response')
            cached_response = self.get(cache_key)
            
            if cached_response:
                # Add cache hit indicator
                cached_response['from_cache'] = True
                print(f"✅ Cache hit for AI response: {intent}")
            
            return cached_response
            
        except Exception as e:
            print(f"❌ AI response retrieval error: {e}")
            return None

class LocationCache(CacheManager):
    """Specialized cache for location data"""
    
    def __init__(self):
        super().__init__()
        self.default_ttl = 3600  # 1 hour for location data
    
    def cache_location_data(self, address: str, location_data: Dict) -> str:
        """Cache geocoded location data"""
        try:
            cache_key = self.get_cache_key(address.lower().strip(), 'location')
            
            cached_data = location_data.copy()
            cached_data['cached_at'] = datetime.now().isoformat()
            
            self.set(cache_key, cached_data, ttl=self.default_ttl)
            return cache_key
            
        except Exception as e:
            print(f"❌ Location caching error: {e}")
            return None
    
    def get_location_data(self, address: str) -> Optional[Dict]:
        """Retrieve cached location data"""
        try:
            cache_key = self.get_cache_key(address.lower().strip(), 'location')
            return self.get(cache_key)
        except Exception as e:
            print(f"❌ Location retrieval error: {e}")
            return None

class WeatherCache(CacheManager):
    """Specialized cache for weather data"""
    
    def __init__(self):
        super().__init__()
        self.default_ttl = 900  # 15 minutes for weather data
    
    def cache_weather_data(self, lat: float, lng: float, weather_data: Dict) -> str:
        """Cache weather data for coordinates"""
        try:
            # Round coordinates to reduce cache fragmentation
            lat_rounded = round(lat, 3)
            lng_rounded = round(lng, 3)
            
            cache_key = self.get_cache_key(f"{lat_rounded},{lng_rounded}", 'weather')
            
            cached_data = weather_data.copy()
            cached_data['cached_at'] = datetime.now().isoformat()
            
            self.set(cache_key, cached_data, ttl=self.default_ttl)
            return cache_key
            
        except Exception as e:
            print(f"❌ Weather caching error: {e}")
            return None
    
    def get_weather_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Retrieve cached weather data"""
        try:
            lat_rounded = round(lat, 3)
            lng_rounded = round(lng, 3)
            cache_key = self.get_cache_key(f"{lat_rounded},{lng_rounded}", 'weather')
            return self.get(cache_key)
        except Exception as e:
            print(f"❌ Weather retrieval error: {e}")
            return None

# Global cache instances
ai_cache = None
location_cache = None  
weather_cache = None

def get_ai_cache():
    """Get global AI response cache instance"""
    global ai_cache
    if ai_cache is None:
        ai_cache = AIResponseCache()
    return ai_cache

def get_location_cache():
    """Get global location cache instance"""
    global location_cache
    if location_cache is None:
        location_cache = LocationCache()
    return location_cache

def get_weather_cache():
    """Get global weather cache instance"""
    global weather_cache
    if weather_cache is None:
        weather_cache = WeatherCache()
    return weather_cache

def get_all_cache_stats() -> Dict:
    """Get statistics from all cache instances"""
    return {
        'ai_cache': get_ai_cache().get_stats(),
        'location_cache': get_location_cache().get_stats(),
        'weather_cache': get_weather_cache().get_stats()
    }