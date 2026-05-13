"""Neo4j database connection management utilities"""
from neo4j import GraphDatabase, basic_auth
from config import Config
from utils.logger import logger


class Neo4jConnectionPool:
    """Neo4j connection pool manager with optimized settings"""
    
    _instance = None
    _driver = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._driver is None:
            self._create_driver()
    
    def _create_driver(self):
        """Create Neo4j driver with optimized connection pool settings"""
        try:
            self._driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=basic_auth(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=50,   # Max connections in pool
                connection_acquisition_timeout=60,  # Timeout for acquiring connection
                keep_alive=True  # Enable keep-alive
            )
            # Verify connection
            self._driver.verify_connectivity()
            logger.info("Neo4j connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create Neo4j connection pool: {e}")
            raise
    
    def get_driver(self):
        """Get the Neo4j driver instance"""
        if self._driver is None:
            self._create_driver()
        return self._driver
    
    def close(self):
        """Close the Neo4j driver"""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection pool closed")


# Singleton instance
neo4j_pool = Neo4jConnectionPool()


def get_neo4j_driver():
    """
    Get Neo4j driver from the pool
    
    Returns:
        Neo4j driver instance
    """
    return neo4j_pool.get_driver()


def execute_cypher_query(cypher: str, parameters: dict = None, read_only: bool = True):
    """
    Execute a Cypher query with proper session management
    
    Args:
        cypher: Cypher query string
        parameters: Query parameters (dict)
        read_only: Whether this is a read-only query
        
    Returns:
        Query results as list of dicts
    """
    driver = get_neo4j_driver()
    try:
        if read_only:
            with driver.session(default_access_mode='READ') as session:
                result = session.run(cypher, **(parameters or {}))
                return result.data()
        else:
            with driver.session(default_access_mode='WRITE') as session:
                result = session.run(cypher, **(parameters or {}))
                return result.data()
    except Exception as e:
        logger.error(f"Cypher query execution failed: {e}\nQuery: {cypher}")
        raise


def batch_execute_cypher(queries: list):
    """
    Execute multiple Cypher queries in a single transaction
    
    Args:
        queries: List of tuples (cypher_string, parameters_dict)
        
    Returns:
        List of results
    """
    driver = get_neo4j_driver()
    results = []
    
    try:
        with driver.session(default_access_mode='WRITE') as session:
            with session.begin_transaction() as tx:
                for cypher, params in queries:
                    result = tx.run(cypher, **params)
                    results.append(result.data())
                tx.commit()
        logger.info(f"Batch executed {len(queries)} queries successfully")
        return results
    except Exception as e:
        logger.error(f"Batch Cypher execution failed: {e}")
        raise
