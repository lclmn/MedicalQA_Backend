  create database userdb;
  use userdb;
  CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    age INT,
    gender VARCHAR(10)
  );
  CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    adminname VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL
  );
  INSERT INTO admin (adminname, password) VALUES ('admin', 'admin');