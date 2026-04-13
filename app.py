from flask import Flask,request,render_template,jsonify
from neo4j import GraphDatabase,basic_auth
import json
from langchain_qa import get_answer
from user import api_bp
from config import Config
from utils.logger import logger
from utils.validators import validate_question, validate_ill_name
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


app = Flask(__name__,static_folder='./dist',  #设置静态文件夹目录
template_folder = "./dist",static_url_path="")
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Setup rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}" if Config.REDIS_HOST != 'localhost' else None
)

driver = GraphDatabase.driver(Config.NEO4J_URI, auth=basic_auth(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD))
app.register_blueprint(api_bp)


def get_result(ill=''):
    """Get graph data with parameterized queries to prevent injection"""
    try:
        with driver.session() as neo_session:
            if ill:
                # Validate input
                is_valid, error_msg = validate_ill_name(ill)
                if not is_valid:
                    logger.warning(f"Invalid disease name: {error_msg}")
                    return {'graph_data': [], 'links': [], 'labels': [], 'stats': {'node_count': 0, 'link_count': 0, 'category_count': 0}}
                
                # Use parameterized query to prevent injection
                cql = "MATCH (a) WHERE a.name CONTAINS $ill OPTIONAL MATCH (a)-[r]-(b) RETURN a, labels(a) as aa, r, b, labels(b) as bb LIMIT 200"
                result = neo_session.run(cql, ill=ill)
            else:
                cql = "MATCH (a)-[r]->(b) RETURN a, labels(a) as aa, r, b, labels(b) as bb LIMIT 200"
                result = neo_session.run(cql)

            result = json.dumps(result.data(),ensure_ascii=False)
            result2  = json.loads(result)
            graph_data = []
            links = []
            already_list = []
            labels = []
            for item in result2:
                for key in item.keys():
                    if key == 'a':  
                        if item[key]["name"] not in already_list:
                            graph_data.append({
                                "name": item[key]["name"],
                                "symbolSize": 50,
                                "category": item["aa"][0],
                            })
                            already_list.append(item[key]["name"])
                    if key == 'b':
                        if item[key]["name"] not in already_list:
                            graph_data.append({
                                "name": item[key]["name"],
                                "symbolSize": 50,
                                "category": item["bb"][0],
                            })
                            already_list.append(item[key]["name"])
                    if key == 'r':
                        links.append(
                            {
                                "source":item[key][0]["name"],
                                "target":item[key][-1]["name"],
                                "name":item[key][1],
                            }
                        )
                    if (key == 'aa' or key == 'bb') and key not in labels:
                        labels.append({"name":item[key][0]})
            # Calculate real statistics
            node_count = len(graph_data)
            link_count = len(links)
            category_count = len(labels)
            
            results = {
                'graph_data':graph_data,
                'links':links,
                'labels':labels,
                'stats': {
                    'node_count': node_count,
                    'link_count': link_count,
                    'category_count': category_count
                }
            }
            logger.info(f"Graph data retrieved: {node_count} nodes, {link_count} links")
            return results
    except Exception as e:
        logger.error(f"Error in get_result: {e}")
        return {'graph_data': [], 'links': [], 'labels': [], 'stats': {'node_count': 0, 'link_count': 0, 'category_count': 0}}

@app.route('/get_graph',methods=['GET'])
def get_graph():
    ill = request.args.get("ill", "")
    try:
        results = get_result(ill)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in get_graph endpoint: {e}")
        return jsonify({'error': 'Failed to retrieve graph data'}), 500

@app.route('/get_ill_info',methods=['GET'])
def get_ill_info():
    try:
        ill_list = request.args.getlist("ill")
        if not ill_list:
            return jsonify({'error': 'Disease name is required'}), 400
        
        ill = ill_list[0]
        
        # Validate input
        is_valid, error_msg = validate_ill_name(ill)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        with driver.session() as neo_session:
            # First, find all matching diseases using parameterized query
            cql = "match (n:ill) where n.name contains $ill return n.name as ill_name"
            result = neo_session.run(cql, ill=ill)
            result_data = result.data()
            
            all_ills_info = []
            for record in result_data:
                ill_name = record['ill_name']
                
                # For each disease, get all its details from related nodes using parameterized query
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
                details_result = neo_session.run(details_cql, ill_name=ill_name)
                details_data = details_result.data()
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

            result_json = json.dumps(all_ills_info, ensure_ascii=False).replace("nan",'No data available')
            logger.info(f"Retrieved info for disease: {ill}")
            return result_json
    except Exception as e:
        logger.error(f"Error in get_ill_info: {e}")
        return jsonify({'error': 'Failed to retrieve disease information'}), 500


@app.route('/question',methods=['GET'])
@limiter.limit("30 per minute")
def medical_answer():
    try:
        question_list = request.args.getlist("question")
        if not question_list:
            return jsonify({'error': 'Question is required'}), 400
        
        question = question_list[0]
        
        # Validate input
        is_valid, error_msg = validate_question(question)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        logger.info(f"Received question: {question}")
        answer = get_answer(question)
        logger.info("Answer generated successfully")
        return jsonify({'answer': answer})
    except Exception as e:
        logger.error(f"Error in medical_answer: {e}")
        return jsonify({'error': 'Failed to generate answer'}), 500

@app.route('/get_analysis_data', methods=['GET'])
def get_analysis_data():
    try:
        with driver.session() as neo_session:
            # 1. Node count statistics
            node_counts = []
            labels_to_count = ["ill", "symptom", "department", "cure_method"]
            for label in labels_to_count:
                cql = f"MATCH (n:{label}) RETURN count(n) as count"
                result = neo_session.run(cql).single()
                count = result["count"] if result else 0
                if count > 0:
                    chinese_label = {
                        "ill": "疾病", "symptom": "症状", 
                        "department": "科室", "cure_method": "治疗方法"
                    }.get(label, label)
                    node_counts.append({"name": chinese_label, "value": count})

            # 2. Disease count by first-level classification
            class1_ill_counts_cql = """
            MATCH (c1:class1)<-[:belongs_to_class1]-(ill:ill)
            WHERE c1.name IS NOT NULL AND c1.name <> '一级分类'
            RETURN c1.name as name, count(ill) as value
            ORDER BY value DESC
            LIMIT 10
            """
            class1_ill_counts_result = neo_session.run(class1_ill_counts_cql)
            class1_ill_counts = [
                {"name": record["name"], "value": record["value"]}
                for record in class1_ill_counts_result if record["name"]
            ]

            # 3. Infectious disease ratio
            infectious_counts_cql = """
            MATCH (i:if_infect)<-[:is_infectious]-(ill:ill)
            WHERE i.name IS NOT NULL
            RETURN i.name as name, count(ill) as value
            ORDER BY value DESC
            """
            infectious_counts_result = neo_session.run(infectious_counts_cql)
            infectious_counts = [
                {"name": record["name"], "value": record["value"]}
                for record in infectious_counts_result if record["name"]
            ]

            # 4. Healing cycle distribution (Top 10)
            healing_cycle_counts_cql = """
            MATCH (h:healing_cycle)<-[:has_healing_cycle]-(ill:ill)
            WHERE h.name IS NOT NULL AND h.name <> '暂无信息'
            RETURN h.name as name, count(ill) as value
            ORDER BY value DESC
            LIMIT 10
            """
            healing_cycle_counts_result = neo_session.run(healing_cycle_counts_cql)
            healing_cycle_counts = [
                {"name": record["name"], "value": record["value"]}
                for record in healing_cycle_counts_result if record["name"]
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
        logger.error(f"Error in get_analysis_data: {e}")
        return jsonify({
            "node_counts": [],
            "class1_ill_counts": [],
            "infectious_counts": [],
            "healing_cycle_counts": [],
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check Neo4j connection
        neo4j_status = "healthy"
        try:
            with driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            neo4j_status = "unhealthy"
        
        return jsonify({
            'status': 'healthy',
            'services': {
                'neo4j': neo4j_status,
                'flask': 'healthy'
            },
            'timestamp': logger.handlers[0].formatter.formatTime(
                logger.makeRecord('health', 20, '', 0, '', (), None),
                '%Y-%m-%d %H:%M:%S'
            )
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route("/")
def index():
    return render_template('index.html',name='index')    
if __name__ == '__main__':
    logger.info(f"Starting Flask application on port {Config.PORT}")
    app.run(debug=Config.DEBUG, threaded=True, port=Config.PORT)