"""Input validation utilities"""
import re
from utils.logger import logger


def validate_username(username):
    """
    Validate username format
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    if len(username) < 3 or len(username) > 50:
        return False, "Username must be between 3 and 50 characters"
    
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and Chinese characters"
    
    return True, None


def validate_password(password):
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    # Check for at least one uppercase letter, one lowercase letter, and one digit
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, None


def validate_age(age):
    """
    Validate age
    
    Args:
        age: Age to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if age is None:
        return False, "Age is required"
    
    try:
        age = int(age)
    except (ValueError, TypeError):
        return False, "Age must be a number"
    
    if age < 1 or age > 150:
        return False, "Age must be between 1 and 150"
    
    return True, None


def validate_gender(gender):
    """
    Validate gender
    
    Args:
        gender: Gender to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    valid_genders = ['male', 'female', 'other', '男', '女', '其他']
    
    if not gender or gender not in valid_genders:
        return False, f"Gender must be one of: {', '.join(valid_genders)}"
    
    return True, None


def validate_question(question):
    """
    Validate medical question
    
    Args:
        question: Question to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not question or not isinstance(question, str):
        return False, "Question is required"
    
    if len(question) < 2:
        return False, "Question must be at least 2 characters long"
    
    if len(question) > 500:
        return False, "Question must be less than 500 characters"
    
    return True, None


def validate_ill_name(ill_name):
    """
    Validate disease name
    
    Args:
        ill_name: Disease name to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not ill_name or not isinstance(ill_name, str):
        return False, "Disease name is required"
    
    if len(ill_name) < 1 or len(ill_name) > 100:
        return False, "Disease name must be between 1 and 100 characters"
    
    # Basic sanitization - remove potentially dangerous characters
    if re.search(r'[;\'\"\\]', ill_name):
        return False, "Disease name contains invalid characters"
    
    return True, None


def sanitize_input(text):
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return text
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Escape special characters
    text = text.replace('\\', '\\\\')
    text = text.replace("'", "\\'")
    text = text.replace('"', '\\"')
    
    return text.strip()
