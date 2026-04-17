"""API response utilities for consistent response format"""
from flask import jsonify
from utils.logger import logger


class APIResponse:
    """Standardized API response formatter"""
    
    @staticmethod
    def success(data=None, message='成功', status_code=200):
        """
        Format successful response
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            Flask response object
        """
        response = {
            'success': True,
            'message': message
        }
        
        if data is not None:
            response['data'] = data
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message='发生错误', error_code=None, status_code=400, details=None):
        """
        Format error response
        
        Args:
            message: Error message
            error_code: Custom error code
            status_code: HTTP status code
            details: Additional error details
            
        Returns:
            Flask response object
        """
        response = {
            'success': False,
            'message': message
        }
        
        if error_code is not None:
            response['error_code'] = error_code
        
        if details is not None:
            response['details'] = details
        
        logger.error(f"API Error [{status_code}]: {message}")
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(message='验证失败', errors=None):
        """
        Format validation error response
        
        Args:
            message: Error message
            errors: List of validation errors
            
        Returns:
            Flask response object
        """
        response = {
            'success': False,
            'message': message,
            'error_type': 'validation_error'
        }
        
        if errors:
            response['errors'] = errors
        
        return jsonify(response), 400
    
    @staticmethod
    def unauthorized(message='需要身份认证'):
        """
        Format unauthorized response
        
        Args:
            message: Error message
            
        Returns:
            Flask response object
        """
        return APIResponse.error(
            message=message,
            error_code='UNAUTHORIZED',
            status_code=401
        )
    
    @staticmethod
    def forbidden(message='访问被拒绝'):
        """
        Format forbidden response
        
        Args:
            message: Error message
            
        Returns:
            Flask response object
        """
        return APIResponse.error(
            message=message,
            error_code='FORBIDDEN',
            status_code=403
        )
    
    @staticmethod
    def not_found(message='资源不存在'):
        """
        Format not found response
        
        Args:
            message: Error message
            
        Returns:
            Flask response object
        """
        return APIResponse.error(
            message=message,
            error_code='NOT_FOUND',
            status_code=404
        )
    
    @staticmethod
    def internal_error(message='服务器内部错误', details=None):
        """
        Format internal server error response
        
        Args:
            message: Error message
            details: Error details (only in development)
            
        Returns:
            Flask response object
        """
        from config import Config
        
        # Don't expose details in production
        if Config.DEBUG:
            return APIResponse.error(
                message=message,
                error_code='INTERNAL_ERROR',
                status_code=500,
                details=details
            )
        else:
            return APIResponse.error(
                message=message,
                error_code='INTERNAL_ERROR',
                status_code=500
            )
    
    @staticmethod
    def rate_limit_exceeded(message='请求频率超限，请稍后重试'):
        """
        Format rate limit exceeded response
        
        Args:
            message: Error message
            
        Returns:
            Flask response object
        """
        return APIResponse.error(
            message=message,
            error_code='RATE_LIMIT_EXCEEDED',
            status_code=429
        )
