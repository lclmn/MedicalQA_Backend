from flask import Flask,request,render_template,jsonify
from flask_cors import CORS
import logging
from langchain_qa import get_answer
from user import api_bp
from config import Config
from utils.logger import logger
from utils.validators import validate_question, validate_ill_name
from utils.neo4j_utils import get_neo4j_driver, execute_cypher_query
from utils.security import SecurityHeaders, sanitize_json_input, check_sql_injection
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import pickle


app = Flask(__name__,static_folder='./dist',  #设置静态文件夹目录
template_folder = "./dist",static_url_path="")
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Enable CORS with restricted origins in production
if Config.DEBUG:
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    # In production, specify allowed origins
    allowed_origins = Config.CORS_ORIGINS.split(',') if hasattr(Config, 'CORS_ORIGINS') else ['https://yourdomain.com']
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# Setup rate limiting with Redis backend
if Config.REDIS_HOST:
    # Build Redis URL with password if configured
    if Config.REDIS_PASSWORD:
        redis_url = f"redis://:{Config.REDIS_PASSWORD}@{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
    else:
        redis_url = f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
else:
    redis_url = None

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=redis_url
)

# Get Neo4j driver from connection pool
driver = get_neo4j_driver()
app.register_blueprint(api_bp, url_prefix='/api')

# Initialize Redis cache if available
redis_cache = None
try:
    if Config.REDIS_HOST:
        redis_params = {
            'host': Config.REDIS_HOST,
            'port': Config.REDIS_PORT,
            'db': Config.REDIS_DB,
            'decode_responses': False,
            'socket_connect_timeout': 5
        }
        
        # Add password if configured
        if Config.REDIS_PASSWORD:
            redis_params['password'] = Config.REDIS_PASSWORD
        
        redis_cache = redis.Redis(**redis_params)
        redis_cache.ping()
        logger.info("Redis cache connected successfully")
    else:
        logger.info("Redis not configured, using in-memory cache only")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Using in-memory cache only.")
    redis_cache = None


def cache_get(key: str):
    """Get value from cache (Redis or memory)"""
    try:
        if redis_cache:
            value = redis_cache.get(key)
            if value:
                return pickle.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
        return None


def cache_set(key: str, value, ttl: int = 3600):
    """Set value in cache (Redis or memory)"""
    try:
        if redis_cache:
            redis_cache.setex(key, ttl, pickle.dumps(value))
    except Exception as e:
        logger.warning(f"Cache set error: {e}")


def get_result(ill=''):
    """Get graph data with optimized queries and connection pooling"""
    try:
        if ill:
            # Validate input
            is_valid, error_msg = validate_ill_name(ill)
            if not is_valid:
                logger.warning(f"Invalid disease name: {error_msg}")
                return {'graph_data': [], 'links': [], 'labels': [], 'stats': {'node_count': 0, 'link_count': 0, 'category_count': 0}}
            
            # Use parameterized query to prevent injection
            cql = "MATCH (a) WHERE a.name CONTAINS $ill OPTIONAL MATCH (a)-[r]-(b) RETURN a, labels(a) as aa, r, b, labels(b) as bb LIMIT 200"
            result_data = execute_cypher_query(cql, {'ill': ill}, read_only=True)
        else:
            cql = "MATCH (a)-[r]->(b) RETURN a, labels(a) as aa, r, b, labels(b) as bb LIMIT 200"
            result_data = execute_cypher_query(cql, read_only=True)

        # Process results efficiently
        graph_data = []
        links = []
        seen_nodes = set()  # Use set for O(1) lookup
        labels_set = set()
        labels = []
        
        for item in result_data:
            # Process node 'a'
            if 'a' in item and item['a']:
                node_a_name = item['a'].get('name')
                if node_a_name and node_a_name not in seen_nodes:
                    graph_data.append({
                        "name": node_a_name,
                        "symbolSize": 50,
                        "category": item.get("aa", [""])[0],
                    })
                    seen_nodes.add(node_a_name)
            
            # Process node 'b'
            if 'b' in item and item['b']:
                node_b_name = item['b'].get('name')
                if node_b_name and node_b_name not in seen_nodes:
                    graph_data.append({
                        "name": node_b_name,
                        "symbolSize": 50,
                        "category": item.get("bb", [""])[0],
                    })
                    seen_nodes.add(node_b_name)
            
            # Process relationship 'r'
            if 'r' in item and item['r']:
                rel = item['r']
                # Neo4j driver returns relationships as dict-like objects
                # The relationship object has: _properties, start_node, end_node, type
                try:
                    # Extract relationship type
                    if hasattr(rel, 'type'):
                        rel_type = rel.type
                    elif isinstance(rel, dict) and 'type' in rel:
                        rel_type = rel['type']
                    else:
                        rel_type = ''
                    
                    # Extract source and target node names
                    # When we RETURN a, r, b - the relationship connects a and b
                    if 'a' in item and item['a'] and 'b' in item and item['b']:
                        source_name = item['a'].get('name', '')
                        target_name = item['b'].get('name', '')
                        
                        if source_name and target_name:
                            links.append({
                                "source": source_name,
                                "target": target_name,
                                "name": rel_type
                            })
                except Exception as e:
                    logger.warning(f"Failed to process relationship: {e}")
            
            # Collect unique labels
            for key in ['aa', 'bb']:
                if key in item and item[key]:
                    label_name = item[key][0]
                    if label_name and label_name not in labels_set:
                        labels.append({"name": label_name})
                        labels_set.add(label_name)
        
        # Calculate statistics
        stats = {
            'node_count': len(graph_data),
            'link_count': len(links),
            'category_count': len(labels)
        }
        
        logger.info(f"Graph data retrieved: {stats['node_count']} nodes, {stats['link_count']} links")
        return {
            'graph_data': graph_data,
            'links': links,
            'labels': labels,
            'stats': stats
        }
    except Exception as e:
        logger.error(f"Error in get_result: {e}", exc_info=True)
        return {'graph_data': [], 'links': [], 'labels': [], 'stats': {'node_count': 0, 'link_count': 0, 'category_count': 0}}

@app.route('/get_graph',methods=['GET'])
def get_graph():
    ill = request.args.get("ill", "")
    try:
        # Use cache for better performance
        cache_key = f"graph_data:{ill}"
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for graph data: {ill}")
            return jsonify(cached_result)
        
        results = get_result(ill)
        
        # Cache the result for 1 hour
        cache_set(cache_key, results, ttl=3600)
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in get_graph endpoint: {e}")
        return jsonify({'error': '获取图谱数据失败'}), 500

@app.route('/get_ill_info',methods=['GET'])
def get_ill_info():
    try:
        ill_list = request.args.getlist("ill")
        if not ill_list:
            return jsonify({'error': '疾病名称不能为空'}), 400
        
        ill = ill_list[0]
        
        # Validate input
        is_valid, error_msg = validate_ill_name(ill)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Use cache for better performance
        cache_key = f"ill_info:{ill}"
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for disease info: {ill}")
            return jsonify(cached_result)
        
        # Use parameterized query to find matching diseases
        search_cql = "MATCH (n:ill) WHERE n.name CONTAINS $ill RETURN n.name as ill_name"
        result_data = execute_cypher_query(search_cql, {'ill': ill}, read_only=True)
        
        all_ills_info = []
        for record in result_data:
            ill_name = record['ill_name']
            
            # Get all disease details in a single optimized query
            details_cql = """
            MATCH (ill:ill {name: $ill_name})
            OPTIONAL MATCH (ill)-[:has_symptom]->(s:symptom)
            OPTIONAL MATCH (ill)-[:should_see]->(d:department)
            OPTIONAL MATCH (ill)-[:belongs_to_class1]->(c1:class1)
            OPTIONAL MATCH (ill)-[:belongs_to_class2]->(c2:class2)
            OPTIONAL MATCH (ill)-[:affects_people]->(p:easy_ill_people)
            OPTIONAL MATCH (ill)-[:treated_by]->(m:cure_method)
            OPTIONAL MATCH (ill)-[:costs]->(cost:cure_cost)
            OPTIONAL MATCH (ill)-[:is_infectious]->(infect_node:if_infect)
            OPTIONAL MATCH (ill)-[:has_proportion]->(prop:ill_proportion)
            OPTIONAL MATCH (ill)-[:has_cure_rate]->(rate:cure_rate)
            OPTIONAL MATCH (ill)-[:has_healing_cycle]->(cycle:healing_cycle)
            RETURN ill.name as name,
                   ill.source_link as source_link,
                   collect(DISTINCT s.name) as symptom,
                   collect(DISTINCT d.name) as department,
                   collect(DISTINCT c1.name) as class1,
                   collect(DISTINCT c2.name) as class2,
                   collect(DISTINCT p.name) as easy_ill_people,
                   collect(DISTINCT m.name) as cure_method,
                   collect(DISTINCT cost.name) as cure_cost,
                   collect(DISTINCT infect_node.name) as if_infect,
                   collect(DISTINCT prop.name) as ill_proportion,
                   collect(DISTINCT rate.name) as cure_rate,
                   collect(DISTINCT cycle.name) as healing_cycle
            """
            details_data = execute_cypher_query(details_cql, {'ill_name': ill_name}, read_only=True)
            
            if details_data:
                disease_info = details_data[0]
                processed_info = {}
                for key, value in disease_info.items():
                    if isinstance(value, list):
                        cleaned_list = [item for item in value if item]
                        processed_info[key] = ", ".join(cleaned_list) if cleaned_list else "暂无信息"
                    else:
                        processed_info[key] = value if value else "暂无信息"
                all_ills_info.append({"data": processed_info})

        logger.info(f"Retrieved info for disease: {ill}, found {len(all_ills_info)} results")
        
        # Cache the result for 2 hours
        cache_set(cache_key, all_ills_info, ttl=7200)
        
        return jsonify(all_ills_info)
    except Exception as e:
        logger.error(f"Error in get_ill_info: {e}", exc_info=True)
        return jsonify({'error': '获取疾病信息失败'}), 500


@app.route('/question',methods=['GET'])
@limiter.limit("30 per minute")
def medical_answer():
    try:
        question_list = request.args.getlist("question")
        if not question_list:
            return jsonify({'error': '问题不能为空'}), 400
        
        question = question_list[0]
        
        # Validate input
        is_valid, error_msg = validate_question(question)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        logger.info(f"Received question: {question}")
        result = get_answer(question)
        
        # Extract answer from result dict (backward compatible)
        if isinstance(result, dict):
            answer = result.get('answer', '')
            source = result.get('source', 'unknown')
            confidence = result.get('confidence', 'unknown')
        else:
            answer = result
            source = 'unknown'
            confidence = 'unknown'
        
        logger.info(f"Answer generated successfully from {source}")
        
        # Try to save conversation if user is authenticated
        conversation_id = request.args.get('conversation_id')
        if conversation_id and 'Authorization' in request.headers:
            try:
                from utils.auth import decode_token
                from utils.db_utils import get_db_connection
                auth_header = request.headers['Authorization']
                token = auth_header.split(" ")[1] if " " in auth_header else None
                if token:
                    payload = decode_token(token)
                    if payload:
                        user_id = payload.get('user_id')
                        username = payload.get('username')
                        # Save conversation as JSON format: {"username": "...", "AI": "..."}
                        _save_conversation_to_db(user_id, username, conversation_id, question, answer)
                        logger.info(f"Conversation saved for user_id={user_id}, conversation_id={conversation_id}")
            except Exception as e:
                logger.warning(f"Failed to save conversation: {e}")
        
        return jsonify({
            'answer': answer,
            'source': source,
            'confidence': confidence
        })
    except Exception as e:
        logger.error(f"Error in medical_answer: {e}")
        return jsonify({'error': '生成答案失败'}), 500


def _save_conversation_to_db(user_id, username, conversation_id, question, answer):
    """
    Helper function to save conversation to database
    Format: {"username": "问题内容", "AI": "AI回答内容"}
    """
    try:
        import json
        from utils.db_utils import get_db_connection
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Create JSON object with username and AI response
                conversation_data = json.dumps({
                    username: question,
                    "AI": answer
                }, ensure_ascii=False)
                
                insert_query = "INSERT INTO conversations (user_id, username, conversation_id, conversation_data) VALUES (%s, %s, %s, %s)"
                cursor.execute(insert_query, (user_id, username, conversation_id, conversation_data))
                connection.commit()
        finally:
            connection.close()
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        raise

@app.route('/search_suggestions', methods=['GET'])
@limiter.limit("60 per minute")
def search_suggestions():
    """
    Get disease name suggestions for autocomplete
    Query parameter: keyword (required)
    Optional: limit (default 10)
    """
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'error': '搜索关键词不能为空'}), 400
        
        if len(keyword) < 1 or len(keyword) > 50:
            return jsonify({'error': '关键词长度必须在1到50个字符之间'}), 400
        
        limit = request.args.get('limit', 10, type=int)
        limit = min(max(limit, 1), 20)  # Limit between 1 and 20
        
        from langchain_qa import get_search_suggestions
        suggestions = get_search_suggestions(keyword, limit)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
    except Exception as e:
        logger.error(f"Error in search_suggestions: {e}")
        return jsonify({'error': '获取搜索建议失败'}), 500


@app.route('/get_analysis_data', methods=['GET'])
def get_analysis_data():
    try:
        # 1. Node count statistics - use batch queries for efficiency
        node_counts = []
        labels_to_count = ["ill", "symptom", "department", "cure_method"]
        label_names = {
            "ill": "疾病", 
            "symptom": "症状", 
            "department": "科室", 
            "cure_method": "治疗方法"
        }
        
        for label in labels_to_count:
            cql = f"MATCH (n:{label}) RETURN count(n) as count"
            result = execute_cypher_query(cql, read_only=True)
            count = result[0]['count'] if result else 0
            if count > 0:
                node_counts.append({"name": label_names.get(label, label), "value": count})

        # 2. Disease count by first-level classification
        class1_ill_counts_cql = """
        MATCH (c1:class1)<-[:belongs_to_class1]-(ill:ill)
        WHERE c1.name IS NOT NULL AND c1.name <> '一级分类'
        RETURN c1.name as name, count(ill) as value
        ORDER BY value DESC
        LIMIT 10
        """
        class1_result = execute_cypher_query(class1_ill_counts_cql, read_only=True)
        class1_ill_counts = [
            {"name": record["name"], "value": record["value"]}
            for record in class1_result if record["name"]
        ]

        # 3. Infectious disease ratio
        infectious_counts_cql = """
        MATCH (i:if_infect)<-[:is_infectious]-(ill:ill)
        WHERE i.name IS NOT NULL AND i.name <> '是否传染'
        RETURN i.name as name, count(ill) as value
        ORDER BY value DESC
        """
        infectious_result = execute_cypher_query(infectious_counts_cql, read_only=True)
        infectious_counts = [
            {"name": record["name"], "value": record["value"]}
            for record in infectious_result if record["name"]
        ]

        # 4. Healing cycle distribution (Top 10)
        healing_cycle_counts_cql = """
        MATCH (h:healing_cycle)<-[:has_healing_cycle]-(ill:ill)
        WHERE h.name IS NOT NULL AND h.name <> '暂无信息'
        RETURN h.name as name, count(ill) as value
        ORDER BY value DESC
        LIMIT 10
        """
        healing_result = execute_cypher_query(healing_cycle_counts_cql, read_only=True)
        healing_cycle_counts = [
            {"name": record["name"], "value": record["value"]}
            for record in healing_result if record["name"]
        ]

        analysis_data = {
            "node_counts": node_counts,
            "class1_ill_counts": class1_ill_counts,
            "infectious_counts": infectious_counts,
            "healing_cycle_counts": healing_cycle_counts,
        }
        
        logger.info("Analysis data retrieved successfully")
        return jsonify(analysis_data)
        
    except Exception as e:
        logger.error(f"Error in get_analysis_data: {e}", exc_info=True)
        return jsonify({
            "node_counts": [],
            "class1_ill_counts": [],
            "infectious_counts": [],
            "healing_cycle_counts": [],
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with comprehensive service status"""
    try:
        # Check Neo4j connection
        neo4j_status = "healthy"
        try:
            result = execute_cypher_query("RETURN 1 as test", read_only=True)
            if not result or result[0].get('test') != 1:
                neo4j_status = "unhealthy"
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            neo4j_status = "unhealthy"
        
        # Check Redis connection
        redis_status = "healthy"
        try:
            if redis_cache:
                redis_cache.ping()
            else:
                redis_status = "not configured"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_status = "unhealthy"
        
        return jsonify({
            'status': 'healthy' if neo4j_status == 'healthy' else 'degraded',
            'services': {
                'neo4j': neo4j_status,
                'redis': redis_status,
                'flask': 'healthy'
            },
            'timestamp': logger.handlers[0].formatter.formatTime(
                logger.makeRecord('health', 20, '', 0, '', (), None),
                '%Y-%m-%d %H:%M:%S'
            )
        })
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route("/")
def index():
    return render_template('index.html',name='index')


# Request logging middleware
@app.before_request
def log_request_info():
    """Log incoming request information and perform security checks"""
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
    
    # Check for SQL injection in query parameters
    for key, value in request.args.items():
        if check_sql_injection(value):
            logger.warning(f"SQL injection attempt detected in query param: {key}")
            return jsonify({'error': '检测到非法输入'}), 400
    
    # Sanitize JSON input for POST requests
    if request.is_json and request.get_json(silent=True):
        sanitized_data = sanitize_json_input(request.get_json())
        # Note: We can't easily replace request.json, but we log it
        logger.debug(f"Sanitized JSON input for {request.path}")
    
    if request.args:
        logger.debug(f"Query params: {dict(request.args)}")


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response = SecurityHeaders.add_security_headers(response)
    logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
    return response


# Graceful shutdown
import signal
import sys

def graceful_shutdown(signum, frame):
    """Handle graceful shutdown"""
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    
    # Close Neo4j driver
    try:
        from utils.neo4j_utils import neo4j_pool
        neo4j_pool.close()
        logger.info("Neo4j connection pool closed")
    except Exception as e:
        logger.error(f"Error closing Neo4j pool: {e}")
    
    # Close Redis connection
    try:
        if redis_cache:
            redis_cache.close()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")
    
    # Close MySQL connection pool
    try:
        from utils.db_utils import db_pool
        db_pool.close()
        logger.info("MySQL connection pool closed")
    except Exception as e:
        logger.error(f"Error closing MySQL pool: {e}")
    
    logger.info("Graceful shutdown completed")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)


# Global error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.route('/clear_cache', methods=['GET', 'POST'])
def clear_cache():
    """Clear all cached data (for development/debugging)"""
    try:
        # Clear graph data cache
        global redis_cache
        if redis_cache:
            # Delete all graph_data:* keys
            keys = redis_cache.keys('graph_data:*')
            if keys:
                redis_cache.delete(*keys)
                logger.info(f"Cleared {len(keys)} graph cache entries")
            
            # Delete all ill_info:* keys
            keys = redis_cache.keys('ill_info:*')
            if keys:
                redis_cache.delete(*keys)
                logger.info(f"Cleared {len(keys)} disease info cache entries")
            
            return jsonify({'success': True, 'message': '缓存已清除'})
        else:
            # Clear in-memory cache (not applicable for Redis-only cache)
            return jsonify({'success': True, 'message': '没有可用的缓存系统'})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'error': '清除缓存失败'}), 500





if __name__ == '__main__':
    # Validate configuration before starting
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    logger.info(f"Starting Flask application on port {Config.PORT}")
    logger.info(f"Environment: {'Development' if Config.DEBUG else 'Production'}")
    app.run(debug=Config.DEBUG, threaded=True, port=Config.PORT)