# Secure Document Management System

A learning project building a security-focused document management system with
Flask and MySQL — with role-based access control, hardened authentication, and
a fully documented design history from first commit onward. Started May 2026,
in active development.

This isn't a tutorial clone. Every security control here was implemented,
broken, debugged, and re-reasoned through from scratch — the full history of
that process, including the mistakes, is documented in this repo rather than
hidden.

## Key Features

**Authentication & Session Security**
- Password hashing via Werkzeug (scrypt)
- Hardened session cookies (`HttpOnly`, `Secure`, `SameSite=Lax`)
- Session cleared and reissued on every login to prevent session fixation
- Implemented dummy-hash comparison to mitigate timing-based user enumeration on invalid-username login attempts

**Brute-Force Protection**
- Exponential account lockout on repeated failed logins
- Login attempts and lockouts logged with IP address

**CSRF Protection**
- Flask-WTF CSRF tokens on every state-changing route (POST/PUT/DELETE)

**Role-Based Access Control**
- Three roles (admin / moderator / user) with clearance-gated document access
- Application-layer authorization checks on every protected route

**Audit Logging**
- Append-only `security_audit_logs` table — logs actions, actor, IP, and
  outcome (ALLOWED / DENIED / ERROR)
- Enforced at the database layer: the app's MySQL user only has `INSERT` on
  this table, so even a compromised application can't tamper with the log

**Database-Layer Least Privilege**
- Dedicated MySQL service account (not root) scoped with per-table `GRANT`
  statements — e.g. `SELECT, INSERT, UPDATE` on `documents`, `INSERT`-only on
  `security_audit_logs` — see [`DATABASE_PRIVILEGE.md`](./DATABASE_PRIVILEGE.md)

**Data Integrity**
- Soft deletes (`is_deleted`) instead of hard deletes, to preserve audit trail
- Multi-table writes wrapped in transactions with commit/rollback so a failure
  partway through never leaves the database in a half-written state

## Tech Stack

- **Language:** Python
- **Backend:** Flask, Flask-WTF
- **Database:** MySQL / MariaDB
- **Auth:** Werkzeug (scrypt password hashing)
- **Config:** python-dotenv

## Project Structure

```
.
├── app.py                    # Main Flask application, routes
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

This project treats its documentation as part of the deliverable, not an
afterthought:

- **`CHANGELOG.MD`** — what changed, release by release, in standard
  Added/Changed/Fixed/Security format.
- **`DEVLOG.MD`** — the reasoning behind those changes: what broke, what was
  learned, what tradeoffs were considered. Cleaned up for readability.
- **`DEVLOG_raw.MD`** — the same journal in its original, unfiltered form,
  written in the moment. Kept for full transparency; expect informal language.
- **`schema_evolution.sql`** — every schema change in the order it actually
  happened, including the broken queries and the fixes.

## Status / Roadmap

Actively in development. Currently working on:
- Admin review workflow for pending documents
- Refactoring route-level access checks into reusable decorators

Planned:
- SAST integration (e.g. Bandit) on the codebase
- DAST scanning with OWASP ZAP against the running app
- Basic automated test coverage with pytest

## Setup

> Note: adjust the environment variable names below to match whatever your
> `.env` file actually uses — check `app.py` / `context.py` if unsure.

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create the database using `schema.sql`:
   ```bash
   mysql -u root -p < schema.sql
   ```
3. Set up a least-privilege database user by running the statements in
   `DATABASE_PRIVILEGE.md`.
4. Create a `.env` file with your database credentials, e.g.:
   ```
   DB_HOST=localhost
   DB_USER=flask_app
   DB_PASSWORD=your_password
   DB_NAME=secure
   SECRET_KEY=your_flask_secret_key
   ```
5. Run the app:
   ```bash
   python app.py
   ```

## Author

Justine Lee G. Pineda — [github.com/leepineda](https://github.com/leepineda)