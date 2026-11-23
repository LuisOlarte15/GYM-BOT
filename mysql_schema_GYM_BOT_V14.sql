CREATE DATABASE IF NOT EXISTS gym_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gym_bot;
CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(120) NOT NULL,username VARCHAR(80) NOT NULL UNIQUE,password_hash VARCHAR(255) NOT NULL,role ENUM('ADMIN','USUARIO') NOT NULL DEFAULT 'USUARIO',age INT NULL,height_cm DECIMAL(5,2) NULL,weight_kg DECIMAL(5,2) NULL,goal VARCHAR(80),level VARCHAR(40),days_per_week TINYINT,avatar LONGTEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS exercises (id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(120) UNIQUE,muscle VARCHAR(80),equipment VARCHAR(80),level VARCHAR(40),sets_text VARCHAR(30),reps_text VARCHAR(40),rest_text VARCHAR(30),description TEXT,video_url TEXT);
CREATE TABLE IF NOT EXISTS routines (id INT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,name VARCHAR(160),goal VARCHAR(80),week_number INT,week_start DATE,week_end DATE,status VARCHAR(30) DEFAULT 'active',completed_at DATETIME NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS routine_days (id INT AUTO_INCREMENT PRIMARY KEY,routine_id INT NOT NULL,day_index TINYINT,day_name VARCHAR(20),status VARCHAR(20) DEFAULT 'pending',completed_at DATETIME NULL,UNIQUE KEY uq_routine_day(routine_id,day_name),FOREIGN KEY(routine_id) REFERENCES routines(id));
CREATE TABLE IF NOT EXISTS routine_items (id INT AUTO_INCREMENT PRIMARY KEY,routine_id INT NOT NULL,day_name VARCHAR(20),exercise_id INT NOT NULL,position TINYINT,FOREIGN KEY(routine_id) REFERENCES routines(id),FOREIGN KEY(exercise_id) REFERENCES exercises(id));
CREATE TABLE IF NOT EXISTS training_logs (id INT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,exercise_id INT NOT NULL,log_date DATETIME,weight_kg DECIMAL(7,2),reps INT,sets_count INT,rpe DECIMAL(3,1),notes TEXT,FOREIGN KEY(user_id) REFERENCES users(id),FOREIGN KEY(exercise_id) REFERENCES exercises(id));


-- V16 Wompi: registro local de órdenes de pago (referencia, monto y estado).
CREATE TABLE payments (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT NOT NULL,
 reference VARCHAR(100) NOT NULL UNIQUE,
 amount_cop BIGINT NOT NULL,
 currency CHAR(3) NOT NULL DEFAULT 'COP',
 status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
 wompi_transaction_id VARCHAR(120) NULL,
 created DATETIME NOT NULL,
 updated DATETIME NULL,
 processed_at DATETIME NULL
);
