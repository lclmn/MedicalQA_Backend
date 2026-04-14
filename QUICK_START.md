# 🚀 对话历史功能 - 快速开始

## 5 分钟快速上手

### 步骤 1: 创建数据库表（1 分钟）

在 MySQL 中执行：

```sql
-- 如果还未执行过 generate_table.sql，请执行完整文件
source D:\code\MedicalQA\MedicalQA_Backend\generate_table.sql

-- 或者只执行以下语句创建 conversations 表
USE userdb;

CREATE TABLE `conversations` (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '对话ID',
  user_id INT NOT NULL COMMENT '用户ID',
  conversation_id VARCHAR(100) NOT NULL COMMENT '会话ID',
  role VARCHAR(20) NOT NULL COMMENT '角色：user或assistant',
  content TEXT NOT NULL COMMENT '消息内容',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_user_conversation (user_id, conversation_id),
  INDEX idx_conversation_id (conversation_id),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户对话历史表';
```

验证表是否创建成功：
```sql
SHOW TABLES LIKE 'conversations';
DESCRIBE conversations;
```

---

### 步骤 2: 启动 Flask 应用（1 分钟）

```bash
cd D:\code\MedicalQA\MedicalQA_Backend
python app.py
```

看到以下输出表示成功：
```
Starting Flask application on port 5001
 * Running on http://127.0.0.1:5001
```

---

### 步骤 3: 测试功能（3 分钟）

#### 方法一：使用自动化测试脚本

```bash
python test_conversation.py
```

脚本会自动测试所有功能并显示结果。

#### 方法二：手动测试（使用 Postman 或 curl）

**1. 登录获取 Token**

```bash
curl -X POST http://127.0.0.1:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Test123456"}'
```

保存返回的 `token`。

**2. 发送问题（自动保存）**

```bash
# 生成一个 conversation_id，例如：conv_123456_test
curl -X GET "http://127.0.0.1:5001/question?question=感冒有哪些症状？&conversation_id=conv_123456_test" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**3. 获取对话列表**

```bash
curl -X GET http://127.0.0.1:5001/get_conversations \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

应该能看到刚才的对话。

**4. 获取对话详情**

```bash
curl -X GET "http://127.0.0.1:5001/get_conversation_detail?conversation_id=conv_123456_test" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

应该能看到完整的问答记录。

---

## 💻 前端集成示例

### 最小化实现

```html
<!DOCTYPE html>
<html>
<head>
    <title>医疗问答</title>
    <style>
        body { font-family: Arial; margin: 0; display: flex; height: 100vh; }
        .sidebar { width: 250px; background: #f5f5f5; padding: 20px; overflow-y: auto; }
        .chat { flex: 1; display: flex; flex-direction: column; padding: 20px; }
        .messages { flex: 1; overflow-y: auto; margin-bottom: 20px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 8px; max-width: 70%; }
        .user { background: #007bff; color: white; margin-left: auto; }
        .assistant { background: #f0f0f0; margin-right: auto; }
        .input-area { display: flex; gap: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .conv-item { padding: 10px; cursor: pointer; border-bottom: 1px solid #ddd; }
        .conv-item:hover { background: #e0e0e0; }
    </style>
</head>
<body>
    <!-- 侧边栏 -->
    <div class="sidebar">
        <button onclick="newConversation()" style="width: 100%; margin-bottom: 20px;">+ 新建对话</button>
        <div id="conversationList"></div>
    </div>
    
    <!-- 聊天区域 -->
    <div class="chat">
        <div class="messages" id="messages"></div>
        <div class="input-area">
            <input type="text" id="questionInput" placeholder="输入您的问题..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">发送</button>
        </div>
    </div>

    <script>
        let currentConvId = null;
        const token = localStorage.getItem('token'); // 假设已登录
        
        // 生成会话 ID
        function generateConvId() {
            return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        
        // 新建对话
        function newConversation() {
            currentConvId = generateConvId();
            document.getElementById('messages').innerHTML = '';
            loadConversations();
        }
        
        // 发送消息
        async function sendMessage() {
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            if (!question) return;
            
            if (!currentConvId) {
                newConversation();
            }
            
            // 显示用户消息
            displayMessage('user', question);
            input.value = '';
            
            // 发送请求
            const response = await fetch(
                `/question?question=${encodeURIComponent(question)}&conversation_id=${currentConvId}`,
                { headers: { 'Authorization': `Bearer ${token}` } }
            );
            const data = await response.json();
            
            // 显示 AI 回复
            if (data.answer) {
                displayMessage('assistant', data.answer);
                loadConversations(); // 刷新列表
            }
        }
        
        // 显示消息
        function displayMessage(role, content) {
            const messagesDiv = document.getElementById('messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}`;
            msgDiv.textContent = content;
            messagesDiv.appendChild(msgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // 加载对话列表
        async function loadConversations() {
            const response = await fetch('/get_conversations', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            
            const listDiv = document.getElementById('conversationList');
            listDiv.innerHTML = '';
            
            data.conversations.forEach(conv => {
                const item = document.createElement('div');
                item.className = 'conv-item';
                item.textContent = conv.last_message.substring(0, 30) + '...';
                item.onclick = () => loadConversationDetail(conv.conversation_id);
                listDiv.appendChild(item);
            });
        }
        
        // 加载对话详情
        async function loadConversationDetail(convId) {
            currentConvId = convId;
            const response = await fetch(
                `/get_conversation_detail?conversation_id=${convId}`,
                { headers: { 'Authorization': `Bearer ${token}` } }
            );
            const data = await response.json();
            
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = '';
            
            data.messages.forEach(msg => {
                displayMessage(msg.role, msg.content);
            });
        }
        
        // 页面加载时初始化
        window.onload = () => {
            newConversation();
        };
    </script>
</body>
</html>
```

保存为 `chat_demo.html`，然后在浏览器中打开即可体验！

---

## 🎯 核心 API 速查

| 接口 | 方法 | 说明 |
|------|------|------|
| `/question?question=xxx&conversation_id=yyy` | GET | 智能问答（自动保存） |
| `/get_conversations` | GET | 获取对话列表 |
| `/get_conversation_detail?conversation_id=xxx` | GET | 获取对话详情 |
| `/delete_conversation` | POST | 删除对话 |

**请求头**（除 question 外都需要）：
```
Authorization: Bearer <your_token>
```

---

## ❓ 常见问题

### Q: 对话没有保存？
A: 检查是否在请求中包含了 `conversation_id` 参数和有效的 `Authorization` header。

### Q: 如何生成 conversation_id？
A: 前端生成，推荐格式：`'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)`

### Q: 可以修改已保存的消息吗？
A: 当前版本不支持，如需修改请先删除再重新发送。

### Q: 对话有数量限制吗？
A: 理论上无限制，取决于数据库存储空间。

---

## 📚 下一步

- 阅读 `CONVERSATION_SETUP_GUIDE.md` 了解详细部署指南
- 查看 `API_DOCUMENTATION.md` 了解完整 API 文档
- 参考 `IMPLEMENTATION_SUMMARY.md` 了解技术实现细节

---

## 🎉 完成！

现在您已经可以快速使用对话历史功能了！享受类似 DeepSeek 的聊天体验吧！
