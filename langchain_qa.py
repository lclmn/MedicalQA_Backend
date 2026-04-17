import os
import json
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from config import Config
from utils.logger import logger
import hashlib
import time
import redis
import pickle

# Configuration from environment variables
NEO4J_URI = Config.NEO4J_URI
NEO4J_USERNAME = Config.NEO4J_USERNAME
NEO4J_PASSWORD = Config.NEO4J_PASSWORD

DEEPSEEK_API_KEY = Config.DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL = Config.DEEPSEEK_BASE_URL

MANUAL_SCHEMA = """
Node properties:
- **ill**: name, source_link
- **symptom**: name
- **department**: name
- **class1**: name
- **class2**: name
- **easy_ill_people**: name
- **cure_method**: name
- **cure_cost**: name
- **if_infect**: name
- **ill_proportion**: name
- **cure_rate**: name
- **healing_cycle**: name

Relationships:
- (:ill)-[:has_symptom]->(:symptom)
- (:ill)-[:should_see]->(:department)
- (:ill)-[:belongs_to_class1]->(:class1)
- (:ill)-[:belongs_to_class2]->(:class2)
- (:ill)-[:affects_people]->(:easy_ill_people)
- (:ill)-[:treated_by]->(:cure_method)
- (:ill)-[:costs]->(:cure_cost)
- (:ill)-[:is_infectious]->(:if_infect)
- (:ill)-[:has_proportion]->(:ill_proportion)
- (:ill)-[:has_cure_rate]->(:cure_rate)
- (:ill)-[:has_healing_cycle]->(:healing_cycle)
"""

class FixedNeo4jGraph(Neo4jGraph):
    """Subclass to force manual schema return."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @property
    def schema(self) -> str:
        return MANUAL_SCHEMA
    
    @schema.setter
    def schema(self, value):
        pass
    
    @property
    def structured_schema(self):
        return {}

    @structured_schema.setter
    def structured_schema(self, value):
        pass

    @property
    def get_structured_schema(self):
        return {}

class MedicalQAChain:
    def __init__(self):
        # Use FixedNeo4jGraph
        self.graph = FixedNeo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            refresh_schema=False
        )
        
        # Initialize DeepSeek LLM with optimized configuration
        self.llm = ChatOpenAI(
            model=Config.DEEPSEEK_MODEL or "deepseek-chat",
            openai_api_key=DEEPSEEK_API_KEY,
            openai_api_base=DEEPSEEK_BASE_URL,
            temperature=0.1,  # Slightly higher for more natural responses
            max_tokens=1024,  # Limit response length
            request_timeout=30,  # Add timeout
            max_retries=3  # Retry failed requests
        )
        
        # Hybrid cache: Redis (if available) + in-memory fallback
        self._cache = {}
        self._cache_ttl = 3600  # Cache TTL: 1 hour
        
        # Initialize Redis cache if available
        self._redis_cache = None
        try:
            if Config.REDIS_HOST:
                redis_params = {
                    'host': Config.REDIS_HOST,
                    'port': Config.REDIS_PORT,
                    'db': Config.REDIS_DB + 1,  # Use separate DB for QA cache
                    'decode_responses': False,
                    'socket_connect_timeout': 5
                }
                
                # Add password if configured
                if Config.REDIS_PASSWORD:
                    redis_params['password'] = Config.REDIS_PASSWORD
                
                self._redis_cache = redis.Redis(**redis_params)
                self._redis_cache.ping()
                logger.info("Redis cache initialized for QA chain")
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}. Using in-memory cache only.")

        # Cypher Generation Prompt with few-shot examples
        self.cypher_generation_template = """Task: Generate Cypher statement to query a graph database.
Instructions:
1. Use ONLY the relationship types and properties provided in the schema below.
2. Do NOT hallucinate new relationships (e.g., do not use 'HAS_SYMPTOM' if 'has_symptom' is defined).
3. The label for a disease is always 'ill'.
4. Do not limit the return value too strictly if a list is expected.

Schema:
{schema}

Examples:
Question: 百日咳的治疗周期是多长？
Cypher: MATCH (i:ill {{name: '百日咳'}})-[:has_healing_cycle]->(h:healing_cycle) RETURN h.name

Question: 感冒的症状是什么？
Cypher: MATCH (i:ill {{name: '感冒'}})-[:has_symptom]->(s:symptom) RETURN s.name

Question: 哪些病属于内科？
Cypher: MATCH (i:ill)-[:should_see]->(d:department {{name: '内科'}}) RETURN i.name

Question: 肺炎怎么治疗？
Cypher: MATCH (i:ill {{name: '肺炎'}})-[:treated_by]->(m:cure_method) RETURN m.name

Question: 治疗糖尿病要花多少钱？
Cypher: MATCH (i:ill {{name: '糖尿病'}})-[:costs]->(c:cure_cost) RETURN c.name

Question: 肺结核是否具有传染性？
Cypher: MATCH (i:ill {{name: '肺结核'}})-[:is_infectious]->(inf:if_infect) RETURN inf.name

Question: 流感的治愈率是多少？
Cypher: MATCH (i:ill {{name: '流感'}})-[:has_cure_rate]->(r:cure_rate) RETURN r.name

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}"""
        
        self.cypher_prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=self.cypher_generation_template
        )

        # QA Prompt
        self.qa_template = """You are an helpful and professional medical assistant.
The information part contains key facts retrieved from a knowledge graph.
Your task is to answer the user's question using this information.

Instructions:
1. **NO Markdown**: Do not use any markdown syntax (no **bold**, *italics*, - lists, # headers, etc.). Use plain text only.
2. **Elaborate**: Do not just list the data. Use the provided information as a foundation, but expand on it using your general medical knowledge to provide a comprehensive, warm, and helpful response.
3. **Accuracy**: While expanding, do not contradict the provided information.
4. **Fallback**: If the provided information is empty, say that you don't know the specific answer from the database, but offer general advice if possible (or trigger the fallback mechanism).

Information:
{context}

Question: {question}
Helpful Answer:"""
        
        self.qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=self.qa_template
        )

        # Initialize GraphCypherQAChain
        self.chain = GraphCypherQAChain.from_llm(
            self.llm,
            graph=self.graph,
            verbose=True,
            cypher_prompt=self.cypher_prompt,
            qa_prompt=self.qa_prompt,
            allow_dangerous_requests=True,
            validate_cypher=False # Disable validation to avoid APOC issues
        )

    def _get_cache_key(self, question: str) -> str:
        """Generate cache key from question"""
        return f"qa:{hashlib.md5(question.encode('utf-8')).hexdigest()}"
    
    def _get_from_cache(self, question: str) -> dict:
        """Get answer from cache if exists and not expired (Redis + memory)"""
        cache_key = self._get_cache_key(question)
        
        # Try Redis first
        if self._redis_cache:
            try:
                cached_data = self._redis_cache.get(cache_key)
                if cached_data:
                    result = pickle.loads(cached_data)
                    logger.info(f"Redis cache hit for question: {question[:50]}...")
                    return result
            except Exception as e:
                logger.warning(f"Redis cache get error: {e}")
        
        # Fallback to in-memory cache
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data['timestamp'] < self._cache_ttl:
                logger.info(f"Memory cache hit for question: {question[:50]}...")
                return cached_data['data']
            else:
                # Remove expired cache
                del self._cache[cache_key]
        
        return None
    
    def _save_to_cache(self, question: str, answer_data: dict):
        """Save answer to cache (Redis + memory)"""
        cache_key = self._get_cache_key(question)
        
        # Save to Redis
        if self._redis_cache:
            try:
                self._redis_cache.setex(
                    cache_key,
                    self._cache_ttl,
                    pickle.dumps(answer_data)
                )
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
        
        # Also save to in-memory cache as fallback
        self._cache[cache_key] = {
            'data': answer_data,
            'timestamp': time.time()
        }
    
    def get_answer(self, question: str) -> dict:
        """
        Get answer from Neo4j KG. If no answer found, fallback to LLM general knowledge.
        Returns dict with answer and metadata
        """
        try:
            logger.info(f"Processing question: {question}")
            
            # Check cache first
            cached_answer = self._get_from_cache(question)
            if cached_answer:
                return cached_answer
            
            # Try to get answer from KG with retry logic
            max_retries = 2
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    response = self.chain.invoke({"query": question})
                    
                    if isinstance(response, dict):
                        result = response.get("result", "").strip()
                        cypher_query = response.get("intermediate_steps", [{}])[0].get("query", "") if response.get("intermediate_steps") else ""
                    else:
                        result = str(response).strip()
                        cypher_query = ""

                    # Check for "I don't know" or similar failure responses
                    fallback_triggers = [
                        "don't know", "no information", 
                        "不清楚", "不知道", "无法提供", "没有相关信息", "没有足够的信息"
                    ]
                    
                    should_fallback = not result or any(trigger in result.lower() for trigger in fallback_triggers)

                    if should_fallback:
                        logger.info(f"KG failed to answer. Fallback to General Knowledge for: {question}")
                        fallback_answer = self.fallback_to_general_knowledge(question)
                        result_data = {
                            'answer': fallback_answer,
                            'source': 'llm_fallback',
                            'confidence': 'medium'
                        }
                    else:
                        logger.info(f"Successfully answered from KG (attempt {attempt + 1})")
                        result_data = {
                            'answer': result,
                            'source': 'knowledge_graph',
                            'confidence': 'high',
                            'cypher_query': cypher_query
                        }
                    
                    # Cache the result
                    self._save_to_cache(question, result_data)
                    return result_data
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Wait before retry
                    continue
            
            # All retries failed, use fallback
            logger.error(f"All KG attempts failed. Last error: {last_error}. Using LLM fallback.")
            fallback_answer = self.fallback_to_general_knowledge(question)
            result_data = {
                'answer': fallback_answer,
                'source': 'llm_error_fallback',
                'confidence': 'low'
            }
            self._save_to_cache(question, result_data)
            return result_data
            
        except Exception as e:
            logger.error(f"Unexpected error in get_answer: {e}", exc_info=True)
            # Final fallback
            fallback_answer = self.fallback_to_general_knowledge(question)
            return {
                'answer': fallback_answer,
                'source': 'llm_error_fallback',
                'confidence': 'low'
            }

    def fallback_to_general_knowledge(self, question: str) -> str:
        """
        Fallback to use the LLM directly for general medical knowledge.
        """
        try:
            logger.info(f"Using LLM fallback for question: {question}")
            messages = [
                ("system", "You are a helpful medical assistant. The user asked a question that could not be answered by the local database. Please use your general medical knowledge to answer the question professionally and responsibly. If it involves serious medical conditions, advise visiting a doctor."),
                ("human", question),
            ]
            response = self.llm.invoke(messages)
            logger.info("LLM fallback answer generated successfully")
            return response.content
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return "抱歉，我无法回答这个问题。建议您咨询专业医生。"

# Singleton instance for easy import
qa_chain = MedicalQAChain()

def get_answer(question):
    """
    Get answer from QA chain
    Returns dict with answer and metadata for backward compatibility
    """
    result = qa_chain.get_answer(question)
    # For backward compatibility, if caller expects just string
    if isinstance(result, dict):
        return result
    return {'answer': result, 'source': 'unknown', 'confidence': 'unknown'}

def get_search_suggestions(keyword: str, limit: int = 10) -> list:
    """
    Get disease name suggestions based on keyword
    Used for autocomplete/search suggestions
    """
    try:
        from utils.neo4j_utils import execute_cypher_query
        
        # Search for diseases matching the keyword with parameterized query
        query = """
        MATCH (i:ill)
        WHERE i.name CONTAINS $keyword
        RETURN i.name as name
        ORDER BY size(i.name)
        LIMIT $limit
        """
        result = execute_cypher_query(query, {'keyword': keyword, 'limit': limit}, read_only=True)
        suggestions = [record['name'] for record in result if record.get('name')]
        
        logger.info(f"Found {len(suggestions)} suggestions for keyword: {keyword}")
        return suggestions
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}", exc_info=True)
        return []
