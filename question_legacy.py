from import_to_neo4j import neo4jInstance
from sentence_transformers import SentenceTransformer
import jieba
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 初始化BERT模型
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 导入neo4j对象，连接到neo4j
neo4j_instance = neo4jInstance("bolt://localhost:7687", "neo4j", "password")
# neo4j_instance = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
# 答案模板
symptom_ill_answer = "{}的症状可能表明{}"
# 意图判断
all_sentence = {
    "symptom_ill":["这个症状可能是什么病","这个症状是什么病","这个症状可能表示什么疾病","头痛是什么病","发烧可能是什么病","这个症状对应什么疾病"],
    "ill_deparment":["这个疾病应该挂什么科","这个疾病是什么科","这个疾病应该去哪个科","这个疾病应该在什么科治疗","感冒应该看什么科"],
    "ill_symptom":["这个疾病可能有什么症状","这个疾病的症状是什么","��个疾病可能引起什么症状","这个疾病的症状有哪些","感冒的症状有哪些","这个疾病有什么表现","这个疾病的表现是什么"],
    "easy_ill_people":["哪些人容易得这个病","哪些群体容易得这个病","哪些群体常见这个病","谁容易得这个病","哪些群体易感这个病"],
    "cure_method":["如何治疗这个疾病","这个疾病的治疗方法是什么","如何治愈这个疾病","如何治疗这个病","如何治疗这种情况"],
    "cure_cost":["治疗这个疾病要多少钱","这个疾病一般要多少钱","这个疾病的治疗费用是多少","治疗这个疾病要花多少钱","大概的医疗费用是多少"],
    "if_infect":["这个疾病传染吗","这个疾病有传染性吗","这个疾病有传染性吗","这个疾病会传染吗","它有传染性吗"],
    "ill_proportion":["这个疾病的患病率是多少","这个疾病的患病比例是多少","发病率是多少","患病率有多高"],
    "cure_rate":["这个疾病治愈的可能性是多少","这个疾病的治愈率是多少","治愈率是多少","能治愈吗","治愈率高吗"],
    "healing_cycle":["治疗这个疾病需要多长时间","这个疾病多长时间能治愈","治愈这个疾病需要多长时间","治疗需要多长时间","治疗周期是多长","多长时间能恢复"]
}
answer_sentence = {
    "symptom_ill":"{}的症状可能表明{}",
    "ill_symptom":"{}的症状有：{}",
    "easy_ill_people":"{}的易感人群是{}",
    "cure_method":"{}的治疗方法包括{}",
    "cure_cost":"{}的治疗费用一般是{}",
    "if_infect":"{}的传染性是：{}",
    "ill_proportion":"{}的患病率是：{}",
    "cure_rate":"{}的治愈率是{}",
    "healing_cycle":"{}的治疗周期一般是{}",
    "ill_deparment":"{}建议去{}检查"
}

# 猜测问题意图 - 使用BERT计算语义相似度
def questionGuess(question):
    result = {}
    # 获取用户问题的BERT向量
    question_embedding = model.encode([question])
    
    for k, v in all_sentence.items():
        # 计算用户问题与该意图下所有模板句子的相似度
        template_embeddings = model.encode(v)
        similarities = cosine_similarity(question_embedding, template_embeddings)[0]
        # 取平均相似度作为该意图的得分
        result[k] = np.mean(similarities)
    
    print(f"调试 - 意图得分: {result}")
    best_intent = max(result, key=result.get)
    print(f"调试 - 最佳意图: {best_intent} 得分: {result[best_intent]}")
    return best_intent

# 提取疾病实体
def get_ill_name(question):
    ill_name = "找不到该疾病"
    words = list(jieba.cut(question))
    print(f"调试 - jieba分词后: {words}")
    
    command = "match (n:ill) return n.name as name"
    ills= neo4j_instance.execute_command(command)
    # 读取所有疾病名称并添加到分词器
    ills = np.array([i["name"] for i in ills])
    print(f"调试 - 数据库中可用疾病: {ills}")
    
    # 首先尝试使用jieba分词进行精确匹配
    inter = np.intersect1d(words,ills)
    print(f"调试 - 问题词语与疾病的交集: {inter}")

    # 匹配疾病名称并返回
    if len(inter)==1:
        ill_name = inter[0]
    elif len(inter) > 1:
        # 如果有多个匹配项，则查找最长的匹配项
        ill_name = max(inter, key=len)
        print(f"调试 - 找到多个匹配项，选择最长的: {ill_name}")
    
    # 如果没有精确匹配，请尝试在原始问题中进行直接子字符串匹配
    if ill_name == "找不到该疾病":
        question_lower = question.lower()
        best_match = ""
        max_score = 0
        
        for disease in ills:
            disease_lower = disease.lower()
            # 检查疾病名称是否是问题的子字符串
            if disease_lower in question_lower:
                # 基于长度的评分（较长的匹配项更好）
                score = len(disease)
                if score > max_score:
                    max_score = score
                    best_match = disease
                print(f"调试 - 找到子字符串匹配: {disease} 得分 {score}")
            
            # 还要检查疾病名称中的单个单词是否在问题中
            disease_words = disease_lower.split()
            matched_words = sum(1 for word in disease_words if word in question_lower)
            if matched_words > 0:
                # 根据匹配的单词数和总长度进行评分
                word_score = (matched_words / len(disease_words)) * len(disease)
                if word_score > max_score:
                    max_score = word_score
                    best_match = disease
                print(f"调试 - 找到基于单词的匹配: {disease} with {matched_words}/{len(disease_words)} words, score {word_score}")
        
        if best_match:
            ill_name = best_match
            print(f"调试 - 选择的最佳匹配: {ill_name} 得分 {max_score}")
        
    # 后备：尝试与单个单词进行模糊匹配
    if ill_name == "找不到该疾病":
        from difflib import SequenceMatcher
        best_similarity = 0
        best_match = ""
        
        for disease in ills:
            # 计算问题与疾病名称之间的相似度
            similarity = SequenceMatcher(None, question.lower(), disease.lower()).ratio()
            if similarity > best_similarity and similarity > 0.3:  # 阈值
                best_similarity = similarity
                best_match = disease
                print(f"调试 - 模糊匹配: {disease} 相似度 {similarity}")
        
        if best_match:
            ill_name = best_match
            print(f"调试 - 最佳模糊匹配: {ill_name} 相似度 {best_similarity}")
        
    print(f"调试 - 最终提取的疾病名称: {ill_name}")
    return ill_name


# 根据意图生成用于查询的cypher语句
def searchGraph(ill_name,intention):
    print(f"调试 - 在图中搜索疾病: {ill_name}, 意图: {intention}")
    answer = "未找到与您的问题相关的信息。请联系当地医院进行咨询。"
    
    if intention == 'ill_symptom':
        command = f'match (n:ill)-[r:has_symptom]->(s:symptom) where n.name="{ill_name}" return s.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        # 获取答案模板
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的症状。"
        
    elif intention  == "ill_deparment":
        command = f'match (n:ill)-[r:should_see]->(d:department) where n.name="{ill_name}" return d.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        # 获取答案模板
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的科室信息。"
    
    elif intention  == "symptom_ill":
        command = f'match (n:ill)-[r:has_symptom]->(s:symptom) where s.name="{ill_name}" return n.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        # 获取答案模板
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到症状{ill_name}对应的疾病。"
    
    elif intention == "easy_ill_people":
        command = f'match (n:ill)-[r:affects_people]->(p:easy_ill_people) where n.name="{ill_name}" return p.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的易感人群信息。"
    
    elif intention == "cure_method":
        command = f'match (n:ill)-[r:treated_by]->(m:cure_method) where n.name="{ill_name}" return m.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的治疗方法信息。"
    
    elif intention == "cure_cost":
        command = f'match (n:ill)-[r:costs]->(c:cure_cost) where n.name="{ill_name}" return c.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的治疗费用信息。"
    
    elif intention == "if_infect":
        command = f'match (n:ill)-[r:is_infectious]->(i:if_infect) where n.name="{ill_name}" return i.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的传染性信息。"
    
    elif intention == "ill_proportion":
        command = f'match (n:ill)-[r:has_proportion]->(p:ill_proportion) where n.name="{ill_name}" return p.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的患病比例信息。"
    
    elif intention == "cure_rate":
        command = f'match (n:ill)-[r:has_cure_rate]->(c:cure_rate) where n.name="{ill_name}" return c.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的治愈率信息。"
    
    elif intention == "healing_cycle":
        command = f'match (n:ill)-[r:has_healing_cycle]->(h:healing_cycle) where n.name="{ill_name}" return h.name as name'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["name"] for i in results])
        if len(result) > 0:
            answer = answer_sentence[intention].format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的治疗周期信息。"
    
    else:
        # 如果是其他意图，尝试通过节点属性查询（向后兼容）
        command = f'match (n:ill) where n.name="{ill_name}" return n.{intention} as intention'
        print(f"调试 - 执行查询: {command}")
        results = neo4j_instance.execute_command(command)
        print(f"调试 - 查询结果: {results}")
        result = np.array([i["intention"] for i in results if i["intention"] is not None])
        # 获取答案模板
        if len(result) > 0:
            answer = answer_sentence.get(intention, f"{ill_name}的{intention}信息是：{{}}").format(ill_name,", ".join(result))
        else:
            answer = f"数据库中未找到{ill_name}的{intention}信息。"
    
    print(f"调试 - 最终答案: {answer}")
    return answer

def multi_symptom_get_ill(symptoms,intention):
    command = f'match'
    for index,symptom in enumerate(symptoms):
        command += f'(n:ill)-[:has_symptom]->(s{str(index+1)}:symptom{{name:"{symptom}"}}) ,'
    command = command[:-1]
    command += "return n.name as name"
    print(f"调试 - 多症状命令: {command}")
    results = neo4j_instance.execute_command(command)
    print(f"调试 - 多症状结果: {results}")
    result = np.array([i["name"] for i in results])
    # # 获取答案模板
    answer = answer_sentence[intention].format(",".join(symptoms),",".join(result))

    return answer

def get_symptom_name(question):
    symptom_name = "找不到该症状"
    words = list(jieba.cut(question))
    command = "match (n:symptom) return n.name as name"
    symptoms= neo4j_instance.execute_command(command)

    # 读取所有名称
    symptoms = np.array([i["name"] for i in symptoms])
    inter = np.intersect1d(words,symptoms)
    print(f"调试 - 在问题中找到的症状: {inter}")
    
    return inter

def generate_user_dict():
    command = "match (n:ill) return n.name as name"
    ills= neo4j_instance.execute_command(command)
    # 读取所有疾病名称并添加到分词器
    ills = np.array([i["name"] for i in ills])
    for ill in ills:     
        # 添加完整的疾病名称，频率要高，以确保jieba能够识别
        jieba.add_word(ill, freq=10000, tag='disease')
        # 同时添加单个有意义的词
        words = ill.split()
        for word in words:
            if len(word) > 2:  # 只添加长度超过2的单词
                jieba.add_word(word, freq=1000)
    
    command = "match (n:symptom) return n.name as name"
    symptoms= neo4j_instance.execute_command(command)

    # 读取所有名称
    symptoms = np.array([i["name"] for i in symptoms])
    for symptom in symptoms:     
        # 添加完整的症状，频率要高
        jieba.add_word(symptom, freq=5000, tag='symptom')
        # 同时添加症状中单个有意义的词
        words = symptom.split()
        for word in words:
            if len(word) > 2:
                jieba.add_word(word, freq=500)
    
    print(f"调试 - 已将{len(ills)}个疾病和{len(symptoms)}个症状添加到jieba词典，频率较高")
    
    # 强制jieba重建其内部结构
    jieba.initialize()

# 主函数
def medical_get_answer(question):
    print(f"调试 - 收到问题: {question}")
    
    # 构建自定义词典
    generate_user_dict()
    intention  = questionGuess(question)
    
    if intention == "symptom_ill":
        symptom_name = get_symptom_name(question)
        if len(symptom_name)>1:
            answer = multi_symptom_get_ill(symptom_name,intention)
        elif len(symptom_name)==0:
            answer = "未找到相关症状。请咨询专业人士进行诊断。"
        else:
            answer = searchGraph(symptom_name[0],intention)
    else:
        ill_name = get_ill_name(question)
        if ill_name == "找不到该疾病":
            answer = "未找到相关疾病。请咨询专业人士进行诊断"
        else:
            answer = searchGraph(ill_name,intention)
    
    print(f"调试 - 返回最终答案: {answer}")
    return answer


if __name__ == "__main__":
    question = input("请输入您的问题: >")
    answer = medical_get_answer(question)
    print(answer)
