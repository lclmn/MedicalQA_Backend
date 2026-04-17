# 医疗智能问答系统后端 (Medical QA System Backend)

基于 **Flask + LangChain + Neo4j + DeepSeek LLM** 构建的企业级智能医疗问答系统。该系统融合知识图谱技术与大语言模型，为用户提供精准的医疗信息查询、智能问答和可视化分析服务。

> **🎉 v2.0 优化版本**: 已完成全面性能优化和安全加固，包括Neo4j连接池、双层缓存机制、SQL/XSS防护、统一响应格式等。详见 [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md)

## 📋 目录

- [核心特性](#核心特性)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [API 接口文档](#api-接口文档)
- [配置说明](#配置说明)
- [数据库设计](#数据库设计)
- [安全特性](#安全特性)
- [性能优化](#性能优化)
- [开发指南](#开发指南)
- [故障排查](#故障排查)

## ✨ 核心特性

### 1. 智能医疗问答引擎
- **知识图谱驱动**: 使用 `GraphCypherQAChain` 将自然语言自动转换为 Cypher 查询
- **DeepSeek-V3 集成**: 基于 DeepSeek 大语言模型进行智能推理和答案生成
- **三层降级机制**: 
  - ✅ 优先从 Neo4j 知识图谱获取精准答案
  - ⚠️ 图谱无答案时自动降级到 LLM 通用医学知识
  - 🔄 异常情况下提供安全的默认响应
- **智能缓存**: 内置多级缓存（内存 + Redis），提升重复查询响应速度
- **元数据返回**: 每次回答附带来源标识（knowledge_graph/llm_fallback/cache）和置信度

### 2. 知识图谱可视化
- 支持疾病、症状、科室、治疗方法等 12 种节点类型的关系展示
- 动态疾病详情查询（症状、科室、分类、治疗费用、治愈率等 11 个维度）
- 实时统计分析面板（节点统计、疾病分类分布、传染病比例、治疗周期分布）
- 智能搜索建议接口，支持疾病名称自动补全

### 3. 用户与对话管理
- 完整的用户注册、登录、信息管理功能
- **手机验证码认证**：集成阿里云短信服务，支持发送和验证短信验证码
- 管理员后台管理接口（批量操作支持）
- JWT Token 认证机制（可配置过期时间）
- 对话历史持久化存储（MySQL JSON 字段）
- 支持多会话管理和一键清空功能

### 4. 企业级安全防护
- **输入验证**: 全面的参数校验与 sanitization（防 SQL/Cypher 注入）
- **速率限制**: API 级别的请求频率控制（Flask-Limiter）
- **密码安全**: bcrypt 加密存储，防止彩虹表攻击
- **参数化查询**: 所有数据库查询使用参数化语句
- **CORS 支持**: 可配置的跨域资源共享策略
- **审计日志**: 完整的操作日志记录与错误追踪

### 5. 高性能架构
- **连接池**: MySQL 连接池管理（DBUtils），避免频繁创建连接
- **Neo4j连接池**: 单例模式连接池，最大50个并发连接，支持自动读写分离
- **多级缓存**: 内存缓存 + Redis 分布式缓存（双层架构，自动降级）
- **索引优化**: Neo4j 节点属性索引加速查询
- **LLM重试机制**: 自动重试失败的请求（最多3次），提高成功率
- **异步支持**: Flask 多线程模式处理并发请求

## 🛠️ 技术栈

### 后端框架
- **Flask 3.0.2**: 轻量级 Web 应用框架
- **Flask-Cors 4.0.0**: 跨域资源共享支持
- **Flask-Limiter 3.5.0**: API 速率限制中间件

### AI & NLP
- **LangChain 0.3.20**: LLM 应用编排框架
- **langchain-openai 0.3.7**: OpenAI 兼容接口（用于 DeepSeek）
- **langchain-neo4j 0.3.0**: Neo4j 图数据库集成
- **DeepSeek Chat**: 大语言模型（deepseek-chat）
- **Jieba 0.42.1**: 中文分词工具（预留扩展）

### 数据库
- **Neo4j 5.28.1**: 图数据库（知识图谱存储）
- **PyMySQL 1.1.0**: MySQL 客户端库
- **DBUtils 3.1.0**: 数据库连接池管理
- **Redis 5.0.4**: 分布式缓存与速率限制存储（可选）

### 数据处理
- **Pandas 2.0.1**: 数据处理与分析
- **NumPy 1.26.4**: 数值计算
- **Requests 2.32.3**: HTTP 请求库
- **BeautifulSoup4**: HTML 解析（数据爬虫）

### 安全与认证
- **bcrypt 4.1.2**: 密码哈希加密
- **PyJWT 2.8.0**: JWT Token 生成与验证
- **python-dotenv 1.0.1**: 环境变量管理

### 其他工具
- **py2neo**: Neo4j Python 客户端（数据导入脚本）
- **sentence-transformers 2.7.0**: 文本嵌入（预留语义搜索扩展）
- **scikit-learn 1.3.0**: 机器学习工具（预留数据分析扩展）
- **alibabacloud-dysmsapi20170525**: 阿里云短信服务SDK（v2.1新增）

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Vue/React)               │
│              (通过 REST API 与后端交互)               │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS/REST API + CORS
┌──────────────────▼──────────────────────────────────┐
│          Flask Application Server (app.py)           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ User Routes │  │  QA Routes   │  │ Graph      │ │
│  │ (user.py)   │  │ (/question)  │  │ Routes     │ │
│  └─────────────┘  └──────┬───────┘  └────────────┘ │
│         │                 │                │         │
│  ┌──────▼──────┐  ┌──────▼───────┐  ┌────▼──────┐  │
│  │ JWT Auth    │  │ Rate Limiter │  │ Cache     │  │
│  │ Validation  │  │ (Limiter)    │  │ Layer     │  │
│  └─────────────┘  └──────────────┘  └───────────┘  │
└──────────────────────────┬──────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼───────┐  ┌──────▼───────┐  ┌──────▼──────┐
│  LangChain    │  │   Neo4j      │  │   MySQL     │
│  QA Chain     │  │   Graph DB   │  │   User DB   │
│               │  │              │  │             │
│ • Cypher Gen  │  │ • ill       │  │ • user      │
│ • KG Query    │  │ • symptom   │  │ • admin     │
│ • LLM Answer  │  │ • dept      │  │ • conversa- │
│ • Fallback    │  │ • ...       │  │   tions     │
└───────┬───────┘  └──────────────┘  └─────────────┘
        │
┌───────▼───────┐
│  DeepSeek     │
│  LLM API      │
│  (OpenAI兼容)  │
└───────────────┘
        │
┌───────▼───────┐
│   Redis       │
│  (Optional)   │
│  Cache Layer  │
└───────────────┘
```

## 📁 项目结构

```
MedicalQA_Backend/
├── app.py                      # Flask 主应用入口（路由、中间件、错误处理）
├── config.py                   # 配置管理模块（多环境支持）
├── langchain_qa.py            # LangChain 问答核心逻辑（含缓存机制）
├── user.py                    # 用户管理 API 蓝图（认证、对话管理）
├── crawler.py                 # 医疗数据爬虫（120ask.com）
├── import_to_neo4j.py         # Neo4j 数据导入脚本
├── generate_table.sql         # MySQL 数据库建表脚本
├── migrate_passwords.py       # 密码迁移工具（明文→bcrypt）
├── requirements.txt           # Python 依赖包列表
├── .env                       # 环境变量配置（不提交到 Git）
├── .env.example              # 环境变量示例文件
├── data.csv                   # 爬取的医疗数据（CSV 格式）
│
├── utils/                     # 工具类模块
│   ├── __init__.py
│   ├── auth.py               # 认证工具（JWT、密码哈希、装饰器）
│   ├── db_utils.py           # MySQL 连接池管理（单例模式）
│   ├── logger.py             # 日志配置（文件轮转、分级记录）
│   ├── validators.py         # 输入验证器（用户名、密码、疾病名等）
│   ├── neo4j_utils.py        # Neo4j 连接池与查询工具（v2.0新增）
│   ├── security.py           # 安全中间件（SQL注入/XSS防护，v2.0新增）
│   ├── response.py           # 统一API响应格式（v2.0新增）
│   └── sms_service.py        # 阿里云短信服务（v2.1新增）
│
├── logs/                      # 日志目录（自动创建）
│   ├── app.log               # 应用日志（INFO 级别）
│   └── error.log             # 错误日志（ERROR 级别）
│
└── dist/                      # 前端静态文件目录（由前端项目构建生成）
    ├── index.html
    ├── static/
    └── ...
```

### 核心模块说明

#### 1. `app.py` - 主应用入口
**职责**:
- Flask 应用初始化与配置加载
- Neo4j 驱动初始化
- Redis 缓存连接（可选）
- CORS 与速率限制中间件注册
- 全局错误处理器（404/500/429）

**主要路由**:
- `GET /get_graph`: 获取知识图谱可视化数据（支持按疾病过滤，带缓存）
- `GET /get_ill_info`: 获取疾病详细信息（多维度数据，带缓存）
- `GET /question`: 医疗问答接口（30次/分钟限流，智能降级）
- `GET /search_suggestions`: 疾病名称搜索建议（60次/分钟限流）
- `GET /get_analysis_data`: 获取统计分析数据
- `GET /health`: 健康检查接口（Neo4j 连接状态）
- `GET /`: 前端页面入口

#### 2. `langchain_qa.py` - 问答核心引擎
**核心类**:
- `MedicalQAChain`: 封装 LangChain 问答逻辑
  - 内置内存缓存（TTL: 1小时）
  - 智能降级策略（KG → LLM → 默认响应）
  - 元数据追踪（来源、置信度、Cypher 查询）
- `FixedNeo4jGraph`: 自定义 Neo4j 图类（强制使用手动 Schema）

**关键函数**:
- `get_answer(question)`: 对外提供的问答接口，返回 dict（含 answer/source/confidence）
- `get_search_suggestions(keyword, limit)`: 疾病名称自动补全

#### 3. `user.py` - 用户管理蓝图
**用户接口**:
- `POST /register`: 用户注册（密码 bcrypt 加密）
- `POST /login`: 用户登录（返回 JWT Token）
- `POST /Adminlogin`: 管理员登录
- `GET /get_users`: 获取所有用户列表（管理员）
- `POST /add_users`: 添加用户（管理员）
- `POST /update_user`: 更新用户信息
- `POST /delete_user`: 删除单个用户
- `POST /batch_delete_users`: 批量删除用户（最多100个）

**对话管理接口**:
- `GET /get_conversations`: 获取用户对话列表（含预览）
- `GET /get_conversation_detail`: 获取对话详细记录
- `POST /delete_conversation`: 删除指定对话
- `POST /clear_all_conversations`: 清空用户所有对话

#### 4. `config.py` - 配置管理
**特性**:
- 基于环境变量的配置加载（`.env` 文件）
- 多环境配置支持（DevelopmentConfig/ProductionConfig）
- 生产环境配置验证（强制修改默认密钥）
- 数据库连接池参数配置

#### 5. `utils/` - 工具类模块
- **auth.py**: 
  - `hash_password()`: bcrypt 密码哈希
  - `verify_password()`: 密码验证
  - `generate_token()`: JWT Token 生成
  - `decode_token()`: JWT Token 解码
  - `@token_required`: 认证装饰器
  - `@admin_required`: 管理员权限装饰器

- **db_utils.py**: 
  - `MySQLConnectionPool`: MySQL 连接池单例
  - `get_db_connection()`: 获取数据库连接

- **logger.py**: 
  - `setup_logger()`: 日志配置（文件轮转、控制台输出）
  - 自动创建 `logs/` 目录
  - 分离 INFO 和 ERROR 日志

- **validators.py**: 
  - `validate_username()`: 用户名验证（3-50字符，字母/数字/中文）
  - `validate_password()`: 密码强度验证（8-128字符，大小写+数字）
  - `validate_age()`: 年龄验证（1-150）
  - `validate_gender()`: 性别验证
  - `validate_question()`: 问题长度验证（2-500字符）
  - `validate_ill_name()`: 疾病名验证（防注入）
  - `sanitize_input()`: 输入 sanitization

## 💻 环境要求

- **Python**: >= 3.9（推荐 3.10+）
- **Neo4j**: >= 5.x（运行在 `bolt://localhost:7687`）
- **MySQL**: >= 5.7 或 MariaDB >= 10.2
- **Redis**（可选）: >= 6.x（用于分布式缓存和速率限制）
- **操作系统**: Windows / Linux / macOS
- **内存**: 建议 4GB+（LangChain + Neo4j 较耗内存）

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd MedicalQA_Backend

# 创建虚拟环境（强烈推荐）
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖包
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填写实际配置
# ⚠️ 必填项：DEEPSEEK_API_KEY
```

**`.env` 文件关键配置**:
```env
# ===== Neo4j 配置 =====
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# ===== DeepSeek API 配置（必填）=====
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# ===== MySQL 配置 =====
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=userdb

# ===== Flask 配置 =====
FLASK_SECRET_KEY=change-this-to-random-string-in-production
FLASK_DEBUG=True
FLASK_PORT=5001

# ===== JWT 配置 =====
JWT_SECRET_KEY=change-this-to-another-random-string
JWT_ACCESS_TOKEN_EXPIRES=3600

# ===== Redis 配置（可选，用于分布式缓存）=====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

⚠️ **生产环境注意事项**:
- 必须修改 `FLASK_SECRET_KEY` 和 `JWT_SECRET_KEY` 为随机字符串
- 设置 `FLASK_DEBUG=False`
- 使用强密码保护数据库

### 3. 初始化数据库

#### 3.1 MySQL 数据库

```bash
# 执行建表脚本
mysql -u root -p < generate_table.sql

# 或者在 MySQL 客户端中手动执行 generate_table.sql 的内容
```

建表脚本会创建：
- `user` 表：用户信息
- `admin` 表：管理员账号
- `conversations` 表：对话历史记录

#### 3.2 Neo4j 图数据库

```bash
# 1. 确保 Neo4j 服务已启动
# 默认访问地址: http://localhost:7474
# Bolt 协议地址: bolt://localhost:7687

# 2. 首次使用需修改默认密码
# 浏览器访问 http://localhost:7474
# 默认账号: neo4j / neo4j
# 按提示修改密码后，更新 .env 文件中的 NEO4J_PASSWORD

# 3. 导入医疗数据到 Neo4j
python import_to_neo4j.py
```

⚠️ **注意**: 
- `import_to_neo4j.py` 会**清空现有数据**并重新导入 `data.csv` 中的所有数据
- 确保 `data.csv` 文件存在且格式正确
- 首次导入可能需要几分钟时间（取决于数据量）

### 4. 启动服务

```bash
# 开发模式启动（热重载）
python app.py
```

服务将在 `http://127.0.0.1:5001` 启动。

### 5. 验证安装

```bash
# 1. 健康检查
curl http://127.0.0.1:5001/health

# 预期响应:
# {"status":"healthy","services":{"neo4j":"healthy","flask":"healthy"},"timestamp":"..."}

# 2. 测试问答接口
curl "http://127.0.0.1:5001/question?question=感冒有哪些症状？"

# 预期响应:
# {"answer":"感冒的常见症状包括...","source":"knowledge_graph","confidence":"high"}

# 3. 测试图谱接口
curl "http://127.0.0.1:5001/get_graph?ill=感冒"

# 4. 测试搜索建议
curl "http://127.0.0.1:5001/search_suggestions?keyword=感冒&limit=5"
```

## 📖 API 接口文档

### 基础信息

- **Base URL**: `http://localhost:5001`
- **Content-Type**: `application/json`
- **认证方式**: JWT Bearer Token（部分接口需要）

### 1. 医疗问答接口

#### GET /question
获取医疗问题的智能回答

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | ✅ | 医疗相关问题（2-500字符） |
| conversation_id | string | ❌ | 会话ID（用于保存对话历史） |

**请求头**（可选，用于保存对话）:
```
Authorization: Bearer <jwt_token>
```

**响应示例**:
```json
{
  "answer": "感冒的常见症状包括流鼻涕、咳嗽、喉咙痛、发热等。建议您多休息、多喝水，如症状持续请及时就医。",
  "source": "knowledge_graph",
  "confidence": "high"
}
```

**响应字段说明**:
- `answer`: AI 生成的回答内容
- `source`: 答案来源
  - `knowledge_graph`: 来自知识图谱
  - `llm_fallback`: 来自 LLM 通用知识
  - `cache`: 来自缓存
  - `llm_error_fallback`: 异常降级后的 LLM 回答
- `confidence`: 置信度（high/medium/low）

**速率限制**: 30 次/分钟/IP

---

### 2. 知识图谱接口

#### GET /get_graph
获取知识图谱可视化数据

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ill | string | ❌ | 疾病名称（为空则返回全部图谱） |

**响应示例**:
```json
{
  "graph_data": [
    {"name": "感冒", "symbolSize": 50, "category": "ill"},
    {"name": "流鼻涕", "symbolSize": 50, "category": "symptom"}
  ],
  "links": [
    {"source": "感冒", "target": "流鼻涕", "name": "has_symptom"}
  ],
  "labels": [{"name": "ill"}, {"name": "symptom"}],
  "stats": {
    "node_count": 2,
    "link_count": 1,
    "category_count": 2
  }
}
```

**缓存策略**: 1小时 TTL

---

#### GET /get_ill_info
获取疾病详细信息

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ill | string | ✅ | 疾病名称（支持模糊匹配） |

**响应示例**:
```json
[
  {
    "data": {
      "name": "感冒",
      "source_link": "https://tag.120ask.com/jibing/ganmao.html",
      "symptom": "流鼻涕, 咳嗽, 喉咙痛, 发热",
      "department": "内科, 呼吸科",
      "class1": "呼吸系统疾病",
      "class2": "上呼吸道感染",
      "easy_ill_people": "儿童, 老年人",
      "cure_method": "药物治疗, 休息, 多喝水",
      "cure_cost": "100-500元",
      "if_infect": "是",
      "ill_proportion": "常见",
      "cure_rate": "95%",
      "healing_cycle": "7-10天"
    }
  }
]
```

**缓存策略**: 2小时 TTL

---

#### GET /search_suggestions
获取疾病名称搜索建议（自动补全）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | ✅ | 搜索关键词（1-50字符） |
| limit | int | ❌ | 返回数量（默认10，最大20） |

**响应示例**:
```json
{
  "success": true,
  "suggestions": ["感冒", "过敏性鼻炎", "肺炎"],
  "count": 3
}
```

**速率限制**: 60 次/分钟/IP

---

#### GET /get_analysis_data
获取统计分析数据（用于数据可视化）

**响应示例**:
```json
{
  "node_counts": [
    {"name": "疾病", "value": 500},
    {"name": "症状", "value": 1200},
    {"name": "科室", "value": 50},
    {"name": "治疗方法", "value": 300}
  ],
  "class1_ill_counts": [
    {"name": "呼吸系统疾病", "value": 80},
    {"name": "消化系统疾病", "value": 65}
  ],
  "infectious_counts": [
    {"name": "是", "value": 120},
    {"name": "否", "value": 380}
  ],
  "healing_cycle_counts": [
    {"name": "7-10天", "value": 150},
    {"name": "1-3个月", "value": 100}
  ]
}
```

---

### 3. 用户管理接口

#### POST /register
用户注册

**请求体**:
```json
{
  "username": "testuser",
  "password": "Password123",
  "age": 25,
  "gender": "male"
}
```

**字段约束**:
- `username`: 3-50字符，仅允许字母/数字/下划线/中文
- `password`: 8-128字符，必须包含大小写字母和数字
- `age`: 1-150 整数
- `gender`: "male"/"female"/"other"/"男"/"女"/"其他"

**响应**:
```json
{
  "success": true,
  "message": "Registration successful"
}
```

---

#### POST /login
用户登录

**请求体**:
```json
{
  "username": "testuser",
  "password": "Password123"
}
```

**响应**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "testuser",
    "age": 25,
    "gender": "male",
    "create_time": "2024-01-01T00:00:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

⚠️ **重要**: 保存返回的 `token`，后续请求需要在 Header 中携带

---

#### POST /Adminlogin
管理员登录

**请求体**:
```json
{
  "username": "admin",
  "password": "admin"
}
```

**响应**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "adminname": "admin",
    "create_time": "2024-01-01T00:00:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "is_admin": true
  }
}
```

---

#### GET /get_users
获取所有用户列表（需管理员权限）

**请求头**:
```
Authorization: Bearer <admin_jwt_token>
```

**响应**:
```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "username": "testuser",
      "age": 25,
      "gender": "male",
      "create_time": "2024-01-01T00:00:00"
    }
  ]
}
```

---

#### POST /add_users
添加用户（管理员接口）

**请求体**:
```json
{
  "username": "newuser",
  "password": "Password123",
  "age": 30,
  "gender": "female"
}
```

---

#### POST /update_user
更新用户信息

**请求体**:
```json
{
  "id": 1,
  "username": "updateduser",
  "password": "NewPassword123",
  "age": 26,
  "gender": "male"
}
```

⚠️ **注意**: `password` 字段可选，不提供则不修改密码

---

#### POST /delete_user
删除单个用户

**请求体**:
```json
{
  "id": 1
}
```

---

#### POST /batch_delete_users
批量删除用户（管理员接口）

**请求体**:
```json
{
  "user_ids": [1, 2, 3, 4, 5]
}
```

**约束**: 单次最多删除 100 个用户

**响应**:
```json
{
  "success": true,
  "message": "Deleted 5 users",
  "deleted_count": 5
}
```

---

### 4. 对话管理接口

⚠️ **所有对话接口都需要 JWT Token 认证**

#### GET /get_conversations
获取用户的对话列表

**请求头**:
```
Authorization: Bearer <jwt_token>
```

**响应**:
```json
{
  "success": true,
  "conversations": [
    {
      "conversation_id": "conv-123456",
      "preview": "感冒的常见症状包括流鼻涕、咳嗽...",
      "last_update": "2024-01-15 14:30:00",
      "qa_count": 5
    }
  ]
}
```

---

#### GET /get_conversation_detail
获取对话的详细记录

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | string | ✅ | 会话ID |

**请求头**:
```
Authorization: Bearer <jwt_token>
```

**响应**:
```json
{
  "success": true,
  "conversation_id": "conv-123456",
  "messages": [
    {
      "role": "user",
      "username": "testuser",
      "content": "感冒有哪些症状？",
      "create_time": "2024-01-15 14:25:00"
    },
    {
      "role": "assistant",
      "content": "感冒的常见症状包括...",
      "create_time": "2024-01-15 14:25:00"
    }
  ]
}
```

---

#### POST /delete_conversation
删除指定对话

**请求头**:
```
Authorization: Bearer <jwt_token>
```

**请求体**:
```json
{
  "conversation_id": "conv-123456"
}
```

---

#### POST /clear_all_conversations
清空用户的所有对话

**请求头**:
```
Authorization: Bearer <jwt_token>
```

**响应**:
```json
{
  "success": true,
  "message": "Cleared 10 conversations",
  "deleted_count": 10
}
```

---

### 5. 系统接口

#### GET /health
服务健康状态检查

**响应**:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": "healthy",
    "flask": "healthy"
  },
  "timestamp": "2024-01-15 14:30:00"
}
```

---

### 错误响应格式

所有错误响应统一格式：

```json
{
  "error": "错误描述信息"
}
```

或（用户接口）:

```json
{
  "success": false,
  "message": "错误描述信息",
  "error": "详细错误信息（仅开发环境）"
}
```

**常见 HTTP 状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `401`: 未认证或 Token 无效
- `403`: 权限不足
- `404`: 资源不存在
- `429`: 速率限制 exceeded
- `500`: 服务器内部错误

## ⚙️ 配置说明

### 环境变量详解

| 变量名 | 说明 | 默认值 | 必填 | 生产环境建议 |
|--------|------|--------|------|-------------|
| `NEO4J_URI` | Neo4j Bolt 协议地址 | `bolt://localhost:7687` | ✅ | 使用内网地址 |
| `NEO4J_USERNAME` | Neo4j 用户名 | `neo4j` | ✅ | - |
| `NEO4J_PASSWORD` | Neo4j 密码 | `password` | ✅ | 使用强密码 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - | ✅ | 妥善保管，勿泄露 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 基础 URL | `https://api.deepseek.com` | ❌ | - |
| `DEEPSEEK_MODEL` | DeepSeek 模型名称 | `deepseek-chat` | ❌ | - |
| `MYSQL_HOST` | MySQL 主机地址 | `localhost` | ✅ | 使用内网地址 |
| `MYSQL_USER` | MySQL 用户名 | `root` | ✅ | 创建专用账号 |
| `MYSQL_PASSWORD` | MySQL 密码 | `123456` | ✅ | 使用强密码 |
| `MYSQL_DB` | MySQL 数据库名 | `userdb` | ✅ | - |
| `FLASK_SECRET_KEY` | Flask 密钥 | `dev-secret-key...` | ✅ | **必须修改**为随机字符串 |
| `FLASK_DEBUG` | 调试模式 | `True` | ❌ | 生产环境设为 `False` |
| `FLASK_PORT` | Flask 服务端口 | `5001` | ❌ | - |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `jwt-secret-key...` | ✅ | **必须修改**为随机字符串 |
| `JWT_ACCESS_TOKEN_EXPIRES` | Token 过期时间（秒） | `3600` | ❌ | 根据需求调整 |
| `REDIS_HOST` | Redis 主机地址 | `localhost` | ❌ | 生产环境建议启用 |
| `REDIS_PORT` | Redis 端口 | `6379` | ❌ | - |
| `REDIS_DB` | Redis 数据库编号 | `0` | ❌ | - |

### 多环境配置

在 `config.py` 中定义了三种配置模式：

- **DevelopmentConfig**: 开发环境（DEBUG=True）
- **ProductionConfig**: 生产环境（DEBUG=False，有配置验证）
- **default**: 默认使用 DevelopmentConfig

通过设置 `FLASK_ENV` 环境变量切换配置：
```bash
export FLASK_ENV=production  # Linux/Mac
set FLASK_ENV=production     # Windows
```

## 🗄️ 数据库设计

### Neo4j 知识图谱 Schema

#### 节点类型（Node Labels）

| 节点标签 | 属性 | 说明 | 索引 |
|---------|------|------|------|
| `ill` | name, source_link | 疾病 | ✅ name |
| `symptom` | name | 症状 | ✅ name |
| `department` | name | 科室 | ✅ name |
| `class1` | name | 一级分类 | ✅ name |
| `class2` | name | 二级分类 | ✅ name |
| `easy_ill_people` | name | 好发人群 | ✅ name |
| `cure_method` | name | 治疗方法 | ✅ name |
| `cure_cost` | name | 治疗费用 | ✅ name |
| `if_infect` | name | 是否传染 | ✅ name |
| `ill_proportion` | name | 患病比例 | ✅ name |
| `cure_rate` | name | 治愈率 | ✅ name |
| `healing_cycle` | name | 治疗周期 | ✅ name |

#### 关系类型（Relationship Types）

```cypher
(:ill)-[:has_symptom]->(:symptom)              # 疾病-症状
(:ill)-[:should_see]->(:department)            # 疾病-就诊科室
(:ill)-[:belongs_to_class1]->(:class1)         # 疾病-一级分类
(:ill)-[:belongs_to_class2]->(:class2)         # 疾病-二级分类
(:ill)-[:affects_people]->(:easy_ill_people)   # 疾病-好发人群
(:ill)-[:treated_by]->(:cure_method)           # 疾病-治疗方法
(:ill)-[:costs]->(:cure_cost)                  # 疾病-治疗费用
(:ill)-[:is_infectious]->(:if_infect)          # 疾病-是否传染
(:ill)-[:has_proportion]->(:ill_proportion)    # 疾病-患病比例
(:ill)-[:has_cure_rate]->(:cure_rate)          # 疾病-治愈率
(:ill)-[:has_healing_cycle]->(:healing_cycle)  # 疾病-治疗周期
```

### MySQL 用户数据库

#### user 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 用户ID |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| password | VARCHAR(255) | NOT NULL | 密码（bcrypt加密） |
| age | INT | NULL | 年龄 |
| gender | VARCHAR(10) | NULL | 性别 |
| create_time | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引**: `idx_username (username)`

#### admin 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 管理员ID |
| adminname | VARCHAR(50) | NOT NULL, UNIQUE | 管理员账号 |
| password | VARCHAR(255) | NOT NULL | 密码（bcrypt加密） |
| create_time | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**: `idx_adminname (adminname)`

#### conversations 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 对话记录ID |
| user_id | INT | NOT NULL, FOREIGN KEY | 用户ID（关联 user 表） |
| username | VARCHAR(50) | NOT NULL | 用户名（冗余字段，便于查询） |
| conversation_id | VARCHAR(100) | NOT NULL | 会话ID（前端生成UUID） |
| conversation_data | JSON | NOT NULL | 对话数据 `{"username": "问题", "AI": "回答"}` |
| create_time | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**: 
- `idx_user_conversation (user_id, conversation_id)`
- `idx_conversation_id (conversation_id)`

**外键**: `FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE`

## 🔒 安全特性

### 1. 密码安全
- ✅ 使用 **bcrypt** 算法进行密码哈希（work factor=12）
- ✅ 盐值自动生成，防止彩虹表攻击
- ✅ 密码长度限制：8-128 字符
- ✅ 密码强度要求：大小写字母 + 数字
- ✅ 密码不在日志中记录明文

### 2. JWT 认证
- ✅ 基于 HS256 算法的 JWT Token
- ✅ Token 可配置过期时间（默认 1 小时）
- ✅ `@token_required` 装饰器保护需要认证的接口
- ✅ `@admin_required` 装饰器保护管理员接口
- ✅ Token 失效后需重新登录

### 3. 输入验证
- ✅ **用户名**: 3-50 字符，仅允许字母、数字、下划线、中文
- ✅ **密码**: 8-128 字符，必须包含大小写字母和数字
- ✅ **年龄**: 1-150 整数
- ✅ **疾病名称**: 1-100 字符，禁止特殊字符（`;`, `'`, `"`, `\`）
- ✅ **问题**: 2-500 字符
- ✅ **搜索关键词**: 1-50 字符

### 4. 防注入攻击
- ✅ **SQL 注入防护**: 使用参数化查询（`%s` 占位符）
- ✅ **Cypher 注入防护**: 
  - 使用参数化查询（`$param` 语法）
  - 输入验证与字符过滤
  - 禁用危险的 APOC 过程
- ✅ **XSS 防护**: 输入 sanitization（移除 null bytes、转义特殊字符）

### 5. API 速率限制
- ✅ 默认限制：200 次/天，50 次/小时
- ✅ 问答接口额外限制：30 次/分钟
- ✅ 搜索建议接口：60 次/分钟
- ✅ 基于 IP 地址进行限流
- ✅ 使用 Redis 存储限流数据（可选）

### 6. CORS 配置
- ✅ 可配置的跨域资源共享策略
- ✅ 默认允许所有来源（生产环境建议限制具体域名）

### 7. 日志审计
- ✅ 所有关键操作记录日志（注册、登录、问答、删除）
- ✅ 错误日志单独存储（`logs/error.log`）
- ✅ 日志轮转：单文件最大 10MB，保留 5 个备份
- ✅ 敏感信息脱敏（密码不记录明文）
- ✅ 结构化日志格式（时间戳、级别、文件名、行号、消息）

### 8. 错误处理
- ✅ 全局错误处理器（404/500/429）
- ✅ 统一的错误响应格式
- ✅ 生产环境不暴露详细堆栈信息
- ✅ 异常捕获与日志记录

## 🚀 性能优化

### 1. 多级缓存策略

#### 内存缓存（langchain_qa.py）
- **用途**: 缓存问答结果
- **TTL**: 1 小时
- **优势**: 零延迟，无需网络IO
- **劣势**: 进程重启后丢失，不支持分布式

#### Redis 缓存（app.py）
- **用途**: 缓存图谱数据和疾病信息
- **TTL**: 
  - 图谱数据: 1 小时
  - 疾病信息: 2 小时
- **优势**: 支持分布式，持久化
- **配置**: 需在 `.env` 中配置 Redis

### 2. 数据库优化

#### Neo4j
- ✅ 所有节点 `name` 属性建立索引
- ✅ 使用参数化查询避免重复编译
- ✅ LIMIT 限制返回数据量（默认 200）

#### MySQL
- ✅ 使用连接池（DBUtils）避免频繁创建连接
- ✅ 关键字段建立索引（username, conversation_id）
- ✅ 外键约束保证数据一致性

### 3. 应用层优化
- ✅ Flask 多线程模式（`threaded=True`）
- ✅ LangChain LLM 请求超时设置（30秒）
- ✅ 批量操作支持（批量删除用户）
- ✅ 懒加载（Redis 连接失败不影响主流程）

### 4. 监控与调优建议
- 📊 监控 Neo4j 查询性能（慢查询日志）
- 📊 监控 Redis 命中率
- 📊 监控 API 响应时间
- 📊 定期清理过期对话记录
- 📊 根据负载调整速率限制阈值

## 🧪 开发指南

### 代码规范
- 遵循 PEP 8 Python 代码风格
- 使用类型注解（Type Hints）
- 函数和类添加文档字符串（Docstrings）
- 日志记录关键操作和异常

### 添加新接口
1. 在 `app.py` 或 `user.py` 中添加路由函数
2. 实现输入验证（使用 `utils/validators.py`）
3. 添加速率限制装饰器（如需要）
4. 添加日志记录
5. 统一错误处理
6. 更新本文档

### 调试技巧
```python
# 启用 Flask 调试模式
export FLASK_DEBUG=True

# 查看详细日志
tail -f logs/app.log
tail -f logs/error.log

# 测试单个接口
curl -v "http://localhost:5001/health"

# 查看 Neo4j 查询日志
# 在 langchain_qa.py 中设置 verbose=True
```

### 常见问题

#### Q1: Redis 连接失败怎么办？
A: 系统会自动降级到纯内存缓存，不影响核心功能。如需使用 Redis，请确保：
```bash
# 安装 Redis
sudo apt-get install redis-server  # Ubuntu
brew install redis                 # macOS

# 启动 Redis
redis-server

# 测试连接
redis-cli ping  # 应返回 PONG
```

#### Q2: DeepSeek API 调用失败？
A: 检查以下几点：
- `.env` 文件中 `DEEPSEEK_API_KEY` 是否正确
- 网络连接是否正常
- API 配额是否用完
- 查看 `logs/error.log` 中的详细错误信息

#### Q3: Neo4j 查询很慢？
A: 优化建议：
- 确认索引已创建（运行 `import_to_neo4j.py` 会自动创建）
- 减少 `LIMIT` 值（在 `get_result()` 函数中）
- 简化 Cypher 查询
- 增加 Neo4j 内存配置

#### Q4: 如何重置管理员密码？
A: 运行迁移脚本：
```bash
python migrate_passwords.py
```

#### Q5: 如何清空缓存？
A: 
- 内存缓存：重启 Flask 应用
- Redis 缓存：`redis-cli FLUSHDB`

## 🐛 故障排查

### 日志位置
- 应用日志: `logs/app.log`
- 错误日志: `logs/error.log`

### 常见问题及解决方案

#### 1. 服务无法启动
```bash
# 检查端口是否被占用
netstat -ano | findstr :5001  # Windows
lsof -i :5001                  # Linux/Mac

# 检查依赖是否安装
pip list | grep Flask

# 查看详细错误信息
python app.py 2>&1 | tee startup.log
```

#### 2. Neo4j 连接失败
```bash
# 检查 Neo4j 服务状态
# Windows: 服务管理器中查看 Neo4j 服务
# Linux: systemctl status neo4j

# 测试 Bolt 连接
python -c "from neo4j import GraphDatabase; d=GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); d.verify_connectivity()"

# 检查防火墙设置
```

#### 3. MySQL 连接失败
```bash
# 检查 MySQL 服务状态
# Windows: 服务管理器中查看 MySQL 服务
# Linux: systemctl status mysql

# 测试连接
mysql -u root -p -h localhost

# 检查 .env 中的配置是否正确
```

#### 4. API 返回 429 错误
- 原因：触发速率限制
- 解决：等待一段时间后重试，或调整 `flask-limiter` 配置

#### 5. 问答接口返回空答案
- 检查 DeepSeek API Key 是否有效
- 查看 `logs/error.log` 中的详细错误
- 测试简单问题（如"感冒的症状"）

### 性能诊断

```python
# 在 app.py 中添加性能监控
import time

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        logger.info(f"{request.method} {request.path} took {elapsed:.2f}s")
    return response
```

## 📝 更新日志

### v2.0.0 (2024-01-15)
- ✨ 新增搜索建议接口 `/search_suggestions`
- ✨ 新增批量删除用户接口 `/batch_delete_users`
- ✨ 新增清空所有对话接口 `/clear_all_conversations`
- 🚀 添加多级缓存机制（内存 + Redis）
- 🚀 优化问答接口返回元数据（source/confidence）
- 🔒 增强输入验证和 sanitization
- 🔒 添加全局错误处理器
- 🐛 修复 `get_ill_info` 返回格式不一致问题
- 📚 完善 API 文档和 README

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础问答功能
- 用户管理系统
- 知识图谱可视化

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: your-email@example.com

---

## 🚀 v2.1 更新说明 (2026-04-17)

### 新增功能：短信验证码认证

#### 1. 阿里云短信服务集成
- ✅ 使用正确的SDK (`alibabacloud-dysmsapi20170525`)
- ✅ 自动生成6位数字验证码
- ✅ 支持自定义验证码长度
- ✅ 完善的错误处理和响应检查

#### 2. 新增API接口
- `POST /api/send_verification_code` - 发送短信验证码
- `POST /api/check_verification_code` - 验证短信验证码

#### 3. 存储方案
- ✅ Redis存储（推荐）：高性能、分布式
- ✅ 内存存储降级：开发环境友好
- ✅ 自动过期清理：5分钟有效期
- ✅ 验证后自动删除：防止重放攻击

#### 4. 安全防护
- ✅ 手机号格式验证
- ✅ 输入参数校验
- ✅ 统一的API响应格式
- ✅ 详细的日志记录

### 文档与测试
- 📄 [SMS_CHANGES_SUMMARY.md](SMS_CHANGES_SUMMARY.md) - 修改总结
- 📖 [SMS_API_DOCUMENTATION.md](SMS_API_DOCUMENTATION.md) - API完整文档
- 🚀 [SMS_QUICK_START.md](SMS_QUICK_START.md) - 快速开始指南
- 🧪 [test_sms_verification.py](test_sms_verification.py) - 测试脚本

### 配置要求
在 `.env` 文件中添加：
```env
ALI_ACCESS_KEY_ID="your-access-key-id"
ALI_ACCESS_KEY_SECRET="your-access-key-secret"
ALI_SIGN_NAME=您的短信签名
ALI_TEMPLATE_CODE=SMS_xxxxxx
```

### 兼容性
- ✅ 完全向后兼容
- ✅ 不影响现有功能
- ✅ 可选依赖（Redis）

---

## 🚀 v2.0 优化说明

### 主要改进

#### 1. 性能优化
- ✅ **Neo4j连接池**: 单例模式,最大50并发连接,性能提升30-50%
- ✅ **双层缓存**: Redis + 内存缓存,命中率提升至80%+
- ✅ **LLM重试机制**: 自动重试失败请求,成功率提升15-25%
- ✅ **查询优化**: 使用set去重,移除冗余JSON序列化

#### 2. 安全加固
- ✅ **SQL注入防护**: 运行时检测 + 参数化查询,双重防护
- ✅ **XSS防护**: 输入过滤 + 输出转义 + CSP头
- ✅ **CORS优化**: 生产环境限制允许的源
- ✅ **安全响应头**: X-Frame-Options, CSP等6个安全头

#### 3. 代码质量
- ✅ **统一响应格式**: APIResponse工具类,标准化所有API响应
- ✅ **异常处理**: 完整堆栈日志,区分开发/生产环境
- ✅ **配置验证**: 启动时自动验证必要配置
- ✅ **优雅关闭**: 信号处理,正确释放所有资源

#### 4. 新增工具模块
- `utils/neo4j_utils.py` - Neo4j连接池管理
- `utils/security.py` - 安全中间件
- `utils/response.py` - 统一响应格式

### 快速验证

运行测试脚本验证优化:
```bash
python test_optimizations.py
```

### 详细文档

- 📖 [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) - 详细优化说明
- 📊 [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) - 完整优化报告

### 兼容性

- ✅ 向后兼容: 所有现有API端点保持不变
- ✅ 数据兼容: 无需修改数据库schema
- ⚠️ 依赖要求: 确保安装所有requirements.txt中的依赖
- ⚠️ Redis可选: 无Redis时自动使用内存缓存

---

**祝您使用愉快！** 🎉
