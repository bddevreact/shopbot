import re
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

class SecurityManager:
    """Professional security and validation system"""
    
    def __init__(self):
        self.failed_attempts = {}  # user_id -> count
        self.blocked_users = set()
        self.rate_limits = {}  # user_id -> last_action_time
    
    def validate_user_input(self, text: str, input_type: str = "general") -> Dict[str, Any]:
        """Validate user input with comprehensive checks"""
        result = {
            'valid': True,
            'sanitized': text,
            'errors': []
        }
        
        # Basic length checks
        if len(text) > 1000:
            result['valid'] = False
            result['errors'].append("Input too long (max 1000 characters)")
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '&', '"', "'", '\\', '/', '`']
        for char in dangerous_chars:
            if char in text:
                result['sanitized'] = result['sanitized'].replace(char, '')
        
        # Type-specific validation
        if input_type == "address":
            result = self._validate_address(text)
        elif input_type == "phrase_code":
            result = self._validate_phrase_code(text)
        elif input_type == "discount_code":
            result = self._validate_discount_code(text)
        
        return result
    
    def _validate_address(self, address: str) -> Dict[str, Any]:
        """Validate delivery address"""
        result = {
            'valid': True,
            'sanitized': address,
            'errors': []
        }
        
        # Check for minimum required fields
        required_fields = ['name', 'street', 'city', 'country']
        address_lower = address.lower()
        
        if len(address) < 20:
            result['valid'] = False
            result['errors'].append("Address too short")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'http[s]?://',  # URLs
            r'@\w+',         # Email-like patterns
            r'\b\d{4,}\b',   # Long numbers (potential card numbers)
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, address):
                result['valid'] = False
                result['errors'].append("Address contains suspicious content")
                break
        
        return result
    
    def _validate_phrase_code(self, phrase: str) -> Dict[str, Any]:
        """Validate secret phrase code"""
        result = {
            'valid': True,
            'sanitized': phrase,
            'errors': []
        }
        
        if len(phrase) < 20:
            result['valid'] = False
            result['errors'].append("Phrase code must be at least 20 characters")
        elif len(phrase) > 40:
            result['valid'] = False
            result['errors'].append("Phrase code must be 40 characters or less")
        
        # Check for common weak patterns
        weak_patterns = [
            r'^[0-9]+$',           # Only numbers
            r'^[a-zA-Z]+$',        # Only letters
            r'(.)\1{3,}',          # Repeated characters
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, phrase):
                result['valid'] = False
                result['errors'].append("Phrase code is too weak")
                break
        
        return result
    
    def _validate_discount_code(self, code: str) -> Dict[str, Any]:
        """Validate discount code"""
        result = {
            'valid': True,
            'sanitized': code.upper().strip(),
            'errors': []
        }
        
        if len(code) < 3 or len(code) > 20:
            result['valid'] = False
            result['errors'].append("Discount code must be 3-20 characters")
        
        if not re.match(r'^[A-Z0-9_-]+$', code.upper()):
            result['valid'] = False
            result['errors'].append("Discount code contains invalid characters")
        
        return result
    
    def check_rate_limit(self, user_id: int, action: str = "general") -> bool:
        """Check if user is rate limited"""
        now = datetime.now()
        key = f"{user_id}_{action}"
        
        if key in self.rate_limits:
            time_diff = now - self.rate_limits[key]
            if time_diff < timedelta(seconds=1):  # 1 second rate limit
                return False
        
        self.rate_limits[key] = now
        return True
    
    def check_failed_attempts(self, user_id: int) -> bool:
        """Check if user has too many failed attempts"""
        if user_id in self.blocked_users:
            return False
        
        failed_count = self.failed_attempts.get(user_id, 0)
        if failed_count >= 5:  # Block after 5 failed attempts
            self.blocked_users.add(user_id)
            return False
        
        return True
    
    def record_failed_attempt(self, user_id: int):
        """Record a failed attempt"""
        self.failed_attempts[user_id] = self.failed_attempts.get(user_id, 0) + 1
    
    def reset_failed_attempts(self, user_id: int):
        """Reset failed attempts for user"""
        if user_id in self.failed_attempts:
            del self.failed_attempts[user_id]
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for logging"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for logging (remove sensitive info)"""
        sensitive_fields = ['address', 'phrase_code', 'private_key', 'passphrase']
        sanitized = data.copy()
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = self.hash_sensitive_data(str(sanitized[field]))
        
        return sanitized

# Global security manager instance
security_manager = SecurityManager()
