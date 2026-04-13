# 医疗问答系统后端 API 文档

**版本**: v1.0  
**基础 URL**: `http://127.0.0.1:5001`  
**最后更新**: 2026-04-13

---

## 📋 目录

- [概述](#概述)
- [认证机制](#认证机制)
- [通用响应格式](#通用响应格式)
- [错误码说明](#错误码说明)
- [接口列表](#接口列表)
  - [医疗问答模块](#医疗问答模块)
  - [知识图谱模块](#知识图谱模块)
  - [用户管理模块](#用户管理模块)
  - [系统模块](#系统模块)
- [速率限制](#速率限制)
- [最佳实践](#最佳实践)

---

## 概述

本 API 文档描述了医疗问答系统后端提供的所有 RESTful 接口。所有接口均返回 JSON 格式数据，使用 UTF-8 编码。

### 技术栈
- **框架**: Flask 3.0.2
- **数据库**: Neo4j (知识图谱) + MySQL (用户数据)
- **AI 模型**: DeepSeek Chat (通过 LangChain)
- **认证**: JWT Token

### 环境要求
- Python >= 3.9
- Neo4j >= 5.x
- MySQL >= 5.7

---

## 认证机制

### JWT Token 认证

部分接口需要 JWT Token 认证。认证流程如下：

1. 调用登录接口获取 Token
2. 在后续请求的 Header 中添加 Token

**Header 格式:**
```
Authorization: Bearer <your_jwt_token>
```

**Token 有效期**: 3600 秒（1 小时）

**受保护的接口**:
- 目前所有用户管理接口暂未强制要求 Token（可根据需求添加 `@token_required` 装饰器）

---

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 失败响应
```json
{
  "success": false,
  "error": "错误信息",
  "message": "详细描述"
}
```

### 分页响应（如适用）
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
}
```

---

## 错误码说明

| HTTP 状态码 | 说明 | 常见原因 |
|------------|------|---------|
| 200 | 成功 | 请求成功处理 |
| 400 | 请求错误 | 参数缺失、格式错误、验证失败 |
| 401 | 未授权 | Token 缺失、无效或过期 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 资源不存在 | 请求的资源不存在 |
| 429 | 请求过多 | 触发速率限制 |
| 500 | 服务器错误 | 内部服务异常 |

---

## 接口列表

### 医疗问答模块

#### 1. 智能医疗问答

**接口地址**: `GET /question`

**接口描述**: 基于知识图谱和 LLM 的智能医疗问答接口，支持自然语言提问。

**速率限制**: 30 次/分钟

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| question | string | 是 | 医疗相关问题（2-500 字符） | 感冒有哪些症状？ |

**请求示例**:
```
GET /question?question=感冒有哪些症状？
```

**成功响应** (200):
```json
{
  "answer": "感冒的常见症状包括流鼻涕、咳嗽、喉咙痛、发热、头痛等。大多数感冒由病毒引起，通常在一周左右自愈。建议多休息、多喝水，如果症状严重可服用退烧药或止咳药。如持续高热或症状加重，请及时就医。"
}
```

**失败响应**:

400 - 参数错误:
```json
{
  "error": "Question is required"
}
```

400 - 验证失败:
```json
{
  "error": "Question must be at least 2 characters long"
}
```

429 - 速率限制:
```json
{
  "error": "Rate limit exceeded. Try again later."
}
```

500 - 服务器错误:
```json
{
  "error": "Failed to generate answer"
}
```

**注意事项**:
- 问题长度限制：2-500 字符
- 支持中文和英文提问
- 回答可能来自知识图谱或 LLM 通用知识
- 首次查询可能较慢（需生成 Cypher 查询）

---

### 知识图谱模块

#### 2. 获取知识图谱数据

**接口地址**: `GET /get_graph`

**接口描述**: 获取用于可视化的知识图谱数据，支持按疾病过滤。

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| ill | string | 否 | 疾病名称（为空则返回全部图谱） | 感冒 |

**请求示例**:
```
GET /get_graph?ill=感冒
```

**成功响应** (200):
```json
{
  "graph_data": [
    {
      "name": "感冒",
      "symbolSize": 50,
      "category": "ill"
    },
    {
      "name": "流鼻涕",
      "symbolSize": 50,
      "category": "symptom"
    },
    {
      "name": "咳嗽",
      "symbolSize": 50,
      "category": "symptom"
    },
    {
      "name": "内科",
      "symbolSize": 50,
      "category": "department"
    }
  ],
  "links": [
    {
      "source": "感冒",
      "target": "流鼻涕",
      "name": "has_symptom"
    },
    {
      "source": "感冒",
      "target": "咳嗽",
      "name": "has_symptom"
    },
    {
      "source": "感冒",
      "target": "内科",
      "name": "should_see"
    }
  ],
  "labels": [
    {"name": "ill"},
    {"name": "symptom"},
    {"name": "department"}
  ],
  "stats": {
    "node_count": 4,
    "link_count": 3,
    "category_count": 3
  }
}
```

**字段说明**:

- `graph_data`: 节点数组
  - `name`: 节点名称
  - `symbolSize`: 节点大小（固定 50）
  - `category`: 节点类型（ill/symptom/department 等）

- `links`: 关系数组
  - `source`: 源节点名称
  - `target`: 目标节点名称
  - `name`: 关系类型

- `labels`: 节点类型标签数组

- `stats`: 统计信息
  - `node_count`: 节点数量
  - `link_count`: 关系数量
  - `category_count`: 类别数量

**失败响应**:

500 - 服务器错误:
```json
{
  "error": "Failed to retrieve graph data"
}
```

**注意事项**:
- 最大返回 200 个节点关系
- 不提供疾病名称时返回全图（可能数据量大）
- 适合用于 ECharts 等可视化库

---

#### 3. 获取疾病详细信息

**接口地址**: `GET /get_ill_info`

**接口描述**: 获取指定疾病的完整信息，包括症状、科室、治疗方法等。

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| ill | string | 是 | 疾病名称（支持模糊匹配） | 感冒 |

**请求示例**:
```
GET /get_ill_info?ill=感冒
```

**成功响应** (200):
```json
[
  {
    "data": {
      "name": "感冒",
      "source_link": "https://tag.120ask.com/jibing/ganmao.html",
      "symptom": "流鼻涕, 咳嗽, 喉咙痛, 发热, 头痛",
      "department": "内科, 呼吸科",
      "class1": "呼吸系统疾病",
      "class2": "上呼吸道感染",
      "easy_ill_people": "儿童, 老年人, 免疫力低下者",
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

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 疾病名称 |
| source_link | string | 原始数据来源链接 |
| symptom | string | 症状列表（逗号分隔） |
| department | string | 就诊科室（逗号分隔） |
| class1 | string | 一级分类 |
| class2 | string | 二级分类 |
| easy_ill_people | string | 好发人群 |
| cure_method | string | 治疗方法 |
| cure_cost | string | 治疗费用 |
| if_infect | string | 是否传染 |
| ill_proportion | string | 患病比例 |
| cure_rate | string | 治愈率 |
| healing_cycle | string | 治疗周期 |

**失败响应**:

400 - 参数缺失:
```json
{
  "error": "Disease name is required"
}
```

400 - 验证失败:
```json
{
  "error": "Disease name contains invalid characters"
}
```

500 - 服务器错误:
```json
{
  "error": "Failed to retrieve disease information"
}
```

**注意事项**:
- 支持模糊匹配（包含查询）
- 可能返回多个匹配的疾病
- 无数据的字段显示为 "暂无信息"
- 返回列表格式，即使只有一个结果

---

#### 4. 获取统计分析数据

**接口地址**: `GET /get_analysis_data`

**接口描述**: 获取知识图谱的统计分析数据，用于数据看板展示。

**请求参数**: 无

**请求示例**:
```
GET /get_analysis_data
```

**成功响应** (200):
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
    {"name": "消化系统疾病", "value": 65},
    {"name": "心血管疾病", "value": 55},
    {"name": "神经系统疾病", "value": 45},
    {"name": "内分泌疾病", "value": 40}
  ],
  "infectious_counts": [
    {"name": "是", "value": 120},
    {"name": "否", "value": 380}
  ],
  "healing_cycle_counts": [
    {"name": "7-10天", "value": 150},
    {"name": "1-3个月", "value": 100},
    {"name": "3-6个月", "value": 80},
    {"name": "6个月以上", "value": 50},
    {"name": "1-2周", "value": 120}
  ]
}
```

**字段说明**:

- `node_counts`: 各类节点数量统计
- `class1_ill_counts`: 一级分类下的疾病数量（Top 10）
- `infectious_counts`: 传染病与非传染病数量
- `healing_cycle_counts`: 治疗周期分布（Top 10）

**失败响应**:

500 - 服务器错误:
```json
{
  "node_counts": [],
  "class1_ill_counts": [],
  "infectious_counts": [],
  "healing_cycle_counts": []
}
```

**注意事项**:
- 数据实时从 Neo4j 查询
- 适合用于图表展示（饼图、柱状图等）
- 空数据返回空数组而非错误

---

### 用户管理模块

#### 5. 用户注册

**接口地址**: `POST /register`

**接口描述**: 新用户注册接口。

**Content-Type**: `application/json`

**请求体**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| username | string | 是 | 用户名（3-50 字符，支持中文） | testuser |
| password | string | 是 | 密码（8-128 字符，需包含大小写字母和数字） | Password123 |
| age | integer | 是 | 年龄（1-150） | 25 |
| gender | string | 是 | 性别（male/female/other/男/女/其他） | male |

**请求示例**:
```json
POST /register
Content-Type: application/json

{
  "username": "testuser",
  "password": "Password123",
  "age": 25,
  "gender": "male"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "Registration successful"
}
```

**失败响应**:

400 - 参数缺失:
```json
{
  "success": false,
  "message": "Request body is required"
}
```

400 - 验证失败:
```json
{
  "success": false,
  "message": "Username must be between 3 and 50 characters"
}
```

400 - 用户名已存在:
```json
{
  "success": false,
  "message": "User already exists",
  "error": "This username is already taken"
}
```

500 - 服务器错误:
```json
{
  "success": false,
  "message": "Registration failed",
  "error": "Database connection error"
}
```

**验证规则**:

- **用户名**: 
  - 长度：3-50 字符
  - 允许：字母、数字、下划线、中文
  - 必须唯一

- **密码**:
  - 长度：8-128 字符
  - 必须包含：大写字母、小写字母、数字
  - 使用 bcrypt 加密存储

- **年龄**: 1-150 整数

- **性别**: male/female/other/男/女/其他

**注意事项**:
- 密码自动 bcrypt 加密
- 用户名唯一性检查
- 记录注册时间（自动）

---

#### 6. 用户登录

**接口地址**: `POST /login`

**接口描述**: 用户登录接口，返回 JWT Token。

**Content-Type**: `application/json`

**请求体**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| username | string | 是 | 用户名 | testuser |
| password | string | 是 | 密码 | Password123 |

**请求示例**:
```json
POST /login
Content-Type: application/json

{
  "username": "testuser",
  "password": "Password123"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "testuser",
    "age": 25,
    "gender": "male",
    "create_time": "2024-01-01T12:00:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InRlc3R1c2VyIiwiZXhwIjoxNzA2ODQxNjAwfQ.abc123..."
  }
}
```

**字段说明**:

- `id`: 用户 ID
- `username`: 用户名
- `age`: 年龄
- `gender`: 性别
- `create_time`: 注册时间
- `token`: JWT Token（用于后续认证）

**失败响应**:

400 - 参数缺失:
```json
{
  "success": false,
  "message": "Request body is required"
}
```

401 - 认证失败:
```json
{
  "success": false,
  "error": "Invalid username or password"
}
```

500 - 服务器错误:
```json
{
  "success": false,
  "message": "Login failed",
  "error": "Database error"
}
```

**注意事项**:
- Token 有效期 1 小时
- 密码验证使用 bcrypt
- 不返回密码字段
- 记录登录日志

---

#### 7. 管理员登录

**接口地址**: `POST /Adminlogin`

**接口描述**: 管理员登录接口。

**Content-Type**: `application/json`

**请求体**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| username | string | 是 | 管理员账号 | admin |
| password | string | 是 | 管理员密码 | admin |

**请求示例**:
```json
POST /Adminlogin
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "user": {
    "id": 1,
    "adminname": "admin",
    "create_time": "2024-01-01T12:00:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "is_admin": true
  }
}
```

**失败响应**:

401 - 认证失败:
```json
{
  "success": false,
  "error": "Invalid username or password"
}
```

**注意事项**:
- 默认管理员账号：admin/admin
- **生产环境务必修改默认密码**
- 返回 `is_admin: true` 标识

---

#### 8. 获取所有用户

**接口地址**: `GET /get_users`

**接口描述**: 获取所有用户列表（管理员功能）。

**请求参数**: 无

**请求示例**:
```
GET /get_users
```

**成功响应** (200):
```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "username": "testuser",
      "age": 25,
      "gender": "male",
      "create_time": "2024-01-01T12:00:00"
    },
    {
      "id": 2,
      "username": "user2",
      "age": 30,
      "gender": "female",
      "create_time": "2024-01-02T10:00:00"
    }
  ]
}
```

**失败响应**:

500 - 服务器错误:
```json
{
  "success": false,
  "message": "Failed to retrieve users",
  "error": "Database error"
}
```

**注意事项**:
- 不返回密码字段
- 建议添加分页（当前未实现）
- 应添加权限验证（当前未实现）

---

#### 9. 添加用户

**接口地址**: `POST /add_users`

**接口描述**: 管理员添加用户接口。

**Content-Type**: `application/json`

**请求体**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| username | string | 是 | 用户名 | newuser |
| password | string | 是 | 密码 | Password123 |
| age | integer | 是 | 年龄 | 30 |
| gender | string | 是 | 性别 | female |

**请求示例**:
```json
POST /add_users
Content-Type: application/json

{
  "username": "newuser",
  "password": "Password123",
  "age": 30,
  "gender": "female"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "Insert successful"
}
```

**失败响应**:

500 - 服务器错误:
```json
{
  "success": false,
  "message": "Insert failed",
  "error": "Duplicate entry for username"
}
```

**注意事项**:
- 与 `/register` 类似，但不进行输入验证
- 应添加管理员权限验证

---

#### 10. 更新用户信息

**接口地址**: `POST /update_user`

**接口描述**: 更新用户信息。

**Content-Type**: `application/json`

**请求体**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| id | integer | 是 | 用户 ID | 1 |
| username | string | 是 | 用户名 | updateduser |
| password | string | 否 | 新密码（不提供则不修改） | NewPass123 |
| age | integer | 是 | 年龄 | 26 |
| gender | string | 是 | 性别 | male |

**请求示例**:
```json
POST /update_user
Content-Type: application/json

{
  "id": 1,
  "username": "updateduser",
  "password": "NewPass123",
  "age": 26,
  "gender": "male"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "Update successful"
}
```

**失败响应**:

500 - 服务器错误:
```json
{
  "success": false,
  "message": "Update failed",
  "error": "User not found"
}
```

**注意事项**:
- 密码可选，不提供则保持原密码
- 密码会自动 bcrypt 加密
- 应添加权限验证（只能修改自己或管理员可修改任何人）

---

#### 11. 删除用户

**接口地址**: `POST /delete_user`

**接口描述**: 删除用户。

**Content-Type**: `application/json`

**请求体**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| id | integer | 是 | 用户 ID | 1 |

**请求示例**:
```json
POST /delete_user
Content-Type: application/json

{
  "id": 1
}
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "Delete successful"
}
```

**失败响应**:

400 - 参数缺失:
```json
{
  "success": false,
  "message": "User ID is required"
}
```

500 - 服务器错误:
```json
{
  "success": false,
  "message": "Delete failed",
  "error": "User not found"
}
```

**注意事项**:
- 删除操作不可恢复
- 应添加权限验证
- 建议实现软删除（标记删除而非物理删除）

---

### 系统模块

#### 12. 健康检查

**接口地址**: `GET /health`

**接口描述**: 服务健康状态检查接口，用于监控和运维。

**请求参数**: 无

**请求示例**:
```
GET /health
```

**成功响应** (200):
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

**字段说明**:

- `status`: 整体服务状态（healthy/unhealthy）
- `services`: 各子服务状态
  - `neo4j`: Neo4j 数据库连接状态
  - `flask`: Flask 应用状态
- `timestamp`: 检查时间戳

**失败响应** (500):
```json
{
  "status": "unhealthy",
  "error": "Neo4j connection failed"
}
```

**注意事项**:
- 可用于负载均衡器健康检查
- 可用于监控系统告警
- 定期检查各依赖服务状态

---

#### 13. 前端页面

**接口地址**: `GET /`

**接口描述**: 返回前端静态页面（index.html）。

**请求参数**: 无

**请求示例**:
```
GET /
```

**响应**: HTML 页面

**注意事项**:
- 静态文件位于 `./dist` 目录
- 需要前端构建后部署到此目录

---

## 速率限制

### 默认限制
- **全局**: 200 次/天，50 次/小时
- **基于**: IP 地址

### 特殊接口限制

| 接口 | 限制 | 说明 |
|------|------|------|
| POST /question | 30 次/分钟 | 防止滥用 AI 接口 |
| 其他接口 | 50 次/小时 | 默认限制 |

### 速率限制响应

当触发速率限制时，返回 429 状态码：

```json
{
  "error": "Rate limit exceeded. Try again in 30 seconds."
}
```

**Header 信息**:
```
Retry-After: 30
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706841630
```

### Redis 配置

如需分布式限流，需配置 Redis：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

---

## 最佳实践

### 1. 错误处理

始终检查响应的 HTTP 状态码和 `success` 字段：

```javascript
// JavaScript 示例
async function callAPI(endpoint, params) {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}?${params}`);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'Request failed');
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

### 2. Token 管理

妥善保存和使用 JWT Token：

```javascript
// 登录获取 Token
const loginResponse = await fetch(`${BASE_URL}/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});
const { user } = await loginResponse.json();
localStorage.setItem('token', user.token);

// 使用 Token 调用接口
const response = await fetch(`${BASE_URL}/protected`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

### 3. 输入验证

前端也应进行输入验证，减轻后端压力：

```javascript
function validateQuestion(question) {
  if (!question || question.length < 2) {
    return '问题至少需要 2 个字符';
  }
  if (question.length > 500) {
    return '问题不能超过 500 个字符';
  }
  return null;
}
```

### 4. 错误重试

对于网络错误或 5xx 错误，实现指数退避重试：

```javascript
async function retryableFetch(url, options, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return response;
      
      if (response.status >= 500 && i < retries - 1) {
        await new Promise(resolve => 
          setTimeout(resolve, Math.pow(2, i) * 1000)
        );
        continue;
      }
      
      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      if (i === retries - 1) throw error;
    }
  }
}
```

### 5. 缓存策略

对不常变化的数据实施缓存：

```javascript
// 缓存疾病信息 1 小时
const cache = new Map();
const CACHE_TTL = 3600000; // 1 小时

async function getDiseaseInfo(illName) {
  const cacheKey = `disease_${illName}`;
  const cached = cache.get(cacheKey);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  
  const response = await fetch(`${BASE_URL}/get_ill_info?ill=${illName}`);
  const data = await response.json();
  
  cache.set(cacheKey, {
    data,
    timestamp: Date.now()
  });
  
  return data;
}
```

### 6. 安全性建议

- **HTTPS**: 生产环境务必使用 HTTPS
- **Token 安全**: 不要在 URL 中传递 Token
- **密码强度**: 强制要求强密码
- **CORS**: 配置合适的 CORS 策略
- **敏感信息**: 不要在前端暴露 API Key

### 7. 性能优化

- **批量请求**: 合并多个小请求
- **懒加载**: 按需加载图谱数据
- **分页**: 大数据集实现分页
- **压缩**: 启用 Gzip 压缩

---

## 附录

### A. 知识图谱 Schema

#### 节点类型

| 标签 | 属性 | 说明 |
|------|------|------|
| ill | name, source_link | 疾病 |
| symptom | name | 症状 |
| department | name | 科室 |
| class1 | name | 一级分类 |
| class2 | name | 二级分类 |
| easy_ill_people | name | 好发人群 |
| cure_method | name | 治疗方法 |
| cure_cost | name | 治疗费用 |
| if_infect | name | 是否传染 |
| ill_proportion | name | 患病比例 |
| cure_rate | name | 治愈率 |
| healing_cycle | name | 治疗周期 |

#### 关系类型

```
(:ill)-[:has_symptom]->(:symptom)
(:ill)-[:should_see]->(:department)
(:ill)-[:belongs_to_class1]->(:class1)
(:ill)-[:belongs_to_class2]->(:class2)
(:ill)-[:affects_people]->(:easy_ill_people)
(:ill)-[:treated_by]->(:cure_method)
(:ill)-[:costs]->(:cure_cost)
(:ill)-[:is_infectious]->(:if_infect)
(:ill)-[:has_proportion]->(:ill_proportion)
(:ill)-[:has_cure_rate]->(:cure_rate)
(:ill)-[:has_healing_cycle]->(:healing_cycle)
```

### B. 常见问题 (FAQ)

#### Q1: 为什么问答接口响应慢？

**A**: 首次查询需要 LLM 生成 Cypher 语句，可能需要 2-5 秒。后续相同问题会更快。建议：
- 实现前端 loading 状态
- 缓存常见问题答案
- 优化 Neo4j 索引

#### Q2: Token 过期如何处理？

**A**: 捕获 401 错误，引导用户重新登录：

```javascript
if (response.status === 401) {
  localStorage.removeItem('token');
  window.location.href = '/login';
}
```

#### Q3: 如何测试 API？

**A**: 使用以下工具：
- **Postman**: 图形化 API 测试
- **curl**: 命令行测试
- **Swagger/OpenAPI**: API 文档和测试（待集成）

#### Q4: 如何增加速率限制？

**A**: 修改 `app.py` 中的配置：

```python
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
)
```

#### Q5: 知识图谱数据如何更新？

**A**: 
1. 运行爬虫获取新数据：`python crawler.py`
2. 导入到 Neo4j：`python import_to_neo4j.py`
3. 重启服务使更改生效

### C. 更新日志

#### v1.0 (2026-04-13)
- ✨ 初始版本发布
- ✨ 实现医疗问答接口
- ✨ 实现知识图谱查询
- ✨ 实现用户管理系统
- ✨ 添加 JWT 认证
- ✨ 添加速率限制
- ✨ 完善输入验证

### D. 联系方式

- **项目地址**: [GitHub Repository]
- **问题反馈**: [Issues]
- **邮箱**: [your-email@example.com]

---

**文档版本**: v1.0  
**最后更新**: 2026-04-13  
**维护者**: Medical QA Team
