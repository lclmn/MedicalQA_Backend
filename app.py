from flask import Flask,request,render_template
from neo4j import GraphDatabase,basic_auth
import json
from langchain_qa import get_answer
from user import api_bp


app = Flask(__name__,static_folder='./dist',  #设置静态文件夹目录
template_folder = "./dist",static_url_path="")
driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "password"))
app.register_blueprint(api_bp)


def get_result(ill=''):
    with driver.session() as neo_session:
        
        if ill:
            cql = f"MATCH (a) WHERE a.name CONTAINS '{ill}' OPTIONAL MATCH (a)-[r]-(b) RETURN a, labels(a) as aa, r, b, labels(b) as bb LIMIT 200"
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
                        print(item)
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
                    print()
                    links.append(
                        {
                            "source":item[key][0]["name"],
                            "target":item[key][-1]["name"],
                            "name":item[key][1],
                        }
                    )
                if (key == 'aa' or key == 'bb') and key not in labels:
                    labels.append({"name":item[key][0]})
        # 计算真实的统计数据
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
        print(results)
        return results

@app.route('/get_graph',methods=['GET'])
def get_graph():
    ill = request.args.get("ill", "")
    with driver.session() as neo_session:
        results = get_result(ill)
        print("in getgraph",results)
        return results

@app.route('/get_ill_info',methods=['GET'])
def get_ill_info():
    print(request.args)
    ill = request.args.getlist("ill")[0]
    with driver.session() as neo_session:
        # First, find all matching diseases
        cql = f"match (n:ill) where n.name contains '{ill}' return n.name as ill_name"
        result = neo_session.run(cql)
        result_data = result.data()
        
        all_ills_info = []
        for record in result_data:
            ill_name = record['ill_name']
            
            # For each disease, get all its details from related nodes
            details_cql = f"""
            MATCH (ill:ill {{name: '{ill_name}'}})
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
            details_result = neo_session.run(details_cql)
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
        return result_json


@app.route('/question',methods=['GET'])
def medical_answer():
    print(request.args)
    question = request.args.getlist("question")[0]
    answer = get_answer(question)
    return f"{answer}"

@app.route('/get_analysis_data', methods=['GET'])
def get_analysis_data():
    with driver.session() as neo_session:
        try:
            # 1. 各类节点数量统计
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

            # 2. 一级分类下的疾病数量
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

            # 3. 传染性疾病比例
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

            # 4. 治疗周期分布 (Top 10)
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
            
            return json.dumps(analysis_data, ensure_ascii=False)
            
        except Exception as e:
            print(f"Error in get_analysis_data: {e}")
            return json.dumps({
                "node_counts": [],
                "class1_ill_counts": [],
                "infectious_counts": [],
                "healing_cycle_counts": [],
            }, ensure_ascii=False)


@app.route("/")
def index():
    return render_template('index.html',name='index')    
if __name__ == '__main__':
    app.run(debug=True,threaded=True,port=5001)