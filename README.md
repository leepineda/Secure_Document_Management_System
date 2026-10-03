# Secure Document Management System

A security-focused document management system built with Flask and MySQL:
role-based access control, hardened authentication, and database-enforced audit
logging. Started May 2026, in active development.

This is a learning project, but not a tutorial clone. Every security control
here was implemented, tested, broken, and re-reasoned from scratch, and the
full history of that process, including the mistakes, is documented in this
repo instead of hidden. Known weaknesses are listed openly under
[Known Limitations](#known-limitations).

## Key Features

**Authentication & Session Security**
- Password hashing via Werkzeug (scrypt)
- Hardened session cookies (`HttpOnly`, `Secure`, `SameSite=Lax`)
- Session cleared and reissued on every login to prevent session fixation
- Per-request session validation: if an account is deleted or suspended while
  the user is logged in, their session ends on the next request
- Dummy-hash comparison on unknown usernames and locked accounts, to reduce
  timing-based user enumeration at login
- Generic "Invalid credentials." response for unknown, deleted, locked, and
  suspended accounts

**Brute-Force Protection**
- Tiered account lockout: 5 failed attempts locks the account for 5 minutes,
  10 failed attempts for 30 minutes. The counter resets on a successful login.
- Login attempts and lockouts are logged with IP address

**CSRF Protection**
- Flask-WTF CSRF tokens on every state-changing (POST) route

**Role-Based Access Control**
- Three roles (admin / moderator / user) with clearance-gated document
  visibility: admins see everything, moderators see approved public and
  internal documents, users see approved public documents
- Authentication check on every protected route; role checks on admin actions
  (user deletion, document approval)
- Admin approval workflow: new documents start as `pending` and are published
  with an assigned clearance level

**Audit Logging**
- Append-only `security_audit_logs` table recording action, actor, IP, and
  outcome (ALLOWED / DENIED / ERROR) for registration, login events, and
  document approvals
- Enforced at the database layer: the app's MySQL account has only `INSERT` on
  this table, so even a compromised application cannot edit or delete log
  entries

**Database-Layer Least Privilege**
- Dedicated MySQL service account (not root) with per-table `GRANT`
  statements, e.g. `SELECT, INSERT, UPDATE` on `documents` and `INSERT`-only on
  `security_audit_logs`. No `DELETE` is granted on any table. See
  [`DATABASE_PRIVILEGE.md`](./DATABASE_PRIVILEGE.md).
- The app refuses to start if any required environment variable is missing,
  so a misconfiguration can never silently fall back to a more privileged
  database account

**Data Integrity**
- Soft deletes (`is_deleted`) instead of hard deletes, to preserve the audit
  trail
- Multi-table writes wrapped in transactions with commit/rollback, so a
  failure partway through never leaves a half-written record
- Parameterized queries throughout

## Tech Stack

- **Language:** Python
- **Backend:** Flask, Flask-WTF
- **Database:** MySQL / MariaDB (PyMySQL driver)
- **Auth:** Werkzeug (scrypt password hashing)
- **Config:** python-dotenv

## Project Structure

```
.
├── app.py                    # Main Flask application and routes
├── context.py                # App/db context helpers
├── pdp.py                    # Policy Decision Point (planned, not yet implemented)
├── schema.sql                # Current, canonical database schema
├── schema_evolution.sql      # Full history of schema decisions, incl. mistakes
├── DATABASE_PRIVILEGE.md     # SQL for the least-privilege DB service account
├── CHANGELOG.MD              # Version-by-version log of what changed and why
├── DEVLOG.MD                 # Day-by-day design reasoning (edited for clarity)
├── DEVLOG_raw.MD             # The same log, unfiltered and unedited
├── static/
├── templates/
└── requirements.txt
```

## Documentation

Documentation is treated as part of the deliverable:

- **`CHANGELOG.MD`**: what changed, release by release (Added / Changed /
  Fixed / Security / Known Issues / Planned).
- **`DEVLOG.MD`**: the reasoning behind those changes: what broke, what was
  learned, which tradeoffs were considered.
- **`DEVLOG_raw.MD`**: the same journal in its original, unfiltered form.
  Expect informal language.
- **`schema_evolution.sql`**: every schema change in the order it happened,
  including the broken queries and their fixes.

## Known Limitations

Found through self-review and documented rather than hidden. Each is tracked
in `CHANGELOG.MD`.

- The home and search routes show all user accounts to any logged-in user
- Audit logging does not yet cover failed logins for unknown usernames,
  attempts on deleted accounts, admin deletions, or 403 denials
- `role_name` is cached in the session, so role changes apply only after the
  user logs in again
- Registration reveals whether a username or email is already taken
  (user enumeration), and the lockout can be triggered against another user's
  account (denial of service); IP-based rate limiting is planned
- Logout is a GET request
- Only the delete and approve routes check roles; document creation and
  search do not
- `clearance_required` on the approve route is not validated in application
  code
- The app has not yet been scanned with SAST/DAST tools and has no automated
  tests

## Status / Roadmap

In progress:
- Refactoring route-level access checks into reusable decorators
- Refreshing the role from the database on each request

Planned:
- Audit log helper function, replacing repeated inserts
- SAST with Bandit, and DAST with OWASP ZAP; findings documented in the repo
- Automated tests with pytest
- Docker setup
- ERD and data dictionary for the schema

## Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create the database using `schema.sql`:
   ```bash
   mysql -u root -p < schema.sql
   ```
3. Create the least-privilege database user by running the statements in
   `DATABASE_PRIVILEGE.md` (replace the placeholder password).
4. Create a `.env` file in the project root. All five variables are required;
   the app will not start if any is missing:
   ```
   DB_HOST=localhost
   DB_USER=flask_app
   DB_PASSWORD=your_password
   DB_NAME=secure
   SECRET_KEY=your_flask_secret_key
   ```
   Generate a secret key with:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
5. Run the app:
   ```bash
   flask run
   ```
   Session cookies are set with the `Secure` flag, so run it behind HTTPS
   outside of local development.

## Author

Justine Lee G. Pineda, [github.com/leepineda](https://github.com/leepineda)
