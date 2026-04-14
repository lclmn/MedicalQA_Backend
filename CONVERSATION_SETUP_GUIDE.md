# 对话历史功能部署指南

## 📋 概述

本指南将帮助您部署和使用新增的对话历史功能，实现类似 DeepSeek 网页版的聊天界面效果。

---

## 🔧 部署步骤

### 步骤 1: 创建数据库表

首先需要在 MySQL 数据库中创建 `conversations` 表。

#### 方法一：使用 MySQL 命令行

```bash
# 登录 MySQL
mysql -u root -p

# 执行 SQL 脚本
source D:\code\MedicalQA\MedicalQA_Backend\generate_table.sql
```

#### 方法二：使用 MySQL Workbench 或其他 GUI 工具

1. 打开 `generate_table.sql` 文件
2. 复制其中的 SQL 语句
3. 在 MySQL Workbench 中执行

#### 验证表是否创建成功

```sql
USE userdb;
SHOW TABLES;
DESCRIBE conversations;
```

应该能看到 `conversations` 表及其字段结构。

---

### 步骤 2: 启动 Flask 应用

```bash
# 进入项目目录
cd D:\code\MedicalQA\MedicalQA_Backend

# 安装依赖（如果还未安装）
pip install -r requirements.txt

# 启动应用
python app.py
```

应用将在 `http://127.0.0.1:5001` 运行。

---

### 步骤 3: 运行测试脚本（可选）

为了验证功能是否正常，可以运行提供的测试脚本：

```bash
python test_conversation.py
```

测试脚本会自动执行以下操作：
1. 注册/登录用户
2. 发送问题并自动保存对话
3. 获取对话列表
4. 获取对话详情
5. 手动保存对话消息
6. 删除对话
7. 验证删除结果

---

## 🎯 API 接口说明

### 核心接口

#### 1. 智能问答（自动保存对话）
```
GET /question?question=你的问题&conversation_id=会话ID
Headers: Authorization: Bearer <token>
```

**特点**：
- 当提供 `conversation_id` 和有效 Token 时，自动保存用户问题和 AI 回答
- 无需手动调用保存接口

#### 2. 获取对话列表
```
GET /get_conversations
Headers: Authorization: Bearer <token>
```

**返回**：
```json
{
  "success": true,
  "conversations": [
    {
      "conversation_id": "conv_1234567890_abc123",
      "last_message": "感冒的常见症状包括...",
      "last_update": "2026-04-14 10:30:00",
      "message_count": 10
    }
  ]
}
```

#### 3. 获取对话详情
```
GET /get_conversation_detail?conversation_id=会话ID
Headers: Authorization: Bearer <token>
```

**返回**：
```json
{
  "success": true,
  "conversation_id": "conv_1234567890_abc123",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "感冒有哪些症状？",
      "create_time": "2026-04-14 10:25:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "感冒的常见症状包括...",
      "create_time": "2026-04-14 10:25:05"
    }
  ]
}
```

#### 4. 删除对话
```
POST /delete_conversation
Headers: 
  Content-Type: application/json
  Authorization: Bearer <token>
Body:
{
  "conversation_id": "会话ID"
}
```

---

## 💻 前端集成示例

### 1. 生成会话 ID

```javascript
// 方法一：使用时间戳 + 随机数
function generateConversationId() {
  return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 方法二：使用 UUID 库
import { v4 as uuidv4 } from 'uuid';
const conversationId = 'conv_' + uuidv4();
```

### 2. 新建对话

```javascript
let currentConversationId = null;

function startNewConversation() {
  currentConversationId = generateConversationId();
  // 清空当前聊天界面
  clearChatUI();
  console.log('新对话已创建:', currentConversationId);
}
```

### 3. 发送消息

```javascript
async function sendMessage(question) {
  if (!currentConversationId) {
    startNewConversation();
  }
  
  const token = localStorage.getItem('token');
  const url = `/question?question=${encodeURIComponent(question)}&conversation_id=${currentConversationId}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (data.answer) {
      // 显示用户消息
      displayMessage('user', question);
      // 显示 AI 回复
      displayMessage('assistant', data.answer);
      
      // 刷新侧边栏对话列表
      refreshConversationList();
    }
  } catch (error) {
    console.error('发送消息失败:', error);
  }
}
```

### 4. 加载对话列表

```javascript
async function loadConversationList() {
  const token = localStorage.getItem('token');
  
  try {
    const response = await fetch('/get_conversations', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
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
      <div class="conversation-title">${conv.last_message}</div>
      <div class="conversation-time">${conv.last_update}</div>
    `;
    item.onclick = () => loadConversation(conv.conversation_id);
    sidebar.appendChild(item);
  });
}
```

### 5. 加载对话详情

```javascript
async function loadConversation(conversationId) {
  const token = localStorage.getItem('token');
  currentConversationId = conversationId;
  
  try {
    const response = await fetch(
      `/get_conversation_detail?conversation_id=${conversationId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    const data = await response.json();
    
    if (data.success) {
      // 清空并重新渲染聊天界面
      clearChatUI();
      data.messages.forEach(msg => {
        displayMessage(msg.role, msg.content);
      });
    }
  } catch (error) {
    console.error('加载对话详情失败:', error);
  }
}
```

### 6. 删除对话

```javascript
async function deleteConversation(conversationId) {
  if (!confirm('确定要删除这个对话吗？')) return;
  
  const token = localStorage.getItem('token');
  
  try {
    const response = await fetch('/delete_conversation', {
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
      loadConversationList();
      
      // 如果删除的是当前对话，清空聊天界面
      if (conversationId === currentConversationId) {
        clearChatUI();
        currentConversationId = null;
      }
    }
  } catch (error) {
    console.error('删除对话失败:', error);
  }
}
```

---

## 🎨 UI 布局建议

参考 DeepSeek 的界面设计：

```
┌──────────────────────────────────────────────────────┐
│ 医疗问答系统                          [用户] [退出]   │
├──────────────┬───────────────────────────────────────┤
│              │                                       │
│ [+ 新建对话] │  用户: 感冒有哪些症状？                │
│              │                                       │
│ ──────────── │  AI: 感冒的常见症状包括流鼻涕、       │
│              │      咳嗽、喉咙痛、发热等...           │
│ 📝 感冒症状  │                                       │
│   10:30      │  用户: 怎么治疗？                     │
│              │                                       │
│ 📝 糖尿病    │  AI: 建议多休息、多喝水，可以服用...  │
│   昨天       │                                       │
│              │                                       │
│ 📝 高血压    │  ┌─────────────────────────────┐     │
│   3天前      │  │ 输入您的问题...      [发送] │     │
│              │  └─────────────────────────────┘     │
│              │                                       │
└──────────────┴───────────────────────────────────────┘
```

### CSS 样式建议

```css
/* 侧边栏 */
.sidebar {
  width: 260px;
  height: 100vh;
  background: #f7f7f8;
  border-right: 1px solid #e5e5e5;
  overflow-y: auto;
}

.conversation-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #e5e5e5;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: #e8e8e8;
}

.conversation-item.active {
  background: #e0e0e0;
}

/* 主聊天区域 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-height: 100vh;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 20px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
  background: #007bff;
  color: white;
  padding: 12px 16px;
  border-radius: 18px 18px 4px 18px;
}

.message.assistant {
  margin-right: auto;
  background: #f0f0f0;
  padding: 12px 16px;
  border-radius: 18px 18px 18px 4px;
}

/* 输入框 */
.input-area {
  padding: 20px;
  border-top: 1px solid #e5e5e5;
}

.input-box {
  display: flex;
  gap: 10px;
}

.input-box input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.input-box button {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.input-box button:hover {
  background: #0056b3;
}
```

---

## 🔍 故障排查

### 问题 1: 对话没有保存

**可能原因**：
- 未提供 `conversation_id` 参数
- Token 无效或过期
- 数据库连接失败

**解决方法**：
1. 检查请求 URL 是否包含 `conversation_id`
2. 检查 Header 中的 Token 是否有效
3. 查看后端日志确认是否有错误信息

### 问题 2: 获取对话列表为空

**可能原因**：
- 该用户还没有任何对话记录
- Token 对应的用户 ID 与保存对话时的用户 ID 不一致

**解决方法**：
1. 先发送一个问题创建对话
2. 检查 Token 是否正确

### 问题 3: 数据库表不存在

**错误信息**：
```
Table 'userdb.conversations' doesn't exist
```

**解决方法**：
执行 `generate_table.sql` 脚本创建表

---

## 📊 数据库表结构

### conversations 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| user_id | INT | 用户ID，外键关联 user 表 |
| conversation_id | VARCHAR(100) | 会话ID（前端生成） |
| role | VARCHAR(20) | 角色：user 或 assistant |
| content | TEXT | 消息内容 |
| create_time | DATETIME | 创建时间 |

**索引**：
- `idx_user_conversation`: (user_id, conversation_id) - 加速查询用户的对话
- `idx_conversation_id`: (conversation_id) - 加速按会话ID查询

**外键约束**：
- `user_id` 关联 `user(id)`，删除用户时级联删除其所有对话

---

## ✨ 最佳实践

### 1. 会话 ID 管理

```javascript
// 推荐：在页面加载时检查是否有进行中的对话
window.onload = function() {
  const savedConvId = sessionStorage.getItem('currentConversationId');
  if (savedConvId) {
    currentConversationId = savedConvId;
    loadConversation(savedConvId);
  } else {
    startNewConversation();
  }
};

// 切换对话时保存
function loadConversation(convId) {
  currentConversationId = convId;
  sessionStorage.setItem('currentConversationId', convId);
  // ... 加载对话内容
}
```

### 2. 自动滚动到底部

```javascript
function displayMessage(role, content) {
  // 添加消息到界面
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;
  messageDiv.textContent = content;
  messagesArea.appendChild(messageDiv);
  
  // 自动滚动到底部
  messagesArea.scrollTop = messagesArea.scrollHeight;
}
```

### 3. 加载状态提示

```javascript
async function sendMessage(question) {
  // 显示加载状态
  showLoadingIndicator();
  
  try {
    const response = await fetch(/* ... */);
    const data = await response.json();
    
    // 隐藏加载状态，显示消息
    hideLoadingIndicator();
    displayMessage('user', question);
    displayMessage('assistant', data.answer);
  } catch (error) {
    hideLoadingIndicator();
    showError('发送失败，请重试');
  }
}
```

### 4. 防抖处理

```javascript
// 防止快速点击发送按钮
let isSending = false;

async function sendMessage(question) {
  if (isSending) return;
  
  isSending = true;
  try {
    // 发送逻辑...
  } finally {
    isSending = false;
  }
}
```

---

## 📚 相关文档

- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - 完整的 API 文档
- [test_conversation.py](./test_conversation.py) - 自动化测试脚本

---

## 🎉 完成！

现在您已经完成了对话历史功能的部署，可以享受类似 DeepSeek 的聊天体验了！

如有问题，请查看：
1. Flask 应用日志：`logs/app.log`
2. 错误日志：`logs/error.log`
3. API 文档：`API_DOCUMENTATION.md`
