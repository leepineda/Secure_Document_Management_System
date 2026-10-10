Changelog

All notable changes to this project are documented here.
Format: Added / Changed / Fixed / Removed / Security / Known Issues / Planned

## 1.0.6 
started 2026-10-04

Security
---
- Added approve webpages (admin only) non admins get prompted with a unauthorized access when clicking approve button.
- Extended the 1.0.5 per-request session validation to also check role, users are logged out if their account is deleted or deactivated, or if their role in the database no longer matches the session. Role changes now apply immediately instead of at next login
- Enforced one role per account (UNIQUE on user_roles.account_id)
- Changed the search query to only show username 
- Added a log_event() helper for security_audit_logs. Validates status before writing, and logs on its own connection so entries survive a rollback

Changed
---
- Removed Known Issues Entry: "Home and search routes expose all user accounts to any logged-in user on Known Issues" its a design decision and it only searches username nothing else 

Planned
---
- Convert the remaining audit-log inserts in login (and other routes) to log_event()
- Log login attempts on deleted accounts and unknown usernames
- IP-based rate limiting
- Add pytest tests
- Run SAST (Bandit) and DAST (OWASP ZAP); document findings
- Dockerize the app

Known Issues
---
- Audit log doesn't record failed logins for unknown usernames or deleted accounts, admin
  deletes, or 403 denials
- Logout is a GET request
- approve route doesn't validate clearance_required against allowed values
- Role checks exist only on delete and approve; add and search have none
- except pass still used in login rollback
- Register assigns the default role with a hardcoded role_id (3). It works because the seed order fixes user = 3, but it depends on that order and isn't readable; should look up "user" by role_name instead

## 1.0.5 2026-10-03 
Security
---
- Removed default fallbacks in get_connection() (user "root", empty password, "test_db"). Before: os.getenv("DB_USER", "root"). Now: os.environ["DB_USER"]. A missing or misspelled variable now stops the app instead of silently connecting as root, which would bypass the least-privilege flask_app account.
- Added a startup check that raises RuntimeError listing any missing environment variables (SECRET_KEY, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
- Login query now excludes soft-deleted accounts (is_deleted = FALSE), so deleted users can no longer log in. They get the same "Invalid credentials." response as unknown users.
- Locked-out accounts now run a dummy hash check before returning, so response time no longer reveals which accounts are locked. timing not yet measured 
- Added a before_request check that re-validates the logged-in account on every request; deleted or suspended accounts are logged out immediately. Verified by soft-deleting a logged-in test user.

Known Issues
---
- Home and search routes expose all user accounts to any logged-in user
- Audit log doesn't record failed logins for unknown usernames or deleted accounts, admin
  deletes, or 403 denials
- role_name is cached in the session, so role changes don't apply until the user logs in again
- Logout is a GET request
- approve route doesn't validate clearance_required against allowed values
- Role checks exist only on delete and approve; add and search have none
- except pass still used in login rollback

Planned
---
- Refresh role_name from the database on each request
- Add a log_event() helper to replace the repeated audit-log inserts
- Log login attempts on deleted accounts and unknown usernames
- IP-based rate limiting
- Add pytest tests
- Run SAST (Bandit) and DAST (OWASP ZAP); document findings
- Dockerize the app

## 1.0.4

Planned
---
- Clean up the app.py to use decorators, the code is getting big and messier
- Learn clean architecture
- Make the UI cleaner not just raw html
- Fix the pending, and add admin confidentiality check and assignment
- Fix up SELECT
- Fix up pass
- Fix the hash, the login route isnt consistent with the hashes, the lockout doesnt use a hash, it also needs to run the hash

Known Issues
---
- using an ENUM and assigning top secret 4, that looks good on logic but if someone sees this code like months, will they have an idea what does 4 even mean? 

Removed
- Removed confidentiality on add route, removed confidentiality and mfa required in register html
- Removed the status allocation on sql when registering, it all now auto goes to active default
- Removed trust_level in user_accounts -> refer to sept 5 entry

Added
- Database privileges


## 1.0.3
Added
---
- Added registration logs
- Added status column on documents
- Added status filter on Index to not show pending, and only show approved

Planned
---
- Fix the pending, and add admin confidentiality check and assignment
- Fix up SELECT
- Fix up pass

Known Issues 
- still using select
- using except pass

## 1.0.2
Added
---
- Added CSRF protection using Flask WTF\
- Added csrf token on state changing methods e.g POST method
- Added login_attempt and lockout_until attributes on user_accounts table
- Added a simple rate limiting lockout + login attempts for one account brute forcing
- Added logging 
- Added Login Logs
- Added for lockout import
- Added get_lockout_duration function
- Added connection.commit() on lockout (keep forgetting)
- Added Dummy hash so every user takes the same time to log, whether they exist or not

Fixed
---
- CSRF protection on destructive routes
- Fixed login, instead of fallback user role when it detects a null role, we throw an error instead
- Fixed get_lockout_duration not defined
- Fixed account_id not being defined at the top


Known Issues / Need fixing
---
- No proper logging
- using except pass:
- Logs need proper indentation and flow

Planned
---
- Restrict document creation by role
- Add login attempt logging to security_audit_logs
- Integrate SAST, DAST, etc... tools

## 1.0.1
Added
---
- Documents table on home route — all authenticated users can view all documents
- Add document route for creating new documents
- Soft deletes via is_deleted BOOLEAN DEFAULT FALSE both user_accounts and documents
- Application-layer role check on delete — non-admins receive 403
- Input whitelisting on username via regex (a-z, A-Z, 0-9, _)
- Role stored in session on login, cleared on logout
- Registration feedback — flash messages on success and error
- Login session check added on search route 
- All routes now all have login checks 
- Removed visibility of deleted users using WHERE is_deleted = FALSE
- Last logged in added on user_credentials / UPDATE
- Documents now have role and clearance check
- Documents = [] fallback in home route, prevents crash if role = unrecognized

Fixed
---
- Fixed register error handler, was returning raw string "Registration failed." instead of redirecting
- Fixed user_role, now correctly fetched from session.get("role_name")
- Fixed soft deletes now only updates is_deleted BOOLEAN

Known issues
---
- Documents visible to all authenticated users regardless of role, department, or clearance level
- Anyone can make documents, regarding role and attribute
- Security logs for now doesn't log login attempts only registration
- No CSRF protection on POST routes CSRF (Cross Site Request Forgery)
- SELECT * still used a lot
- No rate limiting 

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
- Created new user - not using root user anymore

Known Issues
---
- No authentication or password handling
- Root MySQL user still in use
- No input validation

## 0.1.0 Initial

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