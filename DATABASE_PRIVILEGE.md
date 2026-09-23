##
This is what i ran on SQL to execute the principle of least  privilege,

Create a user
---
CREATE USER IF NOT EXISTS 'flask_app'@'localhost' IDENTIFIED BY 'password_placeholder';

Revoke all of the user privileges
---
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'flask_app'@'localhost';

Grant what's only needed on the tables.
---

GRANT SELECT, INSERT, UPDATE ON secure.user_accounts TO 'flask_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON secure.user_credentials TO 'flask_app'@'localhost';
GRANT SELECT ON secure.roles TO 'flask_app'@'localhost';
GRANT SELECT, INSERT ON secure.user_roles TO 'flask_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON secure.documents TO 'flask_app'@'localhost';
GRANT SELECT ON secure.departments TO 'flask_app'@'localhost';
GRANT INSERT ON secure.security_audit_logs TO 'flask_app'@'localhost';

Flush privilege
---
FLUSH PRIVILEGES;

SHOW GRANTS FOR 'flask_app'@'localhost';