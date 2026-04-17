"""Security middleware for request validation and protection"""
import re
from flask import request, jsonify
from utils.logger import logger


def validate_content_type():
    """
    Validate Content-Type header for POST/PUT requests
    Should be called in before_request handler
    """
    if request.method in ['POST', 'PUT', 'PATCH']:
        content_type = request.content_type
        if not content_type:
            logger.warning(f"Missing Content-Type header from {request.remote_addr}")
            return None
        
        # Allow JSON and form data
        if 'application/json' not in content_type and 'application/x-www-form-urlencoded' not in content_type:
            logger.warning(f"Invalid Content-Type: {content_type} from {request.remote_addr}")
            return jsonify({
                'success': False,
                'message': 'Content-Type 必须是 application/json 或 application/x-www-form-urlencoded'
            }), 415
    
    return None


def sanitize_json_input(data):
    """
    Recursively sanitize JSON input to prevent XSS attacks
    
    Args:
        data: Input data (dict, list, or primitive)
        
    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        return {key: sanitize_json_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_input(item) for item in data]
    elif isinstance(data, str):
        # Remove potential XSS patterns
        sanitized = data
        # Remove script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        # Remove event handlers
        sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
        # Remove javascript: protocol
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        return sanitized.strip()
    else:
        return data


def check_sql_injection(text):
    """
    Check for potential SQL injection patterns
    
    Args:
        text: Text to check
        
    Returns:
        True if suspicious pattern found, False otherwise
    """
    if not isinstance(text, str):
        return False
    
    # Common SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b.*\b(FROM|INTO|TABLE|WHERE)\b)",
        r"(--|#|/\*)",  # SQL comments
        r"(\bOR\b\s+\d+\s*=\s*\d+)",  # OR 1=1
        r"(\bAND\b\s+\d+\s*=\s*\d+)",  # AND 1=1
        r"(;\s*(DROP|DELETE|UPDATE|INSERT))",  # Chained statements
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {text[:100]}")
            return True
    
    return False


def rate_limit_by_user(token_required_func):
    """
    Decorator to apply stricter rate limits for authenticated users
    
    Args:
        token_required_func: The token_required decorator function
        
    Returns:
        Decorated function with rate limiting
    """
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        @token_required_func
        def decorated_function(*args, **kwargs):
            # Additional user-specific rate limiting logic can be added here
            user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
            if user_id:
                logger.debug(f"Authenticated user {user_id} accessing {request.path}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class SecurityHeaders:
    """Add security headers to responses"""
    
    @staticmethod
    def add_security_headers(response):
        """
        Add security headers to response
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response with security headers
        """
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Strict Transport Security (HTTPS only)
        # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
