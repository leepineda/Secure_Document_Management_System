CREATE DATABASE IF NOT EXISTS secure;
USE secure;

CREATE TABLE departments (
    department_id INT PRIMARY KEY AUTO_INCREMENT,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

INSERT INTO departments (department_name) VALUES
    ('Human Resources'),
    ('Finance'),
    ('IT'),
    ('Security');

CREATE TABLE user_accounts (
    account_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(32) NOT NULL UNIQUE,
    department_id INT NULL,
    status ENUM('active', 'suspended', 'pending') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    login_attempts INT DEFAULT 0,
    lockout_until DATETIME DEFAULT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);

CREATE TABLE user_credentials (
    account_id INT PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    last_login TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (account_id) REFERENCES user_accounts(account_id) ON DELETE CASCADE
);

CREATE TABLE roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(24) NOT NULL UNIQUE
);

INSERT INTO roles (role_name) VALUES
    ('admin'),
    ('moderator'),
    ('user');

CREATE TABLE user_roles (
    account_id INT,
    role_id INT,
    CONSTRAINT one_role_per_user UNIQUE (account_id),
    FOREIGN KEY (account_id) REFERENCES user_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    PRIMARY KEY (account_id, role_id)
);

CREATE TABLE documents (
    document_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    owner_id INT NOT NULL,
    department_id INT,
    clearance_required ENUM('public', 'internal', 'confidential', 'top_secret') DEFAULT 'internal',
    requires_mfa BOOLEAN DEFAULT FALSE,
    status ENUM('approved', 'rejected', 'pending') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (owner_id) REFERENCES user_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);

CREATE TABLE security_audit_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT NULL,
    action_performed VARCHAR(100) NOT NULL,
    resource_affected VARCHAR(100) NULL,
    ip_address VARCHAR(45),
    status ENUM('ALLOWED', 'DENIED', 'ERROR') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES user_accounts(account_id) ON DELETE SET NULL
);
