-- 创建数据库（如果不存在则创建，更安全）
CREATE DATABASE IF NOT EXISTS userdb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE userdb;

-- 用户表（优化字段、索引、约束）
CREATE TABLE IF NOT EXISTS `user` (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
  username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名（唯一）',
  password VARCHAR(255) NOT NULL COMMENT '密码（bcrypt加密）',
  age INT NULL COMMENT '年龄',
  gender VARCHAR(10) NULL COMMENT '性别',
  phone_number VARCHAR(20) NULL COMMENT '手机号码',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX idx_username (username),
  INDEX idx_phone_number (phone_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- 管理员表
CREATE TABLE IF NOT EXISTS `admin` (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '管理员ID',
  adminname VARCHAR(50) NOT NULL UNIQUE COMMENT '管理员账号',
  password VARCHAR(255) NOT NULL COMMENT '密码（bcrypt加密）',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_adminname (adminname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员表';

-- 插入默认管理员（明文密码，需运行 update_admin_password.py 脚本进行哈希加密）
-- INSERT INTO admin (adminname, password) VALUES ('admin', 'admin');

-- 对话表（用于存储用户与DeepSeek的历史聊天记录）
CREATE TABLE `conversations` (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '对话ID',
  user_id INT NOT NULL COMMENT '用户ID',
  username VARCHAR(50) NOT NULL COMMENT '用户名',
  conversation_id VARCHAR(100) NOT NULL COMMENT '会话ID（前端生成，用于标识一次完整的对话）',
  conversation_data JSON NOT NULL COMMENT '对话数据，格式：{"user": "问题内容", "assistant": "AI回答内容"}',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_user_conversation (user_id, conversation_id),
  INDEX idx_conversation_id (conversation_id),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户对话历史表';