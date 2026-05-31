CREATE DATABASE IF NOT EXISTS security;

USE security;

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR (100) NOT NULL,
    email VARCHAR (100)
);

INSERT INTO users (name, email) VALUES (
    "lee", "leepineda@gmail.com"
); 

CREATE TABLE roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR (24) NOT NULL
);

INSERT INTO roles (role_name) VALU
ES ("admin"),("editor"),("viewer");

CREATE TABLE user_roles (
    user_id INT,
    role_id INT,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
); 

INSERT INTO user_roles VALUES (1,1);

-- added this attributes to try low scale ABAC
ALTER TABLE users
ADD trust_level ENUM("high", "medium", "low") NOT NULL DEFAULt "low";

ALTER TABLE users
ADD status ("active", "suspended", "pending") NOT NULL DEFAULT "pending";

--inserted a new user to see if the default works
INSERT INTO users (name, email) VALUES 
("mockuser","mockuser@gmail.com");

DESCRIBE users;

--updated the admin esque to have high trust and stat active
UPDATE users 
SET trust_level = 'high', status = 'active' 
WHERE name = 'lee';

-- this is wrong
SELECT u.name, r.role_name AS user_role 
FROM users u
JOIN roles r ON u.role_id = r.user_id;

--i needed 2 joins since i have 3 tables actually
SELECT u.name, r.role_name AS user_roles
FROM users u
JOIN user_roles ur ON u.user_id = ur.user_id
JOIN roles r ON ur.role_id = r.role_id;

--UPDATED THE status column it didnt have ENUMMM
ALTER TABLE users 
MODIFY COLUMN status ENUM("active", "suspended", "pending") NOT NULL DEFAULT "pending";

--made a new database, we gon use this one so the old one stays on the other side
CREATE DATABASE secure;
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
    trust_level ENUM('high', 'medium', 'low') NOT NULL DEFAULT 'low',
    status ENUM('active', 'suspended', 'pending') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);

CREATE TABLE user_credentials (
    account_id INT PRIMARY KEY, 
    password_hash VARCHAR(255) NOT NULL, --i think im just gonna use bcrypt
    last_login TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (account_id) REFERENCES user_accounts(account_id) ON DELETE CASCADE
);

CREATE TABLE roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(24) NOT NULL UNIQUE
);

INSERT INTO roles (role_name) VALUES 
    ("admin"), 
    ("moderator"),
    ("user");


CREATE TABLE user_roles (
    account_id INT,
    role_id INT,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, --added timestamps
    FOREIGN KEY (owner_id) REFERENCES user_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);

CREATE TABLE security_audit_logs ( -- append only, no altering data only enter
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT NULL, 
    action_performed VARCHAR(100) NOT NULL, 
    resource_affected VARCHAR(100) NULL,
    ip_address  VARCHAR (45),
    status ENUM('ALLOWED', 'DENIED', 'ERROR') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES user_accounts(account_id) ON DELETE SET NULL
); 

ALTER TABLE user_accounts ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE documents ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE user_accounts 
MODIFY COLUMN status ENUM('active', 'suspended', 'pending') 
DEFAULT 'active';