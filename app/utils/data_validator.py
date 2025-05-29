"""
Data Validator for SafeIndy Assistant
Validates and sanitizes user inputs for security and data integrity
"""

import re
import html
import json
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import validators
from datetime import datetime

class DataValidator:
    def __init__(self):
        # Dangerous patterns to detect
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'<iframe[^>]*>.*?</iframe>',  # Iframes
            r'<object[^>]*>.*?</object>',  # Objects
            r'<embed[^>]*>.*?</embed>',  # Embeds
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
            r'(\b--|\b#|\/\*|\*\/)',
            r'(\bOR\b|\bAND\b).*?=.*?=',
        ]
        
        # Command injection patterns
        self.command_patterns = [
            r'[;&|`$()]',
            r'\b(cat|ls|pwd|whoami|id|uname)\b',
            r'\.\./',
        ]
        
        print("✅ Data validator initialized")
    
    def validate_chat_message(self, message: str, max_length: int = 2000) -> Tuple[bool, str, Optional[str]]:
        """
        Validate chat message input
        
        Args:
            message: User's chat message
            max_length: Maximum allowed length
            
        Returns:
            Tuple of (is_valid, cleaned_message, error_message)
        """
        try:
            if not message or not isinstance(message, str):
                return False, "", "Message cannot be empty"
            
            # Check length
            if len(message) > max_length:
                return False, "", f"Message too long (max {max_length} characters)"
            
            # Check for suspicious patterns
            security_check = self._check_security_patterns(message)
            if not security_check['safe']:
                return False, "", f"Invalid input detected: {security_check['reason']}"
            
            # Clean and sanitize
            cleaned_message = self._sanitize_text(message)
            
            # Basic content validation
            if len(cleaned_message.strip()) == 0:
                return False, "", "Message cannot be empty after cleaning"
            
            # Check for excessive repetition (spam detection)
            if self._is_spam_message(cleaned_message):
                return False, "", "Excessive repetition detected"
            
            return True, cleaned_message, None
            
        except Exception as e:
            return False, "", f"Validation error: {str(e)}"
    
    def validate_location_data(self, location_data: Dict) -> Tuple[bool, Dict, Optional[str]]:
        """
        Validate location data from user
        
        Args:
            location_data: Dictionary containing location information
            
        Returns:
            Tuple of (is_valid, cleaned_data, error_message)
        """
        try:
            if not isinstance(location_data, dict):
                return False, {}, "Location data must be an object"
            
            cleaned_data = {}
            
            # Validate coordinates if present
            if 'lat' in location_data or 'lng' in location_data:
                lat_valid, lat_clean = self._validate_coordinate(location_data.get('lat'), 'latitude')
                lng_valid, lng_clean = self._validate_coordinate(location_data.get('lng'), 'longitude')
                
                if not (lat_valid and lng_valid):
                    return False, {}, "Invalid coordinates provided"
                
                cleaned_data['coordinates'] = {
                    'lat': lat_clean,
                    'lng': lng_clean
                }
            
            # Validate address if present
            if 'address' in location_data:
                address_valid, address_clean, error = self.validate_address(location_data['address'])
                if not address_valid:
                    return False, {}, error or "Invalid address"
                cleaned_data['address'] = address_clean
            
            # Validate accuracy if present
            if 'accuracy' in location_data:
                try:
                    accuracy = float(location_data['accuracy'])
                    if 0 <= accuracy <= 100000:  # Max 100km accuracy
                        cleaned_data['accuracy'] = accuracy
                except (ValueError, TypeError):
                    return False, {}, "Invalid accuracy value"
            
            return True, cleaned_data, None
            
        except Exception as e:
            return False, {}, f"Location validation error: {str(e)}"
    
    def validate_address(self, address: str, max_length: int = 200) -> Tuple[bool, str, Optional[str]]:
        """
        Validate address input
        
        Args:
            address: Address string
            max_length: Maximum allowed length
            
        Returns:
            Tuple of (is_valid, cleaned_address, error_message)
        """
        try:
            if not address or not isinstance(address, str):
                return False, "", "Address cannot be empty"
            
            # Check length
            if len(address) > max_length:
                return False, "", f"Address too long (max {max_length} characters)"
            
            # Security check
            security_check = self._check_security_patterns(address)
            if not security_check['safe']:
                return False, "", f"Invalid address format: {security_check['reason']}"
            
            # Clean address
            cleaned_address = self._sanitize_text(address)
            
            # Basic format validation
            if not re.match(r'^[a-zA-Z0-9\s,.-]+', cleaned_address):
                return False, "", "Address contains invalid characters"
            
            # Check for Indianapolis context
            if 'indianapolis' not in cleaned_address.lower() and 'in' not in cleaned_address.lower():
                cleaned_address += ', Indianapolis, IN'
            
            return True, cleaned_address, None
            
        except Exception as e:
            return False, "", f"Address validation error: {str(e)}"
    
    def validate_email(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """Validate email address"""
        try:
            if not email or not isinstance(email, str):
                return False, "", "Email cannot be empty"
            
            # Basic email validation
            if not validators.email(email):
                return False, "", "Invalid email format"
            
            # Security check
            security_check = self._check_security_patterns(email)
            if not security_check['safe']:
                return False, "", "Invalid email format"
            
            return True, email.lower().strip(), None
            
        except Exception as e:
            return False, "", f"Email validation error: {str(e)}"
    
    def validate_phone_number(self, phone: str) -> Tuple[bool, str, Optional[str]]:
        """Validate phone number"""
        try:
            if not phone or not isinstance(phone, str):
                return False, "", "Phone number cannot be empty"
            
            # Clean phone number (remove formatting)
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            
            # Check format (US numbers)
            if re.match(r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}', cleaned_phone):
                # Format as standard US number
                if cleaned_phone.startswith('+1'):
                    cleaned_phone = cleaned_phone[2:]
                elif cleaned_phone.startswith('1') and len(cleaned_phone) == 11:
                    cleaned_phone = cleaned_phone[1:]
                
                formatted_phone = f"({cleaned_phone[:3]}) {cleaned_phone[3:6]}-{cleaned_phone[6:]}"
                return True, formatted_phone, None
            
            return False, "", "Invalid phone number format"
            
        except Exception as e:
            return False, "", f"Phone validation error: {str(e)}"
    
    def validate_session_data(self, session_data: Dict) -> Tuple[bool, Dict, Optional[str]]:
        """Validate session data"""
        try:
            if not isinstance(session_data, dict):
                return False, {}, "Session data must be an object"
            
            cleaned_data = {}
            
            # Validate session ID
            if 'session_id' in session_data:
                session_id = session_data['session_id']
                if isinstance(session_id, str) and re.match(r'^[a-zA-Z0-9-]+', session_id):
                    cleaned_data['session_id'] = session_id
            
            # Validate chat history
            if 'chat_history' in session_data:
                history = session_data['chat_history']
                if isinstance(history, list) and len(history) <= 100:  # Limit history size
                    cleaned_history = []
                    for entry in history[-50:]:  # Keep last 50 entries
                        if isinstance(entry, dict):
                            cleaned_entry = {}
                            if 'user' in entry:
                                valid, clean_msg, _ = self.validate_chat_message(entry['user'])
                                if valid:
                                    cleaned_entry['user'] = clean_msg
                            if 'bot' in entry:
                                cleaned_entry['bot'] = entry['bot']  # Bot messages are safe
                            if 'timestamp' in entry:
                                cleaned_entry['timestamp'] = entry['timestamp']
                            if cleaned_entry:
                                cleaned_history.append(cleaned_entry)
                    
                    cleaned_data['chat_history'] = cleaned_history
            
            return True, cleaned_data, None
            
        except Exception as e:
            return False, {}, f"Session validation error: {str(e)}"
    
    def _validate_coordinate(self, coord: Any, coord_type: str) -> Tuple[bool, float]:
        """Validate a single coordinate (latitude or longitude)"""
        try:
            coord_float = float(coord)
            
            if coord_type == 'latitude':
                if -90 <= coord_float <= 90:
                    return True, coord_float
            elif coord_type == 'longitude':
                if -180 <= coord_float <= 180:
                    return True, coord_float
            
            return False, 0.0
            
        except (ValueError, TypeError):
            return False, 0.0
    
    def _check_security_patterns(self, text: str) -> Dict[str, Any]:
        """Check text for security threats"""
        try:
            text_lower = text.lower()
            
            # Check for XSS patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return {
                        'safe': False,
                        'reason': 'Potentially dangerous HTML/JavaScript detected',
                        'threat_type': 'xss'
                    }
            
            # Check for SQL injection patterns
            for pattern in self.sql_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return {
                        'safe': False,
                        'reason': 'Potentially dangerous SQL pattern detected',
                        'threat_type': 'sql_injection'
                    }
            
            # Check for command injection patterns
            for pattern in self.command_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return {
                        'safe': False,
                        'reason': 'Potentially dangerous command pattern detected',
                        'threat_type': 'command_injection'
                    }
            
            return {'safe': True, 'reason': None, 'threat_type': None}
            
        except Exception as e:
            return {
                'safe': False,
                'reason': f'Security check error: {str(e)}',
                'threat_type': 'validation_error'
            }
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text input"""
        try:
            # HTML escape
            sanitized = html.escape(text)
            
            # Remove null bytes
            sanitized = sanitized.replace('\x00', '')
            
            # Normalize whitespace
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()
            
            # Remove control characters except newlines and tabs
            sanitized = ''.join(char for char in sanitized 
                              if ord(char) >= 32 or char in ['\n', '\t'])
            
            return sanitized
            
        except Exception as e:
            print(f"❌ Text sanitization error: {e}")
            return text
    
    def _is_spam_message(self, message: str) -> bool:
        """Detect spam messages with excessive repetition"""
        try:
            # Check for repeated characters
            if re.search(r'(\w)\1{10,}', message):  # Same character 10+ times
                return True
            
            # Check for repeated words
            words = message.lower().split()
            if len(words) > 5:
                word_count = {}
                for word in words:
                    word_count[word] = word_count.get(word, 0) + 1
                    if word_count[word] > len(words) * 0.7:  # Word appears in 70%+ of message
                        return True
            
            # Check for repeated phrases
            if len(message) > 50:
                phrases = [message[i:i+20] for i in range(len(message)-19)]
                phrase_count = {}
                for phrase in phrases:
                    phrase_count[phrase] = phrase_count.get(phrase, 0) + 1
                    if phrase_count[phrase] > 3:  # Same 20-char phrase appears 3+ times
                        return True
            
            return False
            
        except Exception as e:
            return False
    
    def validate_api_response(self, response_data: Dict, expected_fields: List[str] = None) -> Tuple[bool, Dict, Optional[str]]:
        """Validate API response data"""
        try:
            if not isinstance(response_data, dict):
                return False, {}, "Response must be an object"
            
            cleaned_data = {}
            
            # Check for required fields
            if expected_fields:
                for field in expected_fields:
                    if field not in response_data:
                        return False, {}, f"Missing required field: {field}"
            
            # Sanitize string fields
            for key, value in response_data.items():
                if isinstance(value, str):
                    cleaned_data[key] = self._sanitize_text(value)
                elif isinstance(value, (int, float, bool)):
                    cleaned_data[key] = value
                elif isinstance(value, list):
                    cleaned_data[key] = value[:100]  # Limit array size
                elif isinstance(value, dict):
                    cleaned_data[key] = value  # Nested objects (could add recursive validation)
                else:
                    cleaned_data[key] = str(value)  # Convert other types to string
            
            return True, cleaned_data, None
            
        except Exception as e:
            return False, {}, f"API response validation error: {str(e)}"
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics"""
        return {
            'validator_status': 'active',
            'patterns_checked': {
                'xss_patterns': len(self.dangerous_patterns),
                'sql_patterns': len(self-sql_patterns),
                'command_patterns': len(self.command_patterns)
            },
            'supported_validations': [
                'chat_messages',
                'location_data',
                'addresses',
                'emails',
                'phone_numbers',
                'session_data',
                'api_responses'
            ]
        }

# Global validator instance
_validator = None

def get_validator():
    """Get global validator instance"""
    global _validator
    if _validator is None:
        _validator = DataValidator()
    return _validator

# Convenience functions for common validations
def validate_chat_input(message: str) -> Tuple[bool, str, Optional[str]]:
    """Quick chat message validation"""
    return get_validator().validate_chat_message(message)

def validate_location_input(location_data: Dict) -> Tuple[bool, Dict, Optional[str]]:
    """Quick location data validation"""
    return get_validator().validate_location_data(location_data)

def validate_email_input(email: str) -> Tuple[bool, str, Optional[str]]:
    """Quick email validation"""
    return get_validator().validate_email(email)