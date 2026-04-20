from neo4j import GraphDatabase
import pandas as pd
from tqdm import tqdm
# 构建连接neo4j的实例对象
# class neo4jInstance:

    # # 设置初始化，接受neo4j服务器地址，用户名，密码
    # def __init__(self, uri, user, password):
    #     # 构建驱动
    #     self.driver = GraphDatabase.driver(uri, auth=(user, password))

    # # 关闭驱动
    # def close(self):
    #     self.driver.close()
    # # 执行指令
    # def execute_command(self,command):
    #     # 通过驱动建立会话
    #     with self.driver.session() as session:
    #         # 执行指令
    #         result = session.execute_write(self.execute,command)
    #         return result
            
    # # 执行指令
    # @staticmethod
    # def execute(tx,command):
    #     result = tx.run(command)
    #     return [i for i in result]
        
from py2neo import Graph, Node, Relationship
from py2neo.errors import ClientError

class neo4jInstance:
    # 设置初始化，接受neo4j服务器地址，用户名，密码
    def __init__(self, uri, user, password):
        # 连接neo4j实例
        self.graph = Graph(uri, auth=(user, password))
    
    # 关闭实例
    def close(self):
        self.graph.close()
    
    # 执行指令
    def execute_command(self, command):
        # 执行指令并返回结果
        result = self.graph.run(command).data()
        return result



if __name__ == "__main__":
    # 连接neo4j
    neo4j_instance = neo4jInstance("bolt://localhost:7687", "neo4j", "password")
    # 读取数据
    df = pd.read_csv('data.csv',encoding='utf-8')
    # 删除所有节点
    delete_command = "match (r) detach delete r"
    neo4j_instance.execute_command(delete_command)
    print("清空数据库")
    
    # 删除并重新创建索引
    indexes_to_create = [
        ("ill", "name"),
        ("symptom", "name"),
        ("department", "name"),
        ("class1", "name"),
        ("class2", "name"),
        ("easy_ill_people", "name"),
        ("cure_method", "name"),
        ("cure_cost", "name"),
        ("if_infect", "name"),
        ("ill_proportion", "name"),
        ("cure_rate", "name"),
        ("healing_cycle", "name")
    ]
    
    # 先查询并删除所有现有索引
    print("查询现有索引...")
    try:
        show_indexes_command = "SHOW INDEXES"
        existing_indexes = neo4j_instance.execute_command(show_indexes_command)
        
        for index in existing_indexes:
            try:
                index_name = index.get('name', '')
                if index_name:
                    drop_command = f"DROP INDEX {index_name}"
                    neo4j_instance.execute_command(drop_command)
                    print(f"已删除索引: {index_name}")
            except Exception as e:
                print(f"删除索引时出错: {e}")
                
    except Exception as e:
        print(f"查询索引时出错，尝试使用旧方法: {e}")
        # 如果SHOW INDEXES不工作，使用旧方法
        for label, property_name in indexes_to_create:
            try:
                drop_index_command = f"DROP INDEX ON :{label}({property_name})"
                neo4j_instance.execute_command(drop_index_command)
                print(f"已删除旧的{label}节点索引。")
            except ClientError:
                print(f"{label}节点索引不存在或已删除。")
    
    # 创建新索引
    print("创建新索引...")
    for label, property_name in indexes_to_create:
        try:
            create_index_command = f"CREATE INDEX FOR (n:{label}) ON (n.{property_name})"
            neo4j_instance.execute_command(create_index_command)
            print(f"已创建{label}节点索引。")
        except Exception as e:
            print(f"创建{label}索引时出错: {e}")
    
    # 循环数据插入neo4j
    for _,row in tqdm(df.iterrows(), total=df.shape[0], desc="正在导入数据到neo4j"):
        ill = str(row['疾病'])
        
        # 创建疾病节点
        ill_name = f'{{name:"{ill}"}}'
        command = f'merge (a:ill {ill_name})'
        neo4j_instance.execute_command(command)
        
        # 处理症状关系
        for symptom in row['哪些症状'].split("、"):
            if symptom.strip():  # 确保症状不为空
                symptom_name = f'{{name:"{symptom}"}}'
                command = f'merge (a:ill {ill_name}) merge (b:symptom {symptom_name}) merge (a)-[r:has_symptom]->(b)'
                neo4j_instance.execute_command(command)
        
        # 处理科室关系
        for department in row['挂什么科'].split("、"):
            if department.strip():  # 确保科室不为空
                department_name = f'{{name:"{department}"}}'
                command = f'merge (a:ill {ill_name}) merge (b:department {department_name}) merge (a)-[r:should_see]->(b)'
                neo4j_instance.execute_command(command)
        
        # 处理一级分类
        class1 = str(row['一级分类'])
        if class1 and class1 != 'nan':
            class1_name = f'{{name:"{class1}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:class1 {class1_name}) merge (a)-[r:belongs_to_class1]->(b)'
            neo4j_instance.execute_command(command)
        
        # 处理二级分类
        class2 = str(row['二级分类'])
        if class2 and class2 != 'nan':
            class2_name = f'{{name:"{class2}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:class2 {class2_name}) merge (a)-[r:belongs_to_class2]->(b)'
            neo4j_instance.execute_command(command)

        # 处理好发人群
        easy_ill_people = str(row['好发人群'])
        if easy_ill_people and easy_ill_people != 'nan':
            people_name = f'{{name:"{easy_ill_people}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:easy_ill_people {people_name}) merge (a)-[r:affects_people]->(b)'
            neo4j_instance.execute_command(command)

        # 处理治疗方法
        cure_method = str(row['治疗方法'])
        if cure_method and cure_method != 'nan':
            method_name = f'{{name:"{cure_method}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:cure_method {method_name}) merge (a)-[r:treated_by]->(b)'
            neo4j_instance.execute_command(command)

        # 处理治疗费用
        cure_cost = str(row['治疗费用'])
        if cure_cost and cure_cost != 'nan':
            cost_name = f'{{name:"{cure_cost}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:cure_cost {cost_name}) merge (a)-[r:costs]->(b)'
            neo4j_instance.execute_command(command)

        # 处理是否传染
        if_infect = str(row['是否传染'])
        if if_infect and if_infect != 'nan':
            infect_name = f'{{name:"{if_infect}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:if_infect {infect_name}) merge (a)-[r:is_infectious]->(b)'
            neo4j_instance.execute_command(command)

        # 处理患病比例
        ill_proportion = str(row['患病比例'])
        if ill_proportion and ill_proportion != 'nan':
            proportion_name = f'{{name:"{ill_proportion}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:ill_proportion {proportion_name}) merge (a)-[r:has_proportion]->(b)'
            neo4j_instance.execute_command(command)

        # 处理治愈率
        cure_rate = str(row['治愈率'])
        if cure_rate and cure_rate != 'nan':
            rate_name = f'{{name:"{cure_rate}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:cure_rate {rate_name}) merge (a)-[r:has_cure_rate]->(b)'
            neo4j_instance.execute_command(command)

        # 处理治疗周期
        healing_cycle = str(row['治疗周期'])
        if healing_cycle and healing_cycle != 'nan':
            cycle_name = f'{{name:"{healing_cycle}"}}'
            command = f'merge (a:ill {ill_name}) merge (b:healing_cycle {cycle_name}) merge (a)-[r:has_healing_cycle]->(b)'
            neo4j_instance.execute_command(command)

        # 保留html链接作为疾病节点的属性
        source_link = str(row['html'])
        if source_link and source_link != 'nan':
            command = f"match (n:ill) where n.name='{ill}' set n.source_link = '{source_link}'"
            neo4j_instance.execute_command(command)
    
    print("数据导入完成！新的schema采用独立节点结构。")
    