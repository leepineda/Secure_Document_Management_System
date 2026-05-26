Changelog

All notable changes to this project are documented here.
Format: Added / Changed / Fixed / Removed / Security / Known Issues

## 1.0.1
Added
---
- Documents table displayed on home route — all authenticated users can view all documents
- Added a add document route that adds/creates new documents

Known issues
---
- Documents visible to all authenticated users regardless of role, department, or clearance level
- Anyone can make documents, regarding role and attribute

## 1.0.0 — 2026-05-25 — MVP

Added
---
- Login route with password hash verification and account status enforcement
- Logout route with session clearing
- Session cookies hardened (`HttpOnly`, `Secure`, `SameSite=Lax`)
- `debug=False` set on Flask app

Changed
---
- All routes now use `try/finally` to guarantee database connection closure

Known Issues
---
- Delete route has no authorization check — any authenticated user can delete any account
- Home route returns all user accounts with no role or ownership filtering
- No CSRF protection on POST routes
- No input validation on any field
- request.remote_addr may log proxy IP instead of real client IP
- Audit log account_id becomes NULL when a user is hard-deleted — traceability lost
- No soft delete implemented
- PDP exists but is empty

## [0.5.0] — 2026-05-23

Added
---
- Register route — inserts into `user_accounts`, `user_credentials`, and `user_roles` atomically
- Password hashing via Werkzeug (scrypt)
- Audit log entry on registration (includes IP address)
- Home route redirects unauthenticated users to login
- Delete route with rollback on failure
- Search route with parameterized `LIKE` query

Changed
---
- All routes migrated from `security` database to `secure` database
- HTML templates updated to reference new table and column names

Security
---
- Credentials stored as hashed values — no plaintext passwords
- All queries use parameterized statements
- Database credentials loaded from `.env` via `python-dotenv`

Known Issues
---
- Delete route has no authorization check — any authenticated user can delete any account
- Home route returns all user accounts with no role or ownership filtering
- No CSRF protection on POST routes
- No input validation on any field
- `request.remote_addr` may log proxy IP instead of real client IP


## 0.4.0 — 2026-05-22 — Schema Overhaul

Added
---
- New `secure` database replacing original `security` database
- `departments` table
- `user_accounts` table (email, username, trust level, status, department)
- `user_credentials` table — credentials separated from identity
- `documents` table with `clearance_required` and `requires_mfa` fields
- `security_audit_logs` table — append-only access event log

Changed
---
- Roles expanded: `admin`, `moderator`, `user` (was `admin`, `editor`, `viewer`)
- `user_roles` now references `account_id` instead of `user_id`

Known Issues
---
- Audit log `account_id` becomes `NULL` when a user is hard-deleted — traceability lost
- No soft delete implemented

## 0.3.0 — 2026-05-17

Added
---
- `trust_level` ENUM (`high`, `medium`, `low`) on users table
- `status` ENUM (`active`, `suspended`, `pending`) on users table
- `pdp.py` — Policy Decision Point skeleton

Known Issues
---
- `debug=True` enabled — must be disabled before any deployment
- Home and search routes missing `try/finally` blocks
- PDP exists in same process as application — no isolation

## 0.2.0 — 2026-05-15

Added
---
- 3-table schema: `users`, `roles`, `user_roles`
- Automatic default role assignment (`viewer`) on user creation
- Transaction logic — commit only on full success, rollback on failure

Changed
---
- Reverted from SQLAlchemy ORM to raw prepared statements

Security
---
- Parameterized queries on all inserts

Known Issues
---
- No authentication or password handling
- Root MySQL user still in use
- No input validation

### 0.1.0 Initial

Added
---
- Flask app connected to MySQL (MariaDB)
- Basic GET and POST routes
- GitHub repository initialized

Security
---
- database password hardcoded in source
- Application running as root MySQL user
- No `.gitignore` — sensitive files exposed in version history