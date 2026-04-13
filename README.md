# 医疗问答系统后端 (Medical QA System Backend)

基于 Flask + LangChain + Neo4j + DeepSeek LLM 构建的智能医疗问答系统后端服务。该系统利用知识图谱和大型语言模型，为用户提供准确的医疗信息问答、疾病信息查询和数据可视化功能。

## 📋 目录

- [核心特性](#核心特性)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [配置说明](#配置说明)
- [数据库设计](#数据库设计)
- [安全特性](#安全特性)
- [开发指南](#开发指南)
- [故障排查](#故障排查)

## ✨ 核心特性

### 1. 智能医疗问答
- **知识图谱查询**: 使用 `GraphCypherQAChain` 将自然语言问题自动转换为 Cypher 查询语句
- **DeepSeek LLM 集成**: 基于 DeepSeek-V3 大语言模型（通过 OpenAI 兼容接口）进行 Cypher 生成和答案优化
- **智能降级机制**: 
  - 当知识图谱包含答案时，LLM 基于图谱数据进行专业化扩展回答
  - 当知识图谱无答案时，自动降级到 LLM 通用医学知识进行回答
- **Schema 感知**: 预定义图数据库 Schema，确保生成的 Cypher 查询结构正确且高效

### 2. 知识图谱可视化
- 支持疾病、症状、科室、治疗方法等多维度节点关系展示
- 提供疾病详细信息查询（症状、科室、分类、治疗费用、治愈率等）
- 动态统计分析面板（节点统计、疾病分类分布、传染病比例、治疗周期分布）

### 3. 用户管理系统
- 完整的用户注册、登录、信息管理功能
- 管理员后台管理接口
- JWT Token 认证机制
- bcrypt 密码加密存储

### 4. 安全防护
- 输入验证与 sanitization（防止 SQL/NoSQL 注入）
- API 速率限制（Flask-Limiter）
- 参数化查询（防止 Cypher 注入）
- 完善的日志记录与错误追踪

## 🛠️ 技术栈

### 后端框架
- **Flask 3.0.2**: Web 应用框架
- **Flask-Cors 4.0.0**: 跨域资源共享支持
- **Flask-Limiter 3.5.0**: API 速率限制

### AI & NLP
- **LangChain 0.3.20**: LLM 应用开发框架
- **langchain-openai 0.3.7**: OpenAI API 集成（用于 DeepSeek）
- **langchain-neo4j 0.3.0**: Neo4j 图数据库集成
- **DeepSeek Chat**: 大语言模型（deepseek-chat）
- **Jieba 0.42.1**: 中文分词工具

### 数据库
- **Neo4j 5.28.1**: 图数据库（知识图谱存储）
- **PyMySQL 1.1.0**: MySQL 客户端
- **DBUtils 3.1.0**: 数据库连接池管理
- **Redis**: 缓存与速率限制存储（可选）

### 数据处理
- **Pandas 2.0.1**: 数据处理与分析
- **NumPy 1.26.4**: 数值计算
- **Requests 2.32.3**: HTTP 请求库
- **BeautifulSoup4**: HTML 解析（爬虫）

### 安全
- **bcrypt 4.1.2**: 密码哈希加密
- **PyJWT 2.8.0**: JWT Token 生成与验证
- **python-dotenv 1.0.1**: 环境变量管理

### 其他工具
- **py2neo**: Neo4j Python 客户端（数据导入）
- **sentence-transformers 2.7.0**: 文本嵌入（预留扩展）
- **scikit-learn 1.3.0**: 机器学习工具（预留扩展）

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Vue/React)               │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────────────────┐
│              Flask Application (app.py)              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ User Routes │  │  QA Routes   │  │ Graph      │ │
│  │ (user.py)   │  │ (/question)  │  │ Routes     │ │
│  └─────────────┘  └──────┬───────┘  └────────────┘ │
└──────────────────────────┼──────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼───────┐  ┌──────▼───────┐  ┌──────▼──────┐
│  LangChain    │  │   Neo4j      │  │   MySQL     │
│  QA Chain     │  │   Graph DB   │  │   User DB   │
│               │  │              │  │             │
│ • Cypher Gen  │  │ • ill       │  │ • user      │
│ • KG Query    │  │ • symptom   │  │ • admin     │
│ • LLM Answer  │  │ • dept      │  │             │
│ • Fallback    │  │ • ...       │  │             │
└───────┬───────┘  └──────────────┘  └─────────────┘
        │
┌───────▼───────┐
│  DeepSeek     │
│  LLM API      │
└───────────────┘
```

## 📁 项目结构

```
MedicalQA_Backend/
├── app.py                      # Flask 主应用入口
├── config.py                   # 配置管理模块
├── langchain_qa.py            # LangChain 问答核心逻辑
├── user.py                    # 用户管理 API 蓝图
├── crawler.py                 # 医疗数据爬虫
├── import_to_neo4j.py         # Neo4j 数据导入脚本
├── generate_table.sql         # MySQL 数据库建表脚本
├── migrate_passwords.py       # 密码迁移工具
├── requirements.txt           # Python 依赖包
├── .env                       # 环境变量配置（不提交到 Git）
├── .env.example              # 环境变量示例文件
├── data.csv                   # 爬取的医疗数据（CSV 格式）
│
├── utils/                     # 工具类模块
│   ├── __init__.py
│   ├── auth.py               # 认证工具（JWT、密码哈希）
│   ├── db_utils.py           # 数据库连接池管理
│   ├── logger.py             # 日志配置
│   └── validators.py         # 输入验证器
│
├── logs/                      # 日志目录
│   ├── app.log               # 应用日志
│   └── error.log             # 错误日志
│
└── dist/                      # 前端静态文件目录（由前端项目构建生成）
    ├── index.html
    └── ...
```

### 核心模块说明

#### 1. `app.py` - 主应用入口
- Flask 应用初始化与配置
- Neo4j 驱动初始化
- 路由注册：
  - `/get_graph`: 获取知识图谱数据（支持按疾病过滤）
  - `/get_ill_info`: 获取疾病详细信息
  - `/question`: 医疗问答接口（带速率限制）
  - `/get_analysis_data`: 获取统计分析数据
  - `/health`: 健康检查接口
  - `/`: 前端页面入口
- 用户 API 蓝图注册（`user.py`）

#### 2. `langchain_qa.py` - 问答核心
- `MedicalQAChain` 类：封装 LangChain 问答逻辑
- `FixedNeo4jGraph`: 自定义 Neo4j 图类（强制使用手动 Schema）
- `get_answer()`: 对外提供的问答接口函数
- 智能降级策略实现

#### 3. `user.py` - 用户管理
- Flask Blueprint: `api_bp`
- 用户接口：
  - `POST /register`: 用户注册
  - `POST /login`: 用户登录
  - `GET /get_users`: 获取所有用户（管理员）
  - `POST /add_users`: 添加用户（管理员）
  - `POST /update_user`: 更新用户信息
  - `POST /delete_user`: 删除用户
  - `POST /Adminlogin`: 管理员登录

#### 4. `config.py` - 配置管理
- 基于环境变量的配置加载
- 多环境配置支持（Development/Production）
- 配置项验证（生产环境安全检查）

#### 5. `utils/` - 工具类
- **auth.py**: JWT Token 生成/验证、密码哈希/验证、认证装饰器
- **db_utils.py**: MySQL 连接池管理（单例模式）
- **logger.py**: 日志配置（文件轮转、控制台输出）
- **validators.py**: 输入验证（用户名、密码、年龄、性别、问题、疾病名）

## 💻 环境要求

- **Python**: >= 3.9
- **Neo4j**: >= 5.x（运行在 `bolt://localhost:7687`）
- **MySQL**: >= 5.7 或 MariaDB >= 10.2
- **Redis**（可选）: >= 6.x（用于速率限制）
- **操作系统**: Windows / Linux / macOS

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd MedicalQA_Backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填写实际配置
# 必填项：DEEPSEEK_API_KEY
```

`.env` 文件关键配置：
```env
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# DeepSeek API 配置（必填）
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# MySQL 配置
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DB=userdb

# Flask 配置
FLASK_SECRET_KEY=your-secret-key-change-in-production
FLASK_DEBUG=True
FLASK_PORT=5001

# JWT 配置
JWT_SECRET_KEY=jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=3600

# Redis 配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 3. 初始化数据库

#### 3.1 MySQL 数据库

```bash
# 执行建表脚本
mysql -u root -p < generate_table.sql

# 或使用 MySQL 客户端手动执行 generate_table.sql 中的 SQL 语句
```

#### 3.2 Neo4j 图数据库

```bash
# 确保 Neo4j 服务已启动
# 默认访问地址: http://localhost:7474
# Bolt 协议地址: bolt://localhost:7687

# 首次使用需修改默认密码（默认为 neo4j/neo4j）
# 修改后更新 .env 文件中的 NEO4J_PASSWORD

# 导入数据到 Neo4j
python import_to_neo4j.py
```

**注意**: `import_to_neo4j.py` 会清空现有数据并重新导入 `data.csv` 中的所有数据。请确保 `data.csv` 文件存在且格式正确。

### 4. 启动服务

```bash
# 开发模式启动
python app.py
```

服务将在 `http://127.0.0.1:5001` 启动。

### 5. 验证安装

```bash
# 健康检查
curl http://127.0.0.1:5001/health

# 测试问答接口
curl "http://127.0.0.1:5001/question?question=感冒有哪些症状？"

# 测试图谱接口
curl "http://127.0.0.1:5001/get_graph?ill=感冒"
```

## 📖 API 文档

### 医疗问答接口

#### GET /question
获取医疗问题的智能回答

**请求参数:**
- `question` (string, required): 医疗相关问题

**响应示例:**
```json
{
  "answer": "感冒的常见症状包括流鼻涕、咳嗽、喉咙痛、发热等..."
}
```

**速率限制:** 30 次/分钟

---

### 知识图谱接口

#### GET /get_graph
获取知识图谱可视化数据

**请求参数:**
- `ill` (string, optional): 疾病名称（为空则返回全部图谱）

**响应示例:**
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

---

#### GET /get_ill_info
获取疾病详细信息

**请求参数:**
- `ill` (string, required): 疾病名称

**响应示例:**
```json
[
  {
    "data": {
      "name": "感冒",
      "source_link": "https://...",
      "symptom": "流鼻涕, 咳嗽, 喉咙痛",
      "department": "内科, 呼吸科",
      "class1": "呼吸系统疾病",
      "cure_method": "药物治疗, 休息",
      "cure_cost": "100-500元",
      "if_infect": "是",
      "healing_cycle": "7-10天"
    }
  }
]
```

---

#### GET /get_analysis_data
获取统计分析数据

**响应示例:**
```json
{
  "node_counts": [
    {"name": "疾病", "value": 500},
    {"name": "症状", "value": 1200}
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

### 用户管理接口

#### POST /register
用户注册

**请求体:**
```json
{
  "username": "testuser",
  "password": "Password123",
  "age": 25,
  "gender": "male"
}
```

**响应:**
```json
{
  "success": true,
  "message": "Registration successful"
}
```

---

#### POST /login
用户登录

**请求体:**
```json
{
  "username": "testuser",
  "password": "Password123"
}
```

**响应:**
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

---

#### POST /Adminlogin
管理员登录

**请求体:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**响应:**
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

**响应:**
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

**请求体:**
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

**请求体:**
```json
{
  "id": 1,
  "username": "updateduser",
  "password": "NewPassword123",
  "age": 26,
  "gender": "male"
}
```

---

#### POST /delete_user
删除用户

**请求体:**
```json
{
  "id": 1
}
```

---

### 健康检查接口

#### GET /health
服务健康状态检查

**响应:**
```json
{
  "status": "healthy",
  "services": {
    "neo4j": "healthy",
    "flask": "healthy"
  },
  "timestamp": "2024-01-01 12:00:00"
}
```

## ⚙️ 配置说明

### 环境变量详解

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `NEO4J_URI` | Neo4j Bolt 协议地址 | `bolt://localhost:7687` | 是 |
| `NEO4J_USERNAME` | Neo4j 用户名 | `neo4j` | 是 |
| `NEO4J_PASSWORD` | Neo4j 密码 | `password` | 是 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - | **是** |
| `DEEPSEEK_BASE_URL` | DeepSeek API 基础 URL | `https://api.deepseek.com` | 否 |
| `DEEPSEEK_MODEL` | DeepSeek 模型名称 | `deepseek-chat` | 否 |
| `MYSQL_HOST` | MySQL 主机地址 | `localhost` | 是 |
| `MYSQL_USER` | MySQL 用户名 | `root` | 是 |
| `MYSQL_PASSWORD` | MySQL 密码 | `123456` | 是 |
| `MYSQL_DB` | MySQL 数据库名 | `userdb` | 是 |
| `FLASK_SECRET_KEY` | Flask 密钥 | `dev-secret-key...` | **生产环境必填** |
| `FLASK_DEBUG` | 调试模式 | `True` | 否 |
| `FLASK_PORT` | Flask 服务端口 | `5001` | 否 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `jwt-secret-key...` | **生产环境必填** |
| `JWT_ACCESS_TOKEN_EXPIRES` | Token 过期时间（秒） | `3600` | 否 |
| `REDIS_HOST` | Redis 主机地址 | `localhost` | 否 |
| `REDIS_PORT` | Redis 端口 | `6379` | 否 |
| `REDIS_DB` | Redis 数据库编号 | `0` | 否 |

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

| 节点标签 | 属性 | 说明 |
|---------|------|------|
| `ill` | name, source_link | 疾病 |
| `symptom` | name | 症状 |
| `department` | name | 科室 |
| `class1` | name | 一级分类 |
| `class2` | name | 二级分类 |
| `easy_ill_people` | name | 好发人群 |
| `cure_method` | name | 治疗方法 |
| `cure_cost` | name | 治疗费用 |
| `if_infect` | name | 是否传染 |
| `ill_proportion` | name | 患病比例 |
| `cure_rate` | name | 治愈率 |
| `healing_cycle` | name | 治疗周期 |

#### 关系类型（Relationship Types）

```
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

#### admin 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 管理员ID |
| adminname | VARCHAR(50) | NOT NULL, UNIQUE | 管理员账号 |
| password | VARCHAR(255) | NOT NULL | 密码（bcrypt加密） |
| create_time | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

## 🔒 安全特性

### 1. 密码安全
- 使用 **bcrypt** 算法进行密码哈希
- 盐值自动生成，防止彩虹表攻击
- 密码长度限制：8-128 字符
- 密码强度要求：大小写字母 + 数字

### 2. JWT 认证
- 基于 HS256 算法的 JWT Token
- Token 可配置过期时间（默认 1 小时）
- `@token_required` 装饰器保护需要认证的接口
- `@admin_required` 装饰器保护管理员接口

### 3. 输入验证
- **用户名**: 3-50 字符，仅允许字母、数字、下划线、中文
- **密码**: 8-128 字符，必须包含大小写字母和数字
- **年龄**: 1-150 整数
- **疾病名称**: 1-100 字符，禁止特殊字符（`;`, `'`, `"`, `\`）
- **问题**: 2-500 字符

### 4. 防注入攻击
- **SQL 注入防护**: 使用参数化查询（`%s` 占位符）
- **Cypher 注入防护**: 
  - 使用参数化查询（`$param` 语法）
  - 输入验证与字符过滤
  - 禁用危险的 APOC 过程
- **XSS 防护**: 输入 sanitization

### 5. API 速率限制
- 默认限制：200 次/天，50 次/小时
- 问答接口额外限制：30 次/分钟
- 基于 IP 地址进行限流
- 使用 Redis 存储限流数据（可选）

### 6. 日志审计
- 所有关键操作记录日志（注册、登录、问答）
- 错误日志单独存储（`logs/error.log`）
- 日志轮转：单文件最大 10MB，保留 5 个备份
- 敏感信息脱敏（密码不记录明文）

## 🧪 开发指南
