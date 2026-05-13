"""Authentication and security utilities"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import Config
from utils.logger import logger


def hash_password(password):
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password, hashed_password):
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def generate_token(user_id, username, expires_delta=None):
    """
    Generate JWT access token
    
    Args:
        user_id: User ID
        username: Username
        expires_delta: Token expiration time in seconds (optional, defaults to Config.JWT_ACCESS_TOKEN_EXPIRES)
        
    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = Config.JWT_ACCESS_TOKEN_EXPIRES
    
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(seconds=expires_delta),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    logger.info(f"Token generated for user: {username}, expires in {expires_delta} seconds")
    return token


def decode_token(token):
    """
    Decode and verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"无效的Token: {e}")
        return None


def token_required(f):
    """
    Decorator to protect routes with JWT authentication
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({
                    'success': False,
                    'message': '无效的Token格式。请使用: Bearer <token>'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'message': '缺少Token'
            }), 401
        
        # Decode token
        payload = decode_token(token)
        if payload is None:
            return jsonify({
                'success': False,
                'message': 'Token无效或已过期'
            }), 401
        
        # Add user info to request context
        request.current_user = payload
        logger.debug(f"Authenticated user: {payload.get('username')}")
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    Decorator to require admin privileges
    
    Usage:
        @app.route('/admin')
        @admin_required
        def admin_route():
            ...
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        # Check if user is admin (you may need to adjust this based on your user model)
        if not request.current_user.get('is_admin', False):
            return jsonify({
                'success': False,
                'message': '需要管理员权限'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated
