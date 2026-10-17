# Secure Document Management System

A security-focused document management system built with Flask and MySQL, featuring role-based access control (RBAC), hardened authentication, IP rate limiting, and database-enforced audit logging. Started May 2026, in active development.

This is a transparent learning project. Every security control here was implemented, tested, broken, and re-reasoned from scratch to understand the mechanics behind modern web security.

## Key Features

**Authentication & Session Security**
- Password hashing via Werkzeug (scrypt).
- Hardened session cookies (`HttpOnly`, `Secure`, `SameSite=Lax`).
- Session cleared and reissued on every login to prevent session fixation.
- Per-request session validation detects changes (deleted account, suspended status, role changes) and invalidates the session immediately.
- Dummy-hash comparisons on unknown/locked accounts to mitigate timing-based user enumeration.

**Brute-Force & Spam Protection**
- IP-based rate limiting via `Flask-Limiter` on authentication and data submission endpoints.
- Tiered account lockout (5 minutes for 5 fails, 30 minutes for 10 fails).

**Access Control & Authorization**
- `@roles_required` decorator enforces RBAC centrally across protected routes.
- Three roles (admin, moderator, user) with clearance-gated document visibility.
- Admin-only document approval endpoint validating against strict `clearance_required` database ENUMs.
- Safeguards preventing administrators from deleting their own accounts.

**Audit Logging & Database Security**
- Centralized `log_event()` helper safely tracks action, actor, IP, and outcome in an append-only `security_audit_logs` table.
- Database-layer least privilege: the application runs on a dedicated MySQL service account with strictly limited `GRANT` permissions and no `DELETE` access.
- Soft deletes (`is_deleted`) to preserve relational data and forensic audit trails.
- Multi-table writes wrapped in database transactions with automatic rollbacks.

## Tech Stack

- **Backend:** Python, Flask, Flask-WTF, Flask-Limiter
- **Database:** MySQL / MariaDB (PyMySQL)
- **Security:** Werkzeug (scrypt)
- **Environment:** python-dotenv

## Documentation Focus

Documentation is treated as a core deliverable of this project:
- **`CHANGELOG.MD`**: Version history and feature tracking.
- **`DEVLOG.MD`**: Curated reasoning behind design decisions, failures, and tradeoffs.
- **`schema_evolution.sql`**: Chronological record of database schema decisions.

## Setup

1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create the database using `schema.sql`:
   ```bash
   mysql -u root -p < schema.sql
   ```
3. Apply the least-privilege database user permissions outlined in `DATABASE_PRIVILEGE.md`.
4. Create a `.env` file in the project root:
   ```text
   DB_HOST=localhost
   DB_USER=flask_app
   DB_PASSWORD=your_password
   DB_NAME=secure
   SECRET_KEY=your_generated_secret_key
   ```
   *(Generate a secure secret key using: `python -c "import secrets; print(secrets.token_hex(32))"`)*
5. Run the application:
   ```bash
   flask run

## Author
Justine Lee G. Pineda, [github.com/leepineda](https://github.com/leepineda)