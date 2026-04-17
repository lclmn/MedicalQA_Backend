"""Configuration management module"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (only for non-sensitive configs)
# Sensitive keys (DEEPSEEK_API_KEY) should be set in system environment variables for security
load_dotenv()


class Config:
    """Base configuration"""
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
    
    # DeepSeek API Configuration
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    
    # SMS Configuration - Using Mock Service for local testing
    # In production, replace with real SMS service configuration if needed
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '123456')
    MYSQL_DB = os.getenv('MYSQL_DB', 'userdb')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('FLASK_PORT', '5001'))
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)  # Optional Redis password
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Database connection pool settings
    MYSQL_POOL_SIZE = 5
    MYSQL_MAX_OVERFLOW = 10
    MYSQL_POOL_TIMEOUT = 30
    MYSQL_POOL_RECYCLE = 3600
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check required environment variables
        if not cls.NEO4J_URI:
            errors.append("NEO4J_URI 配置项为必填项")
        
        if not cls.DEEPSEEK_API_KEY and not cls.DEBUG:
            errors.append("生产环境下 DEEPSEEK_API_KEY 为必填项")
        
        # Security checks for production
        if not cls.DEBUG:
            if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
                errors.append("生产环境下必须修改 SECRET_KEY")
            if cls.JWT_SECRET_KEY == 'jwt-secret-key-change-in-production':
                errors.append("生产环境下必须修改 JWT_SECRET_KEY")
            if cls.CORS_ORIGINS == '*':
                errors.append("生产环境下应限制 CORS_ORIGINS")
        
        if errors:
            raise ValueError(f"配置验证失败:\n" + "\n".join(errors))
        
        return True


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    @classmethod
    def validate(cls):
        """Validate required production settings"""
        # Call parent validation first
        super().validate()
        
        # Additional production-specific checks
        if not cls.DEEPSEEK_API_KEY:
            raise ValueError("生产环境下必须设置 DEEPSEEK_API_KEY")


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, config_by_name['default'])
