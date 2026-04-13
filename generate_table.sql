-- 创建数据库（如果不存在则创建，更安全）
CREATE DATABASE IF NOT EXISTS userdb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE userdb;

-- 用户表（优化字段、索引、约束）
CREATE TABLE `user` (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
  username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名（唯一）',
  password VARCHAR(255) NOT NULL COMMENT '密码（bcrypt加密）',
  age INT NULL COMMENT '年龄',
  gender VARCHAR(10) NULL COMMENT '性别',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- 管理员表
CREATE TABLE `admin` (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '管理员ID',
  adminname VARCHAR(50) NOT NULL UNIQUE COMMENT '管理员账号',
  password VARCHAR(255) NOT NULL COMMENT '密码（bcrypt加密）',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_adminname (adminname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员表';

-- 插入默认管理员（明文密码，需运行 update_admin_password.py 脚本进行哈希加密）
INSERT INTO admin (adminname, password) VALUES ('admin', 'admin');