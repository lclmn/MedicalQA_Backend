"""Database connection management utilities"""
import pymysql
from dbutils.pooled_db import PooledDB
from config import Config
from utils.logger import logger


class MySQLConnectionPool:
    """MySQL connection pool manager"""
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            self._create_pool()
    
    def _create_pool(self):
        """Create connection pool"""
        try:
            self._pool = PooledDB(
                creator=pymysql,
                maxconnections=Config.MYSQL_POOL_SIZE,
                mincached=2,
                maxcached=5,
                maxshared=3,
                blocking=True,
                maxusage=None,
                setsession=[],
                ping=1,
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                port=3306,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info("MySQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create MySQL connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        try:
            connection = self._pool.connection()
            logger.debug("Got connection from pool")
            return connection
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise
    
    def close(self):
        """Close the connection pool"""
        if self._pool:
            self._pool.close()
            logger.info("MySQL connection pool closed")


# Singleton instance
db_pool = MySQLConnectionPool()


def get_db_connection():
    """
    Get a database connection from the pool
    
    Returns:
        pymysql connection object
    """
    return db_pool.get_connection()
