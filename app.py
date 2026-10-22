import os
import re #for regex expressions
from functools import wraps #for the decorators
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash #added scrypt import
from werkzeug.security import check_password_hash #for checking hash
import pymysql
from flask_wtf.csrf import CSRFProtect #CSRF protection
from datetime import datetime, timedelta #for lockout
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()   # reads .env and puts values into os.environment

required = ["SECRET_KEY", "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"] #checks if the environment variables are right
missing = [v for v in required if not os.getenv(v)]
if missing:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

#added this so real IP addresses gets used
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

app.secret_key = os.getenv("SECRET_KEY")

csrf = CSRFProtect(app)

DUMMY_HASH = generate_password_hash("DAHkoldpadkadpwdbadwuBUy12139@#!2373modkaojdouw---391-dad") #added this to use for anti Timing Attack

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

#Sql connection
def get_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )

VALID_ROLES = {"admin", "moderator", "user"}
DEFAULT_ROLE = "user" #role every new registration gets, looked up by NAME not by id
VALID_CLEARANCES = {"public", "internal", "confidential", "top_secret"} #must match the clearance_required ENUM in the schema

def roles_required(*allowed_roles):
    """Decorator: the route runs only if the user is logged in AND their role is in allowed_roles.
    One place for the rule, so a route can't forget it.
    """
    def decorator(view):
        @wraps(view) #keeps the original function name, Flask uses it as the endpoint name
        def wrapped(*args, **kwargs):
            if "account_id" not in session:
                return redirect(url_for("login")) #no flash here, a flash on a page that never shows it leaks to the next page

            if session.get("role_name") not in allowed_roles:
                try_log_event("Unauthorized Access", "DENIED", session["account_id"], resource=request.endpoint)
                return "Unauthorized: You do not have permission to perform this action.", 403

            return view(*args, **kwargs)
        return wrapped
    return decorator

@app.before_request #this function validates the user if they are deleted or not, and also to for checking roles
def check_session_still_valid():

    if request.endpoint in ("login", "register", "logout", "static", "add", "approve", "index", "search"):
        return
 
    if "account_id" not in session:
        return
 
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            #LEFT JOINs and no is_deleted filter, so we can tell WHY the session is no longer valid
            cursor.execute(
                "SELECT ua.status, ua.is_deleted, r.role_name "
                "FROM user_accounts ua "
                "LEFT JOIN user_roles ur ON ur.account_id = ua.account_id "
                "LEFT JOIN roles r ON r.role_id = ur.role_id "
                "WHERE ua.account_id = %s",
                (session["account_id"],)
            )
            user = cursor.fetchone()
    except Exception as e:
        print(f"Session check error: {e}")
        session.clear()
        return redirect(url_for("login"))
    finally:
        connection.close()
 
    #work out the reason, the first match wins (None = the session is still valid)
    reason = None
    if not user:
        reason = "Account Not Found"
    elif user["is_deleted"]:
        reason = "Account Deleted"
    elif user["status"] != "active":
        reason = "Account Not Active"
    elif user["role_name"] is None:
        reason = "No Role Assigned"
    elif user["role_name"] not in VALID_ROLES:
        reason = "Invalid Role"
    elif user["role_name"] != session.get("role_name"):
        reason = f"Role Changed ({session.get('role_name')} to {user['role_name']})"
 
    if reason:
        #log BEFORE clearing, session["account_id"] is gone after session.clear()
        try_log_event(f"Session Ended: {reason}", "DENIED", session["account_id"], resource="session")
        session.clear()
        flash("Your session has ended. Please log in again.", "error")
        return redirect(url_for("login"))

@app.route("/")
@roles_required("admin", "moderator", "user")
def home():

    user_role = session["role_name"]
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            documents = []
            user_accounts = []

            if user_role == "admin":
                cursor.execute("SELECT account_id, username, email, status FROM user_accounts WHERE is_deleted = FALSE")
                user_accounts = cursor.fetchall()
                cursor.execute("SELECT * FROM documents WHERE is_deleted = FALSE")

            elif user_role == "moderator":
                cursor.execute("SELECT * FROM documents WHERE is_deleted = FALSE AND clearance_required IN ('public', 'internal') AND status IN ('approved')")

            elif user_role == "user":
                cursor.execute("SELECT * FROM documents WHERE is_deleted = FALSE AND clearance_required IN ('public') AND status IN ('approved')")

            documents = cursor.fetchall()

    except Exception as e:
        print(f"Database error occured: {e}")
        return "An error occurred: index.", 500

    finally:
        connection.close()
    #until here
    return render_template("index.html", user_accounts=user_accounts, documents=documents)

#add a search route sql syntax still
@app.route("/search")
@roles_required("admin", "moderator", "user")
def search():

    query = request.args.get("q", "")   # reads ?q=Alice from the URL
    connection = get_connection()
    results = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT username FROM user_accounts "
                "WHERE username LIKE %s AND status = 'active' AND is_deleted = FALSE",
                (f"%{query}%",)
            )
            results = cursor.fetchall()

    except Exception as e:
        print(f"Database error occured: {e}")
        return "An error occurred while searching.", 500

    finally:
        connection.close()

    return render_template("search.html", results=results, query=query)

#delete
@app.route("/delete/<int:account_id>", methods=["POST"])
@roles_required("admin")
def delete_user(account_id):

    if account_id == session["account_id"]:
        return "You cannot delete your own account.", 400

    connection = get_connection()
    try:
        with connection.cursor() as cursor: #made delete only update to introduce soft deletes
            cursor.execute(
                "UPDATE user_accounts "
                "SET is_deleted = TRUE "
                "WHERE account_id = %s ",
                (account_id,)
            )

            if cursor.rowcount== 0:
                return "User not found or already deleted", 404

            log_event("Delete User Account", "ALLOWED", session["account_id"], resource="user_accounts", connection=connection)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print (f"Database error occured: {e}")
        try_log_event("Delete User Account", "ERROR", session["account_id"], resource="user_accounts")
        return "An error occured while deleting a user.", 500

    finally:
        connection.close()

    return redirect("/")


@app.route("/add", methods = ["GET", "POST"])
@limiter.limit("10 per minute")
@roles_required("admin", "moderator", "user")
def add():

    if request.method == "POST":

        title = request.form.get("title")
        content = request.form.get("content")

        department_id = request.form.get("department_id")
        if department_id == "":
            department_id = None

        if not title:
            flash("Title is required")
            return render_template("add.html")

        owner_id = session["account_id"]

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO documents (title, content, owner_id, department_id)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (title, content, owner_id, department_id))

            log_event("Document Creation Successful", "ALLOWED", session["account_id"], resource="documents", connection=connection)
            connection.commit()
            flash("Document added successfully!")
            return redirect(url_for("home"))

        except Exception as e:
            connection.rollback()
            print(f"Error {e}")
            try_log_event("Document Creation Failed", "ERROR", session["account_id"], resource="documents")
            flash("An error occurred while saving the document. Please try again.")

        finally:
            connection.close()

    return render_template("add.html")

def get_lockout_duration(attempts):
    if attempts >= 10:
        return datetime.now() + timedelta(minutes=30)
    elif attempts >= 5:
        return datetime.now() + timedelta(minutes=5)
    else:
        return None

@app.route("/login", methods = ["GET", "POST"])
@limiter.limit("5 per minute")
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                #no is_deleted filter in the WHERE anymore, so we can tell a deleted account apart from an unknown username (for the audit log)
                sql = """
                    SELECT ua.account_id, ua.status, ua.is_deleted, uc.password_hash, ua.login_attempts, ua.lockout_until
                    FROM user_accounts ua
                    JOIN user_credentials uc ON ua.account_id = uc.account_id
                    WHERE ua.username = %s
                """

                cursor.execute(sql, (username,))
                user = cursor.fetchone()

                if not user:
                    check_password_hash(DUMMY_HASH, password) #here so even if a user doesnt exist they still check the hash so same time fot every user whether they exist or not
                    try_log_event("Login Unknown Username", "DENIED", None, resource="user_accounts") #no account to attach it to, the IP is still recorded
                    flash('Invalid credentials.', 'error')
                    return redirect(url_for('login'))

                account_id = user["account_id"]

                if user["is_deleted"]:
                    check_password_hash(DUMMY_HASH, password) #same timing as every other failure
                    try_log_event("Login Deleted Account", "DENIED", account_id, resource="user_accounts")
                    flash("Invalid credentials.", "error")
                    return redirect(url_for("login"))

                if user["lockout_until"] and datetime.now() < user["lockout_until"]:
                    check_password_hash(DUMMY_HASH, password) #now also checks the hash
                    try_log_event("Login Locked Account", "DENIED", account_id, resource="user_accounts")
                    flash("Invalid credentials.", "error")
                    return redirect(url_for("login"))

                if not check_password_hash(user["password_hash"], password):
                    new_attempts = user["login_attempts"] + 1
                    lockout_until = get_lockout_duration(new_attempts) if new_attempts >= 5 else None

                    cursor.execute(
                    "UPDATE user_accounts SET login_attempts = %s, lockout_until = %s WHERE account_id = %s",
                    (new_attempts, lockout_until, user["account_id"])
                    )
                    connection.commit()

                    try_log_event("Login Wrong Credentials", "DENIED", account_id, resource="user_accounts")
                    flash("Invalid credentials.", "error")
                    return redirect(url_for("login"))

                # only after if match we check status
                if user["status"] == "suspended":
                    try_log_event("Login Suspended Account", "DENIED", account_id, resource="user_accounts")
                    flash("Invalid credentials.", "error")
                    return redirect(url_for("login"))

                elif user["status"] == "pending":
                    try_log_event("Login Pending Account", "DENIED", account_id, resource="user_accounts")
                    flash("Your account registration is still pending approval.", "error")
                    return redirect(url_for("login"))

                elif user["status"] != "active":  #if ever the status gets tampered and not on the status ENUM
                    try_log_event("Login Non Active Account", "DENIED", account_id, resource="user_accounts")
                    flash("Account status abnormal. Access denied.", "error")
                    return redirect(url_for("login"))


                #if everythings successfull reset login_attempts and lockout_until
                cursor.execute(
                "UPDATE user_accounts SET login_attempts = 0, lockout_until = NULL WHERE account_id = %s",
                (account_id,)
                )

                cursor.execute(
                    "UPDATE user_credentials SET last_login = NOW() WHERE account_id = %s",
                    (account_id,)
                )
                connection.commit()

                cursor.execute(
                    """
                    SELECT r.role_name FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.role_id
                    WHERE ur.account_id = %s
                    """,
                    (account_id,)
                )

                role = cursor.fetchone() #returns a dictionary of role_name and the value and if its not found its role = none
                #if role is none it redirects to the login
                if not role:
                    try_log_event("Login Role Not Found", "ERROR", account_id, resource="user_accounts")
                    flash("Account configuration error. Please contact support.", "error")
                    return redirect(url_for("login"))

                #the success log is written BEFORE the session is created, if the log fails the login fails too (no log, no access)
                log_event("Login Success", "ALLOWED", account_id, resource="user_accounts")

                session.clear() #clear any remaining session and make a new one
                session["account_id"] = account_id
                session["role_name"] = role["role_name"]

                flash("Logged in Successfully", "success")

                return redirect(url_for("home"))

        except Exception as e:
            print(f"Database error: {e}")
            flash("An error occurred during login. Please try again.", "danger")
            try:
                connection.rollback()
            except Exception as rollback_error: #was a bare "except: pass", now the failure is at least visible
                print(f"Rollback error: {rollback_error}")
            return redirect(url_for("login"))

        finally:
            connection.close()

    return render_template("login.html")

@app.route("/register", methods =["GET", "POST"])
@limiter.limit("5 per hour")
#came backk
def register():

    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "error")
            return render_template("register.html")

        if not re.match(r"^[a-zA-Z0-9_]+$", username): #whitelisting a-z and capital A-Z 0-9 and underscores
            flash("Username can only contain letters, numbers, and underscores.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password) # we use scrypt here and hash teh pass before inserting onto database

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_accounts " #user registers here
                    "(email, username) " # status omitted — database defaults to 'active' for now
                    "VALUES (%s, %s) ",
                    (email, username) #
                )

                account_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO user_credentials "
                    "(account_id, password_hash) "
                    "VALUES (%s, %s) ",
                    (account_id, password_hash)
                )

                #the role is looked up by NAME, no more hardcoded role_id 3 that depends on the seed order
                cursor.execute(
                    "INSERT INTO user_roles "
                    "(account_id, role_id) "
                    "SELECT %s, role_id FROM roles WHERE role_name = %s",
                    (account_id, DEFAULT_ROLE)
                )

                if cursor.rowcount != 1: #the SELECT found no role with that name, so nothing was inserted
                    raise RuntimeError(f"Default role '{DEFAULT_ROLE}' not found in roles table")

            #the log is written inside the same transaction, so the account and its log are saved together or not at all
            log_event("Account Registration", "ALLOWED", account_id, resource="user_accounts", connection=connection)
            connection.commit()

            flash("Registration Success! You can now log in.", "success")
            return redirect("/login")

        except pymysql.err.IntegrityError as e:
            connection.rollback()

            #account_id is None on purpose: the rollback removed that account row, so a log pointing at it would break the foreign key
            try_log_event("Account Registration Failed", "DENIED", None, resource="user_accounts")

            flash ("Email or username is already taken.", "error")
            return redirect(url_for("register"))

        except Exception as e:
            connection.rollback()
            print(f"Registration error: {e}")
            try_log_event("Account Registration Error", "ERROR", None, resource="user_accounts")

            flash("Registration Failed: An error occurred.", "danger")
            return redirect(url_for("register"))

        finally:
            connection.close()

    return render_template("register.html")

@app.route("/logout", methods=["POST"]) #POST + CSRF token, a plain link can no longer log someone out
def logout():
    session.clear()

    flash("You have been successfully logged out.", "success")

    return redirect(url_for("login"))

@app.route("/approve", methods=["GET"])
@roles_required("admin")
def approve_page():

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT document_id, title FROM documents WHERE status = 'pending'"
            )
            documents = cursor.fetchall()
    finally:
        connection.close()

    return render_template("approve.html", documents=documents)

@app.route("/approve/<int:document_id>", methods=["POST"])
@roles_required("admin")
def approve(document_id):

    clearance_required = request.form.get("clearance_required")
    if clearance_required not in VALID_CLEARANCES:
        flash("Confidentiality level is required.", "error")
        return redirect(url_for("home"))

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # Update the document status from pending to approved and change confidentiality
            sql = """
                UPDATE documents
                SET status = 'approved', clearance_required = %s
                WHERE document_id = %s AND status = 'pending'
            """
            cursor.execute(sql, (clearance_required, document_id))

            # Verify if the document was actually found and updated
            if cursor.rowcount == 0:
                flash("Document not found or it is already approved.", "error")
                return redirect(url_for("home"))

            # Log the successful action to your security audit logs
            log_event("Approved Document", "ALLOWED", session["account_id"], resource="documents", connection=connection)

        connection.commit()
        flash("Document approved and confidentiality updated successfully!", "success")

    except Exception as e:
        connection.rollback()
        print(f"Database error occurred: {e}")
        try_log_event("Approve Document Fail", "ERROR", session["account_id"], resource="documents")
        flash("An error occurred while approving the document.", "error") #before this the admin saw nothing when it failed

    finally:
        connection.close()

    return redirect(url_for("home"))

VALID_LOG_STATUSES = {"ALLOWED", "DENIED", "ERROR"}

def log_event(action, status, account_id, resource=None, connection=None):
    """Write one row to security_audit_logs.

    Pass connection to join an existing transaction; otherwise the log
    is written on its own connection so it survives a rollback.
    """
    if status not in VALID_LOG_STATUSES:
        raise ValueError(f"Invalid audit status: {status}")

    own_connection = connection is None
    if own_connection:
        connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO security_audit_logs "
                "(account_id, action_performed, resource_affected, ip_address, status) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    account_id,
                    action[:100],
                    resource[:100] if resource else None,
                    (request.remote_addr or "")[:45] or None,
                    status,
                ),
            )
        if own_connection:
            connection.commit()
    except Exception as e:
        print(f"Audit log error: {e}")
        raise
    finally:
        if own_connection:
            connection.close()

def try_log_event(*args, **kwargs):
    """Best-effort version of log_event for denial and error paths.

    The request is already being denied or has already failed, so a broken
    audit log must not turn that into a second crash. The error is printed.
    """
    try:
        log_event(*args, **kwargs)
    except Exception as e:
        print(f"Audit log failed (best effort): {e}")

@app.errorhandler(429)
def ratelimit_handler(e):
    # Log the IP rate limit violation using your existing helper
    try_log_event("IP Rate Limit Exceeded", "DENIED", session.get("account_id"), resource=request.endpoint)
    
    flash(f"Rate limit exceeded: {e.description}", "error")
    # Redirect to home if logged in, otherwise back to login
    if "account_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

#initialize the application
if __name__ == "__main__":
    app.run(debug=False) #made false