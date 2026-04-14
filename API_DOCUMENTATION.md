# 医疗问答系统 - 前端 API 调用文档

**版本**: v2.0  
**基础 URL**: `http://127.0.0.1:5001`  
**最后更新**: 2026-04-14  
**适用对象**: 前端开发人员

---

## 📋 目录

- [快速开始](#快速开始)
- [认证机制](#认证机制)
- [核心接口](#核心接口)
  - [用户认证](#用户认证)
  - [智能问答（含自动保存）](#智能问答)
  - [对话历史管理](#对话历史管理)
- [完整示例](#完整示例)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 登录获取 Token

```javascript
const loginResponse = await fetch('http://127.0.0.1:5001/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'your_username',
    password: 'your_password'
  })
});

const loginData = await loginResponse.json();
const token = loginData.user.token;

// 保存 token
localStorage.setItem('token', token);
```

### 2. 发送问题（自动保存对话）

```javascript
// 生成唯一的会话 ID
const conversationId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

// 发送问题
const question = '感冒有哪些症状？';
const response = await fetch(
  `http://127.0.0.1:5001/question?question=${encodeURIComponent(question)}&conversation_id=${conversationId}`,
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

const data = await response.json();
console.log('AI回答:', data.answer);
// ✅ 问题和回答已自动保存到数据库
```

### 3. 获取历史对话列表

```javascript
const convResponse = await fetch('http://127.0.0.1:5001/get_conversations', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const convData = await convResponse.json();
console.log('对话列表:', convData.conversations);
```

---

## 🔐 认证机制

### JWT Token 认证

所有需要用户身份的接口都需要在请求头中携带 Token。

**获取 Token**：
- 调用 `/login` 或 `/Adminlogin` 接口
- Token 有效期：3600 秒（1 小时）

**使用 Token**：
```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

**Token 过期处理**：
```javascript
if (response.status === 401) {
  // Token 过期，跳转到登录页
  localStorage.removeItem('token');
  window.location.href = '/login';
}
```

---

## 📡 核心接口

### 用户认证

#### 1. 用户登录

**接口**: `POST /login`

**请求体**:
```json
{
  "username": "张三",
  "password": "password123"
}
```

**响应**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "张三",
    "age": 25,
    "gender": "male",
    "create_time": "2026-04-14 10:00:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**前端使用**:
```javascript
async function login(username, password) {
  const response = await fetch('http://127.0.0.1:5001/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  if (data.success) {
    localStorage.setItem('token', data.user.token);
    localStorage.setItem('username', data.user.username);
    return data.user;
  } else {
    throw new Error(data.error || '登录失败');
  }
}
```

---

#### 2. 用户注册

**接口**: `POST /register`

**请求体**:
```json
{
  "username": "新用户",
  "password": "password123",
  "age": 25,
  "gender": "male"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Registration successful"
}
```

---

### 智能问答

#### 3. 发送问题（⭐ 核心接口）

**接口**: `GET /question`

**重要**: 此接口会**自动保存**对话到数据库，无需手动调用保存接口！

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 用户的问题 |
| conversation_id | string | 推荐 | 会话ID，用于关联对话历史 |

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
  "answer": "感冒的常见症状包括流鼻涕、咳嗽、喉咙痛等..."
}
```

**前端完整示例**:
```javascript
class ChatService {
  constructor() {
    this.currentConversationId = null;
    this.token = localStorage.getItem('token');
  }
  
  // 生成新的会话 ID
  generateConversationId() {
    return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }
  
  // 发送消息
  async sendMessage(question) {
    // 如果没有当前会话，创建新会话
    if (!this.currentConversationId) {
      this.currentConversationId = this.generateConversationId();
    }
    
    const url = `http://127.0.0.1:5001/question?question=${encodeURIComponent(question)}&conversation_id=${this.currentConversationId}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      });
      
      if (response.status === 401) {
        // Token 过期
        this.handleTokenExpired();
        return null;
      }
      
      const data = await response.json();
      
      if (data.answer) {
        return {
          success: true,
          answer: data.answer,
          conversationId: this.currentConversationId
        };
      } else {
        return {
          success: false,
          error: data.error || '获取回答失败'
        };
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      return {
        success: false,
        error: '网络错误'
      };
    }
  }
  
  // 开始新对话
  startNewConversation() {
    this.currentConversationId = this.generateConversationId();
    return this.currentConversationId;
  }
  
  // 处理 Token 过期
  handleTokenExpired() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    window.location.href = '/login';
  }
}

// 使用示例
const chatService = new ChatService();

// 发送消息
const result = await chatService.sendMessage('肺结核会传染吗？');
if (result.success) {
  console.log('AI回答:', result.answer);
  console.log('会话ID:', result.conversationId);
}
```

**注意事项**:
- ✅ 必须携带 `Authorization` header
- ✅ 建议携带 `conversation_id` 参数以保存对话历史
- ✅ 问题和回答会自动保存到 `conversations` 表
- ❌ **不要**手动调用 `/save_conversation` 接口（已废弃）

---

### 对话历史管理

#### 4. 获取对话列表

**接口**: `GET /get_conversations`

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "conversations": [
    {
      "conversation_id": "conv_1713081234567_abc123",
      "preview": "肺结核具有传染性，主要通过空气传播...",
      "last_update": "2026-04-14 13:50:07",
      "qa_count": 5
    },
    {
      "conversation_id": "conv_1713081200000_xyz789",
      "preview": "感冒通常由病毒引起，症状包括...",
      "last_update": "2026-04-14 12:30:00",
      "qa_count": 3
    }
  ]
}
```

**字段说明**:
- `conversation_id`: 会话唯一标识
- `preview`: 最后一次 AI 回答的预览（最多100字符）
- `last_update`: 最后更新时间
- `qa_count`: 该会话中的问答对数量

**前端使用**:
```javascript
async function loadConversationList() {
  const token = localStorage.getItem('token');
  
  try {
    const response = await fetch('http://127.0.0.1:5001/get_conversations', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      // 渲染侧边栏对话列表
      renderSidebar(data.conversations);
    }
  } catch (error) {
    console.error('加载对话列表失败:', error);
  }
}

function renderSidebar(conversations) {
  const sidebar = document.getElementById('conversation-sidebar');
  sidebar.innerHTML = '';
  
  conversations.forEach(conv => {
    const item = document.createElement('div');
    item.className = 'conversation-item';
    item.innerHTML = `
      <div class="preview">${conv.preview}</div>
      <div class="time">${conv.last_update}</div>
      <div class="count">${conv.qa_count} 条对话</div>
    `;
    item.onclick = () => loadConversationDetail(conv.conversation_id);
    sidebar.appendChild(item);
  });
}
```

---

#### 5. 获取对话详情

**接口**: `GET /get_conversation_detail`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | string | 是 | 会话ID |

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "conversation_id": "conv_1713081234567_abc123",
  "messages": [
    {
      "role": "user",
      "username": "张三",
      "content": "肺结核会传染吗？",
      "create_time": "2026-04-14 13:50:07"
    },
    {
      "role": "assistant",
      "content": "肺结核具有传染性，主要通过空气传播。当患者咳嗽、打喷嚏或说话时，会将含有结核菌的飞沫排到空气中...",
      "create_time": "2026-04-14 13:50:07"
    },
    {
      "role": "user",
      "username": "张三",
      "content": "怎么预防？",
      "create_time": "2026-04-14 13:51:00"
    },
    {
      "role": "assistant",
      "content": "预防肺结核的方法包括：接种卡介苗、保持良好通风、避免与患者密切接触...",
      "create_time": "2026-04-14 13:51:00"
    }
  ]
}
```

**前端使用**:
```javascript
async function loadConversationDetail(conversationId) {
  const token = localStorage.getItem('token');
  
  try {
    const response = await fetch(
      `http://127.0.0.1:5001/get_conversation_detail?conversation_id=${conversationId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    const data = await response.json();
    
    if (data.success) {
      // 清空当前聊天界面
      clearChatUI();
      
      // 渲染所有消息
      data.messages.forEach(msg => {
        displayMessage(msg.role, msg.content, msg.create_time);
      });
      
      // 设置当前会话 ID
      currentConversationId = conversationId;
    }
  } catch (error) {
    console.error('加载对话详情失败:', error);
  }
}

function displayMessage(role, content, time) {
  const messagesDiv = document.getElementById('messages');
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}`;
  
  msgDiv.innerHTML = `
    <div class="content">${content}</div>
    <div class="time">${time}</div>
  `;
  
  messagesDiv.appendChild(msgDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
```

---

#### 6. 删除对话

**接口**: `POST /delete_conversation`

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "conversation_id": "conv_1713081234567_abc123"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Conversation deleted successfully"
}
```

**前端使用**:
```javascript
async function deleteConversation(conversationId) {
  if (!confirm('确定要删除这个对话吗？')) {
    return;
  }
  
  const token = localStorage.getItem('token');
  
  try {
    const response = await fetch('http://127.0.0.1:5001/delete_conversation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        conversation_id: conversationId
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // 刷新对话列表
      await loadConversationList();
      
      // 如果删除的是当前对话，清空聊天界面
      if (conversationId === currentConversationId) {
        clearChatUI();
        currentConversationId = null;
      }
      
      alert('删除成功');
    } else {
      alert('删除失败: ' + data.message);
    }
  } catch (error) {
    console.error('删除对话失败:', error);
    alert('网络错误');
  }
}
```

---

## 💻 完整示例

### React 组件示例

```jsx
import React, { useState, useEffect } from 'react';

const ChatApp = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const token = localStorage.getItem('token');
  
  // 加载对话列表
  useEffect(() => {
    loadConversations();
  }, []);
  
  const loadConversations = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5001/get_conversations', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (data.success) {
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error('加载对话列表失败:', error);
    }
  };
  
  // 加载对话详情
  const loadConversation = async (conversationId) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:5001/get_conversation_detail?conversation_id=${conversationId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const data = await response.json();
      if (data.success) {
        setMessages(data.messages);
        setCurrentConvId(conversationId);
      }
    } catch (error) {
      console.error('加载对话失败:', error);
    }
  };
  
  // 发送消息
  const sendMessage = async () => {
    if (!inputValue.trim() || loading) return;
    
    const question = inputValue;
    setInputValue('');
    setLoading(true);
    
    // 如果没有当前会话，创建新会话
    const convId = currentConvId || `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    if (!currentConvId) {
      setCurrentConvId(convId);
    }
    
    // 添加用户消息到界面
    const userMsg = {
      role: 'user',
      content: question,
      create_time: new Date().toLocaleString()
    };
    setMessages(prev => [...prev, userMsg]);
    
    try {
      const response = await fetch(
        `http://127.0.0.1:5001/question?question=${encodeURIComponent(question)}&conversation_id=${convId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      const data = await response.json();
      
      if (data.answer) {
        // 添加 AI 消息到界面
        const aiMsg = {
          role: 'assistant',
          content: data.answer,
          create_time: new Date().toLocaleString()
        };
        setMessages(prev => [...prev, aiMsg]);
        
        // 刷新对话列表
        loadConversations();
      }
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 新建对话
  const startNewChat = () => {
    setCurrentConvId(null);
    setMessages([]);
  };
  
  return (
    <div className="chat-app">
      {/* 侧边栏 */}
      <div className="sidebar">
        <button onClick={startNewChat}>+ 新建对话</button>
        <div className="conversation-list">
          {conversations.map(conv => (
            <div 
              key={conv.conversation_id}
              className={`conversation-item ${conv.conversation_id === currentConvId ? 'active' : ''}`}
              onClick={() => loadConversation(conv.conversation_id)}
            >
              <div className="preview">{conv.preview}</div>
              <div className="time">{conv.last_update}</div>
            </div>
          ))}
        </div>
      </div>
      
      {/* 聊天区域 */}
      <div className="chat-main">
        <div className="messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <div className="content">{msg.content}</div>
              <div className="time">{msg.create_time}</div>
            </div>
          ))}
        </div>
        
        <div className="input-area">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="输入您的问题..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading}>
            {loading ? '发送中...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatApp;
```

---

## ❓ 常见问题

### Q1: 为什么对话没有保存？

**A**: 检查以下几点：
1. 是否在请求中包含了 `conversation_id` 参数？
2. 是否携带了有效的 `Authorization` header？
3. Token 是否过期？
4. 查看后端日志是否有错误信息

### Q2: 如何生成 conversation_id？

**A**: 前端生成，推荐使用以下格式：
```javascript
const conversationId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
// 示例：conv_1713081234567_abc123xyz
```

### Q3: Token 过期怎么办？

**A**: 
```javascript
// 在每次请求后检查响应状态
if (response.status === 401) {
  localStorage.removeItem('token');
  window.location.href = '/login';
}
```

### Q4: 如何实现类似 DeepSeek 的界面？

**A**: 参考上面的完整示例，关键点：
1. 左侧显示对话列表（`/get_conversations`）
2. 右侧显示聊天内容（`/get_conversation_detail`）
3. 点击"新建对话"生成新的 `conversation_id`
4. 发送问题时带上 `conversation_id`，自动保存

### Q5: 对话数据保存在哪里？

**A**: 保存在 MySQL 的 `conversations` 表中，格式为：
```json
{
  "用户名": "问题内容",
  "AI": "AI回答内容"
}
```

### Q6: 可以修改已发送的消息吗？

**A**: 当前版本不支持修改。如需修改，请删除该对话后重新发送。

---

## 📞 技术支持

如有问题，请查看：
- 后端日志：`logs/app.log`
- 错误日志：`logs/error.log`
- 数据库表结构：`generate_table.sql`

---

**文档版本**: v2.0  
**最后更新**: 2026-04-14  
**维护者**: Medical QA Team
