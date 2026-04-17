# 医疗智能问答系统 - 后端API接口文档

## 重要提示

**所有用户相关接口均已添加 `/api` 前缀！**

例如：
- ✅ 正确：`POST /api/send_verification_code`
- ❌ 错误：`POST /send_verification_code`

## 目录
- [基础信息](#基础信息)
- [认证相关接口](#认证相关接口)
- [用户管理接口](#用户管理接口)
- [医疗问答接口](#医疗问答接口)
- [疾病信息查询接口](#疾病信息查询接口)
- [对话历史管理接口](#对话历史管理接口)
- [数据分析接口](#数据分析接口)
- [系统健康检查](#系统健康检查)

---

## 基础信息

### 服务器地址
```
开发环境: http://localhost:5001
生产环境: https://your-domain.com
```

### 通用响应格式

**成功响应:**
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

**失败响应:**
```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": "详细错误信息（仅开发环境）"
}
```

### 认证方式
需要在请求头中携带JWT Token：
```
Authorization: Bearer <your_jwt_token>
```

---

## 认证相关接口

### 1. 发送验证码

**接口地址:** `POST /api/send_verification_code`

**请求示例:**
```bash
curl -X POST http://localhost:5001/api/send_verification_code \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "13800138000"}'
```

**请求参数:**
```json
{
  "phone_number": "13800138000"
}
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| phone_number | string | 是 | 手机号码（支持+86前缀） |

**返回示例:**
```json
{
  "success": true,
  "message": "验证码发送成功，请注意查收"
}
```

**⚠️ 重要：查看验证码方式**

由于当前使用的是**模拟短信服务**（开发环境），验证码不会真的发送到手机，而是打印在：

1. **控制台输出**：
```
INFO - 📱 模拟发送验证码 → 13800138000，验证码：123456
```

2. **日志文件**：`logs/app.log`

生产环境可替换为真实的阿里云短信服务。

**错误示例:**
```json
{
  "success": false,
  "message": "手机号格式不正确",
  "error_code": "VALIDATION_ERROR"
}
```

---

### 2. 验证验证码

**接口地址:** `POST /api/check_verification_code`

**请求示例:**
```bash
curl -X POST http://localhost:5001/api/check_verification_code \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "13800138000", "code": "123456"}'
```

**请求参数:**
```json
{
  "phone_number": "13800138000",
  "code": "123456"
}
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| phone_number | string | 是 | 手机号码 |
| code | string | 是 | 6位验证码 |

**返回示例:**
```json
{
  "success": true,
  "message": "验证成功"
}
```

**错误示例:**
```json
{
  "success": false,
  "message": "验证码已过期",
  "error_code": "CODE_EXPIRED"
}
```

---

### 3. 用户注册

**接口地址:** `POST /api/register`

**请求示例:**
```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "张三",
    "password": "Password123",
    "phone_number": "13800138000",
    "verification_code": "123456",
    "age": 25,
    "gender": "男"
  }'
```

**请求参数:**
```json
{
  "username": "张三",
  "password": "Password123",
  "phone_number": "13800138000",
  "verification_code": "123456",
  "age": 25,
  "gender": "男"
}
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名（3-50字符，支持中文） |
| password | string | 是 | 密码（至少8位，包含大小写字母和数字） |
| phone_number | string | 是 | 手机号码 |
| verification_code | string | 是 | 短信验证码 |
| age | integer | 是 | 年龄（1-150） |
| gender | string | 是 | 性别（男/女/其他/male/female/other） |

**返回示例:**
```json
{
  "success": true,
  "message": "注册成功"
}
```

**错误示例:**
```json
{
  "success": false,
  "message": "该手机号已被注册",
  "error_code": "PHONE_EXISTS"
}
```

---

### 4. 用户登录

**接口地址:** `POST /api/login`

**请求示例:**
```bash
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "张三",
    "password": "Password123",
    "phone_number": "13800138000",
    "verification_code": "123456"
  }'
```

**请求参数:**
```json
{
  "username": "张三",
  "password": "Password123",
  "phone_number": "13800138000",
  "verification_code": "123456"
}
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| phone_number | string | 是 | 手机号码 |
| verification_code | string | 是 | 短信验证码 |

**返回示例:**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "user": {
      "id": 1,
      "username": "张三",
      "phone_number": "13800138000",
      "age": 25,
      "gender": "男",
      "create_time": "2024-01-01 12:00:00",
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
}
```

**错误示例:**
```json
{
  "success": false,
  "message": "用户名、手机号或密码错误",
  "error_code": "INVALID_CREDENTIALS"
}
```

---

### 5. 管理员登录

**接口地址:** `POST /api/Adminlogin`

**请求参数:**
```json
{
  "username": "admin",
  "password": "AdminPass123"
}
```

**返回示例:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "adminname": "admin",
    "create_time": "2024-01-01 12:00:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "is_admin": true
  }
}
```

---

## 用户管理接口

### 6. 获取用户列表

**接口地址:** `GET /api/get_users`

**请求头:**
```
Authorization: Bearer <admin_token>
```

**返回示例:**
```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "username": "张三",
      "age": 25,
      "gender": "男",
      "create_time": "2024-01-01 12:00:00"
    },
    {
      "id": 2,
      "username": "李四",
      "age": 30,
      "gender": "女",
      "create_time": "2024-01-02 14:30:00"
    }
  ]
}
```

---

### 7. 添加用户（管理员）

**接口地址:** `POST /api/add_users`

**请求头:**
```
Authorization: Bearer <admin_token>
```

**请求示例:**
```bash
curl -X POST http://localhost:5001/api/add_users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "username": "王五",
    "password": "Password123",
    "phone_number": "13900139000",
    "gender": "男",
    "age": 28
  }'
```

**请求参数:**
```json
{
  "username": "王五",
  "password": "Password123",
  "phone_number": "13900139000",
  "gender": "男",
  "age": 28
}
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名（3-50字符，支持中文） |
| password | string | 是 | 密码（至少8位，包含大小写字母和数字） |
| phone_number | string | 是 | 手机号码 |
| gender | string | 是 | 性别（男/女/其他/male/female/other） |
| age | integer | 否 | 年龄（1-150，可不填） |

**返回示例:**
```json
{
  "success": true,
  "message": "添加成功"
}
```

**错误示例:**
```json
{
  "success": false,
  "message": "用户名已存在",
  "error_code": "USER_EXISTS"
}
```

或者：
```json
{
  "success": false,
  "message": "该手机号已被注册",
  "error_code": "PHONE_EXISTS"
}
```

---

### 8. 更新用户信息

**接口地址:** `POST /api/update_user`

**请求参数:**
```json
{
  "id": 1,
  "username": "张三丰",
  "password": "NewPassword123",
  "age": 26,
  "gender": "男"
}
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 用户ID |
| username | string | 是 | 新用户名 |
| password | string | 否 | 新密码（不提供则不修改） |
| age | integer | 是 | 新年龄 |
| gender | string | 是 | 新性别 |

**返回示例:**
```json
{
  "success": true,
  "message": "更新成功"
}
```

---

### 9. 删除用户

**接口地址:** `POST /api/delete_user`

**请求参数:**
```json
{
  "id": 1
}
```

**返回示例:**
```json
{
  "success": true,
  "message": "删除成功"
}
```

---

### 10. 批量删除用户

**接口地址:** `POST /api/batch_delete_users`

**请求参数:**
```json
{
  "user_ids": [1, 2, 3]
}
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_ids | array | 是 | 用户ID数组（最多100个） |

**返回示例:**
```json
{
  "success": true,
  "message": "已删除 3 个用户",
  "deleted_count": 3
}
```

---

## 医疗问答接口

### 11. 智能问答

**接口地址:** `GET /question`

**限流:** 30次/分钟

**请求参数:**
```
GET /question?question=感冒的症状是什么？&conversation_id=unique-id-123
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| question | string | 是 | 医疗问题（2-500字符） |
| conversation_id | string | 否 | 会话ID（用于保存对话历史） |

**请求头（可选）:**
```
Authorization: Bearer <token>
```

**返回示例:**
```json
{
  "answer": "感冒的常见症状包括：\n\n1. 鼻塞、流鼻涕\n2. 喉咙痛\n3. 咳嗽\n4. 轻微发热\n5. 头痛\n6. 全身乏力\n\n建议您多休息，多喝水。如果症状持续加重或出现高烧，请及时就医。",
  "source": "knowledge_graph",
  "confidence": "high"
}
```

**返回字段说明:**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| answer | string | AI回答内容 |
| source | string | 答案来源（knowledge_graph/llm_fallback/llm_error_fallback） |
| confidence | string | 置信度（high/medium/low） |

**错误示例:**
```json
{
  "error": "问题不能为空"
}
```

---

### 12. 搜索建议

**接口地址:** `GET /search_suggestions`

**限流:** 60次/分钟

**请求参数:**
```
GET /search_suggestions?keyword=感冒&limit=10
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keyword | string | 是 | 搜索关键词（1-50字符） |
| limit | integer | 否 | 返回数量（默认10，最大20） |

**返回示例:**
```json
{
  "success": true,
  "suggestions": [
    "感冒",
    "感冒咳嗽",
    "流行性感冒",
    "普通感冒"
  ],
  "count": 4
}
```

---

## 疾病信息查询接口

### 13. 获取疾病详细信息

**接口地址:** `GET /get_ill_info`

**请求参数:**
```
GET /get_ill_info?ill=感冒
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ill | string | 是 | 疾病名称 |

**返回示例:**
```json
[
  {
    "data": {
      "name": "感冒",
      "source_link": "https://tag.120ask.com/jibing/ganmao.html",
      "symptom": "鼻塞, 流鼻涕, 喉咙痛, 咳嗽, 发热",
      "department": "呼吸内科, 内科",
      "class1": "呼吸系统疾病",
      "class2": "上呼吸道感染",
      "easy_ill_people": "所有人群",
      "cure_method": "对症治疗, 休息, 多饮水",
      "cure_cost": "100-500元",
      "if_infect": "是",
      "ill_proportion": "常见",
      "cure_rate": "95%",
      "healing_cycle": "5-7天"
    }
  }
]
```

**错误示例:**
```json
{
  "error": "疾病名称不能为空"
}
```

---

### 14. 获取知识图谱数据

**接口地址:** `GET /get_graph`

**请求参数:**
```
GET /get_graph?ill=感冒
```

**参数说明:**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ill | string | 否 | 疾病名称（不提供则返回全部图谱） |

**返回示例:**
```json
{
  "graph_data": [
    {
      "name": "感冒",
      "symbolSize": 50,
      "category": "ill"
    },
    {
      "name": "鼻塞",
      "symbolSize": 50,
      "category": "symptom"
    },
    {
      "name": "呼吸内科",
      "symbolSize": 50,
      "category": "department"
    }
  ],
  "links": [
    {
      "source": "感冒",
      "target": "鼻塞",
      "name": "has_symptom"
    },
    {
      "source": "感冒",
      "target": "呼吸内科",
      "name": "should_see"
    }
  ],
  "labels": [
    {"name": "ill"},
    {"name": "symptom"},
    {"name": "department"}
  ],
  "stats": {
    "node_count": 15,
    "link_count": 20,
    "category_count": 5
  }
}
```

**返回字段说明:**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| graph_data | array | 节点数据（name: 节点名称, symbolSize: 节点大小, category: 节点类型） |
| links | array | 关系数据（source: 源节点, target: 目标节点, name: 关系类型） |
| labels | array | 节点类型列表 |
| stats | object | 统计信息（node_count: 节点数, link_count: 关系数, category_count: 类型数） |

---

## 对话历史管理接口

### 15. 获取对话列表

**接口地址:** `GET /api/get_conversations`

**请求头:**
```
Authorization: Bearer <token>
```

**返回示例:**
```json
{
  "success": true,
  "conversations": [
    {
      "conversation_id": "conv-20240101-001",
      "preview": "感冒的常见症状包括鼻塞、流鼻涕、喉咙痛等...",
      "last_update": "2024-01-01 15:30:00",
      "qa_count": 5
    },
    {
      "conversation_id": "conv-20240102-002",
      "preview": "糖尿病是一种慢性代谢性疾病...",
      "last_update": "2024-01-02 10:20:00",
      "qa_count": 3
    }
  ]
}
```

**返回字段说明:**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| conversation_id | string | 会话ID |
| preview | string | 最后一条AI回答预览（最多100字符） |
| last_update | string | 最后更新时间 |
| qa_count | integer | 该会话中的问答对数量 |

---

### 16. 获取对话详情

**接口地址:** `GET /api/get_conversation_detail`

**请求头:**
```
Authorization: Bearer <token>
```

**请求参数:**
```
GET /api/get_conversation_detail?conversation_id=conv-20240101-001
```

**返回示例:**
```json
{
  "success": true,
  "messages": [
    {
      "role": "user",
      "username": "张三",
      "content": "感冒的症状是什么？",
      "create_time": "2024-01-01 15:20:00"
    },
    {
      "role": "assistant",
      "content": "感冒的常见症状包括：\n\n1. 鼻塞、流鼻涕\n2. 喉咙痛\n3. 咳嗽...",
      "create_time": "2024-01-01 15:20:05"
    },
    {
      "role": "user",
      "username": "张三",
      "content": "需要吃什么药？",
      "create_time": "2024-01-01 15:25:00"
    },
    {
      "role": "assistant",
      "content": "感冒通常是病毒感染，一般不需要抗生素...",
      "create_time": "2024-01-01 15:25:08"
    }
  ],
  "conversation_id": "conv-20240101-001"
}
```

**返回字段说明:**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| messages | array | 消息列表 |
| messages[].role | string | 角色（user/assistant） |
| messages[].username | string | 用户名（仅user角色） |
| messages[].content | string | 消息内容 |
| messages[].create_time | string | 创建时间 |

---

### 17. 删除对话

**接口地址:** `POST /api/delete_conversation`

**请求头:**
```
Authorization: Bearer <token>
```

**请求参数:**
```json
{
  "conversation_id": "conv-20240101-001"
}
```

**返回示例:**
```json
{
  "success": true,
  "message": "对话删除成功"
}
```

**错误示例:**
```json
{
  "success": false,
  "message": "对话不存在"
}
```

---

### 18. 清空所有对话

**接口地址:** `POST /api/clear_all_conversations`

**请求头:**
```
Authorization: Bearer <token>
```

**返回示例:**
```json
{
  "success": true,
  "message": "已清空 10 个对话",
  "deleted_count": 10
}
```

---

## 数据分析接口

### 19. 获取分析数据

**接口地址:** `GET /get_analysis_data`

**返回示例:**
```json
{
  "node_counts": [
    {"name": "疾病", "value": 1250},
    {"name": "症状", "value": 3500},
    {"name": "科室", "value": 85},
    {"name": "治疗方法", "value": 420}
  ],
  "class1_ill_counts": [
    {"name": "呼吸系统疾病", "value": 180},
    {"name": "消化系统疾病", "value": 150},
    {"name": "心血管疾病", "value": 120},
    {"name": "神经系统疾病", "value": 95}
  ],
  "infectious_counts": [
    {"name": "是", "value": 320},
    {"name": "否", "value": 930}
  ],
  "healing_cycle_counts": [
    {"name": "1-2周", "value": 450},
    {"name": "3-4周", "value": 280},
    {"name": "1-3个月", "value": 180},
    {"name": "长期治疗", "value": 120}
  ]
}
```

**返回字段说明:**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| node_counts | array | 各类节点数量统计 |
| class1_ill_counts | array | 一级分类疾病数量（Top 10） |
| infectious_counts | array | 传染性疾病统计 |
| healing_cycle_counts | array | 治疗周期分布（Top 10） |

---

## 系统健康检查

### 20. 健康检查

**接口地址:** `GET /health`

**返回示例:**
```json
{
  "status": "healthy",
  "services": {
    "neo4j": "healthy",
    "redis": "healthy",
    "flask": "healthy"
  },
  "timestamp": "2024-01-01 12:00:00"
}
```

**返回字段说明:**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| status | string | 整体状态（healthy/degraded/unhealthy） |
| services | object | 各服务状态 |
| services.neo4j | string | Neo4j数据库状态 |
| services.redis | string | Redis缓存状态 |
| services.flask | string | Flask应用状态 |
| timestamp | string | 检查时间戳 |

---

### 21. 清除缓存（调试用）

**接口地址:** `GET /clear_cache` 或 `POST /clear_cache`

**返回示例:**
```json
{
  "success": true,
  "message": "缓存已清除"
}
```

---

## 错误码说明

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| VALIDATION_ERROR | 参数验证失败 | 400 |
| USER_EXISTS | 用户已存在 | 400 |
| PHONE_EXISTS | 手机号已被注册 | 400 |
| CODE_EXPIRED | 验证码已过期 | 400 |
| INVALID_CODE | 验证码错误 | 400 |
| INVALID_CREDENTIALS | 用户名或密码错误 | 401 |
| UNAUTHORIZED | 未授权访问 | 401 |
| FORBIDDEN | 禁止访问 | 403 |
| NOT_FOUND | 资源不存在 | 404 |
| RATE_LIMIT_EXCEEDED | 请求频率超限 | 429 |
| INTERNAL_ERROR | 服务器内部错误 | 500 |
| SMS_SEND_FAILED | 短信发送失败 | 500 |

---

## 前端开发建议

### 1. 认证流程
```javascript
// 1. 发送验证码
const sendCode = async (phoneNumber) => {
  const response = await fetch('http://localhost:5001/api/send_verification_code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber })
  });
  return response.json();
};

// 2. 注册/登录
const login = async (credentials) => {
  const response = await fetch('http://localhost:5001/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials)
  });
  const data = await response.json();
  
  if (data.success) {
    // 保存token到localStorage
    localStorage.setItem('token', data.data.user.token);
    localStorage.setItem('userInfo', JSON.stringify(data.data.user));
  }
  
  return data;
};

// 3. 在后续请求中携带token
const fetchData = async (url) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`http://localhost:5001${url}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};
```

### 2. 问答功能
```javascript
// 发起医疗问答
const askQuestion = async (question, conversationId) => {
  const url = `http://localhost:5001/question?question=${encodeURIComponent(question)}&conversation_id=${conversationId}`;
  const token = localStorage.getItem('token');
  
  const response = await fetch(url, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  });
  
  return response.json();
};

// 获取搜索建议（防抖处理）
const getSearchSuggestions = async (keyword) => {
  const response = await fetch(`http://localhost:5001/search_suggestions?keyword=${encodeURIComponent(keyword)}&limit=10`);
  return response.json();
};
```

### 3. 对话历史
```javascript
// 获取对话列表
const getConversations = async () => {
  const token = localStorage.getItem('token');
  const response = await fetch('http://localhost:5001/api/get_conversations', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};

// 获取对话详情
const getConversationDetail = async (conversationId) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`http://localhost:5001/api/get_conversation_detail?conversation_id=${conversationId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};
```

### 4. 知识图谱可视化
```javascript
// 获取图谱数据（可用于ECharts等可视化库）
const getGraphData = async (diseaseName) => {
  const url = diseaseName 
    ? `http://localhost:5001/get_graph?ill=${encodeURIComponent(diseaseName)}`
    : 'http://localhost:5001/get_graph';
  
  const response = await fetch(url);
  return response.json();
};

// ECharts配置示例
const option = {
  series: [{
    type: 'graph',
    layout: 'force',
    data: graphData.graph_data,
    links: graphData.links,
    categories: graphData.labels,
    roam: true,
    label: { show: true },
    force: { repulsion: 100 }
  }]
};
```

---

## 注意事项

1. **API前缀**: 
   - ✅ 所有用户相关接口必须使用 `/api` 前缀（如 `/api/login`）
   - ❌ 不要省略 `/api` 前缀，否则会返回 405 错误
   - ℹ️ 医疗问答和图谱接口不需要 `/api` 前缀（如 `/question`, `/get_graph`）

2. **Token有效期**: JWT Token有效期为7天，过期后需重新登录
3. **限流策略**: 
   - 问答接口：30次/分钟
   - 搜索建议：60次/分钟
   - 全局默认：200次/天，50次/小时
4. **缓存机制**: 疾病信息和图谱数据有缓存（1-2小时），可提高响应速度
5. **跨域支持**: 已配置CORS，支持跨域请求
6. **验证码查看**: 开发环境下验证码打印在控制台和日志文件中，不会真实发送短信
7. **安全建议**: 
   - 生产环境务必使用HTTPS
   - 不要在前端代码中硬编码敏感信息
   - Token应安全存储（建议使用httpOnly cookie）

---

## 联系方式

如有问题，请联系后端开发团队。
