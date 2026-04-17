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
        return False, "用户名不能为空"
    
    if len(username) < 3 or len(username) > 50:
        return False, "用户名长度必须在3到50个字符之间"
    
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
        return False, "用户名只能包含字母、数字、下划线和中文字符"
    
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
        return False, "密码不能为空"
    
    if len(password) < 8:
        return False, "密码长度至少为8个字符"
    
    if len(password) > 128:
        return False, "密码长度不能超过128个字符"
    
    # Check for at least one uppercase letter, one lowercase letter, and one digit
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含至少一个大写字母"
    
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含至少一个小写字母"
    
    if not re.search(r'\d', password):
        return False, "密码必须包含至少一个数字"
    
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
        return False, "年龄不能为空"
    
    try:
        age = int(age)
    except (ValueError, TypeError):
        return False, "年龄必须是数字"
    
    if age < 1 or age > 150:
        return False, "年龄必须在1到150之间"
    
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
        return False, f"性别必须是以下值之一: {', '.join(valid_genders)}"
    
    return True, None


def validate_phone_number(phone_number):
    """
    Validate Chinese phone number format
    Supports formats: 13812345678, +8613812345678, 8613812345678
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not phone_number or not isinstance(phone_number, str):
        return False, "手机号码不能为空"
    
    # Remove spaces and dashes
    phone_number = phone_number.replace(' ', '').replace('-', '')
    
    # Remove country code prefix if present
    if phone_number.startswith('+86'):
        phone_number = phone_number[3:]
    elif phone_number.startswith('86'):
        phone_number = phone_number[2:]
    
    # Check if it's a valid Chinese mobile number (11 digits, starts with 1)
    if not re.match(r'^1[3-9]\d{9}$', phone_number):
        return False, "手机号码格式不正确，请输入有效的中国大陆手机号"
    
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
        return False, "问题不能为空"
    
    if len(question) < 2:
        return False, "问题长度至少为2个字符"
    
    if len(question) > 500:
        return False, "问题长度不能超过500个字符"
    
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
        return False, "疾病名称不能为空"
        
    if len(ill_name) < 1 or len(ill_name) > 100:
        return False, "疾病名称长度必须在1到100个字符之间"
        
    # Basic sanitization - remove potentially dangerous characters
    if re.search(r"[;'\"\\]", ill_name):
        return False, "疾病名称包含非法字符"
    
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
