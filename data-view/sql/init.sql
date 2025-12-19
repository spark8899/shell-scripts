-- sql/init.sql
-- Create database if it doesn't exist (optional, depends on your setup)
-- CREATE DATABASE IF NOT EXISTS your_database_name CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE your_database_name;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: The default admin user will be added by the application
--       during startup if it doesn't exist, using the hashed password.
--       You could manually insert here if you pre-hash the password.
-- Example (manual insert with pre-hashed password - replace hash):
-- INSERT INTO users (username, hashed_password) VALUES ('admin', '$2b$12$....hashed_password_here....');
