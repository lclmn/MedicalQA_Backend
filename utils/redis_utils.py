"""Shared Redis connection management utility"""
import redis
from config import Config
from utils.logger import logger

_redis_clients = {}


def get_redis_client(db: int = None, decode_responses: bool = False) -> redis.Redis:
    """
    Get or create a Redis client for the given configuration.

    Args:
        db: Redis DB number (defaults to Config.REDIS_DB)
        decode_responses: Whether to auto-decode responses to str

    Returns:
        Redis client instance, or None if Redis is not configured
    """
    if not Config.REDIS_HOST:
        return None

    if db is None:
        db = Config.REDIS_DB

    cache_key = f"{db}:{decode_responses}"

    if cache_key not in _redis_clients:
        try:
            params = {
                'host': Config.REDIS_HOST,
                'port': Config.REDIS_PORT,
                'db': db,
                'decode_responses': decode_responses,
                'socket_connect_timeout': 5,
            }
            if Config.REDIS_PASSWORD:
                params['password'] = Config.REDIS_PASSWORD

            client = redis.Redis(**params)
            client.ping()
            _redis_clients[cache_key] = client
            logger.info(f"Redis connected (db={db}, decode={decode_responses})")
        except Exception as e:
            logger.warning(f"Redis connection failed (db={db}): {e}")
            return None

    return _redis_clients[cache_key]


def close_all():
    """Close all Redis connections gracefully."""
    for key, client in list(_redis_clients.items()):
        try:
            client.close()
            logger.info(f"Redis connection closed: {key}")
        except Exception as e:
            logger.error(f"Error closing Redis {key}: {e}")
    _redis_clients.clear()
