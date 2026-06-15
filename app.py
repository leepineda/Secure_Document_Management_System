import os
import re #for regex expressions
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash #added scrypt import
from werkzeug.security import check_password_hash #for checking hash
import pymysql
from flask_wtf.csrf import CSRFProtect #CSRF protection
from datetime import datetime, timedelta #for lockout

load_dotenv()   # reads .env and puts values into os.environment

app = Flask(__name__)

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
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "test_db"),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/")
def home():

    if 'account_id' not in session: #removed the flash since it doesnt show it and also leaks the flash message to the register function and also its gonna get redirected if they arent in session
        return redirect(url_for("login"))

    current_user_id = session['account_id'] #if they are logged in take their data
    user_role = session["role_name"]
    connection = get_connection()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user_accounts WHERE is_deleted = FALSE" )
            user_accounts = cursor.fetchall()

            documents = []

            if user_role == "admin":
                cursor.execute("SELECT * FROM documents WHERE is_deleted = FALSE")

            elif user_role == "moderator":
                cursor.execute("SELECT * FROM documents WHERE is_deleted = FALSE AND clearance_required IN ('public', 'internal') AND status IN ('approved')")
            
            elif user_role == "user":
                cursor.execute("SELECT * FROM documents WHERE is_deleted = FALSE AND clearance_required IN ('public') AND status IN ('approved')")

            documents = cursor.fetchall()
        
    except Exception as e:
        print(f"Database error occured: {e}")
        return "An error occurred: index.", 400

    finally:    
        connection.close()
    #until here
    return render_template("index.html", user_accounts=user_accounts, documents=documents)

#add a search route sql syntax still
@app.route("/search") 
def search():

    if "account_id" not in session:
        flash("You must be logged in to add a document.")
        return redirect(url_for("login"))

    query = request.args.get("q", "")   # reads ?q=Alice from the URL
    connection = get_connection()
    results = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_accounts WHERE username LIKE %s ",
                (f"%{query}%",)
            )
            results = cursor.fetchall()

    except Exception as e:
        print(f"Database error occured: {e}")
        return "An error occurred while searching.", 400

    finally:    
        connection.close()

    return render_template("search.html", results=results, query=query)

#delete
@app.route("/delete/<int:account_id>", methods=["POST"])
def delete_user(account_id):

    if session.get("role_name") != "admin":
        return "Unauthorized: You do not have permission to perform this action.", 403

    connection = get_connection()
    try:
        with connection.cursor() as cursor: #made delete only update to introduce soft deletes
            cursor.execute(
                "UPDATE user_accounts "
                "SET is_deleted = TRUE "
                "WHERE account_id = %s ", 
                (account_id,)
            )

        connection.commit()

    except Exception as e:
        connection.rollback()
        print (f"Database error occured: {e}")
        return "An error occured while deleting a user.", 500

    finally:
        connection.close()

    return redirect("/")


@app.route("/add", methods = ["GET", "POST"])
def add():

    if "account_id" not in session:
        flash("You must be logged in to add a document.")
        return redirect(url_for("login"))

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
                    INSERT INTO documents (title, content, owner_id, department_id, clearance_required)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (title, content, owner_id, department_id, 4))

            connection.commit()
            flash("Document added successfully!")
            return redirect(url_for("home"))

        except Exception as e:
            connection.rollback()
            flash("An error occurred while saving the document. Please try again.")
            print(f"Error {e}")
        
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
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
    
        connection = get_connection()
        try:
            with connection.cursor() as cursor: 
                sql = """
                    SELECT ua.account_id, ua.status, uc.password_hash, ua.login_attempts, ua.lockout_until
                    FROM user_accounts ua 
                    JOIN user_credentials uc ON ua.account_id = uc.account_id 
                    WHERE ua.username = %s
                """
                    
                cursor.execute(sql, (username,))
                user = cursor.fetchone()

                if not user:
                    check_password_hash(DUMMY_HASH, password) #here so even if a user doesnt exist they still check the hash so same time fot every user whether they exist or not
                    flash('Invalid credentials.', 'error')
                    return redirect(url_for('login'))

                account_id = user["account_id"]

                if user["lockout_until"] and datetime.now() < user["lockout_until"]:
                    cursor.execute(
                        "INSERT INTO security_audit_logs "
                        "(account_id, action_performed, resource_affected, ip_address, status) "
                        "VALUES (%s, %s, %s, %s, %s) ",
                        (
                            account_id,
                            "Login Locked Account",
                            "user_accounts",
                            request.remote_addr,
                            "DENIED"
                        )
                    )
                    connection.commit()
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

                    cursor.execute(
                        "INSERT INTO security_audit_logs "
                        "(account_id, action_performed, resource_affected, ip_address, status) "
                        "VALUES (%s, %s, %s, %s, %s) ",
                        (
                            account_id,
                            "Login Wrong Credentials",
                            "user_accounts",
                            request.remote_addr,
                            "DENIED"
                        )
                    )
                    connection.commit()
                    flash("Invalid credentials.", "error")
                    return redirect(url_for("login"))
                    
                # only after if match we check status
                if user["status"] == "suspended":
                    cursor.execute(
                        "INSERT INTO security_audit_logs "
                        "(account_id, action_performed, resource_affected, ip_address, status) "
                        "VALUES (%s, %s, %s, %s, %s) ",
                        (
                            account_id,
                            "Login Suspended Account",
                            "user_accounts",
                            request.remote_addr,
                            "DENIED"
                        )
                    )
                    connection.commit()
                    flash("Invalid credentials.", "error")
                    return redirect(url_for("login"))

                elif user["status"] == "pending":
                    cursor.execute(
                        "INSERT INTO security_audit_logs "
                        "(account_id, action_performed, resource_affected, ip_address, status) "
                        "VALUES (%s, %s, %s, %s, %s) ",
                        (
                            account_id,
                            "Login Pending Account",
                            "user_accounts",
                            request.remote_addr,
                            "DENIED"
                        )
                    )
                    connection.commit()
                    flash("Your account registration is still pending approval.", "error")
                    return redirect(url_for("login"))

                elif user["status"] != "active":  #if ever the status gets tampered and not on the status ENUM
                    cursor.execute(
                        "INSERT INTO security_audit_logs "
                        "(account_id, action_performed, resource_affected, ip_address, status) "
                        "VALUES (%s, %s, %s, %s, %s) ",
                        (
                            account_id,
                            "Login Non Active User",
                            "user_accounts",
                            request.remote_addr,
                            "DENIED"
                        )
                    )
                    connection.commit()
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
                    cursor.execute(
                        "INSERT INTO security_audit_logs "
                        "(account_id, action_performed, resource_affected, ip_address, status) "
                        "VALUES (%s, %s, %s, %s, %s) ",
                        (
                            account_id,
                            "Login Role Not Found",
                            "user_accounts",
                            request.remote_addr,
                            "ERROR"
                        )
                    )
                    connection.commit()
                    flash("Account configuration error. Please contact support.", "error")
                    return redirect(url_for("login"))
                
                session.clear() #clear any remaining session and make a new one
                session["account_id"] = account_id
                session["role_name"] = role["role_name"]
                
                flash("Logged in Successfully", "success")

                cursor.execute(
                    "INSERT INTO security_audit_logs "
                    "(account_id, action_performed, resource_affected, ip_address, status) "
                    "VALUES (%s, %s, %s, %s, %s) ",
                    (
                        account_id,
                        "Login Success",
                        "user_accounts",
                        request.remote_addr,
                        "ALLOWED"
                    )
                )
                
                connection.commit()

                return redirect(url_for("home")
                )

        except Exception as e:  
            print(f"Database error: {e}")
            flash("An error occurred during login. Please try again.", "danger")
            try:
                connection.rollback()
            except:
                pass
            return redirect(url_for("login"))

        finally:
            connection.close()

    return render_template("login.html")

@app.route("/register", methods =["GET", "POST"])
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
                    "(email, username, status) "
                    "VALUES (%s, %s, %s) ",
                    (email, username, 1) #also
                )

                account_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO user_credentials "
                    "(account_id, password_hash) "
                    "VALUES (%s, %s) ",
                    (account_id, password_hash)
                )

                cursor.execute( #insert role 
                    "INSERT INTO user_roles "
                    "(account_id, role_id) "
                    "VALUES (%s, %s) ",
                    (account_id, 3)
                )
            connection.commit()

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                            "INSERT INTO security_audit_logs "
                            "(account_id, action_performed, resource_affected, ip_address, status) "
                            "VALUES (%s, %s, %s, %s, %s) ",
                            (
                                account_id,
                                "Account Registration",
                                "user_accounts",
                                request.remote_addr, 
                                "ALLOWED"
                            )
                        )
                connection.commit()
            except Exception as e:
                print (f"Audit log error (success): {e}")

            flash("Registration Success! You can now log in.", "success")
            return redirect("/login")

        except pymysql.err.IntegrityError as e:
            connection.rollback()

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO security_audit_logs "
                        "(account_id, action_performed, resource_affected, ip_address, status) "
                        "VALUES (%s, %s, %s, %s, %s) ",
                        (
                            None,
                            "Account Registration Failed",
                            "user_accounts",
                            request.remote_addr,
                            "DENIED"
                        )
                    )
                connection.commit()
            except Exception as log_error:
                print(f"Audit log error (duplicate): {log_error}")

            flash ("Email or username is already taken.", "error")
            return redirect(url_for("register"))

        except pymysql.MySQLError as e:
            connection.rollback()

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO security_audit_logs "
                        "(account_id, action_performed, resource_affected, ip_address, status) "
                        "VALUES (%s, %s, %s, %s, %s) ",
                        (
                            None,
                            "Account Registration Error",
                            "user_accounts",
                            request.remote_addr,
                            "ERROR"
                        )
                    )
                connection.commit()
            except Exception as log_error:
                print(f"Audit log error (db error): {log_error}")

            print(f"Database error: {e}")
            flash("Registration Failed: Database error occurred.", "danger")
            return redirect(url_for("register"))

        finally:
            connection.close()

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear() # added this instead of adding every attribute stored one by one
    
    flash("You have been successfully logged out.", "success")
    
    return redirect(url_for("login"))

#@app.route("/approve", methods = ["POST", "PUT"])
#def approve():
    
    #if request.method == "PUT"


#initialize the application
if __name__ == "__main__":
    app.run(debug=False) #made false