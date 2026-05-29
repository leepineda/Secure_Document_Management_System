import os
import re #for regex expressions
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash #added scrypt import
from werkzeug.security import check_password_hash #for checking hash
import pymysql

load_dotenv()   # reads .env and puts values into os.environment

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

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
    #we added this block to fetch data from the users table
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user_accounts WHERE is_deleted = FALSE")
            user_accounts = cursor.fetchall()

            cursor.execute("SELECT * FROM documents WHERE is_deleted = FALSE")
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

#delete route, note that a route is like a function
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
    #need to a

@app.route("/add", methods = ["GET", "POST"])
def add():

    if "account_id" not in session:
        flash("You must be logged in to add a document.")
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form.get("title")
        content = request.form.get("content")
        clearance_required = request.form.get("clearance_required")

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
                cursor.execute(sql, (title, content, owner_id, department_id, clearance_required))

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

@app.route("/login", methods = ["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
    
        connection = get_connection()
        try:
            with connection.cursor() as cursor: #removed the filter status and added messages
                sql = """
                    SELECT ua.account_id, ua.status, uc.password_hash 
                    FROM user_accounts ua 
                    JOIN user_credentials uc ON ua.account_id = uc.account_id 
                    WHERE ua.username = %s
                """
                    
                cursor.execute(sql, (username,))
                user = cursor.fetchone()

                if user and check_password_hash(user["password_hash"], password) and user["status"] == "active":
                    account_id = user["account_id"] #added a active user check and store on session
                    #added a block that selects the role_name from database and saves it on the session
                    cursor.execute(
                            """
                            SELECT r.role_name FROM user_roles ur
                            JOIN roles r ON ur.role_id = r.role_id
                            WHERE ur.account_id = %s
                            """,
                            (user["account_id"],)
                        )
                    role = cursor.fetchone()
                    session["account_id"] = account_id
                    session["role_name"] = role["role_name"] if role else "user"

                    #added timestamp for last login in user_credentials
                    cursor.execute("UPDATE user_credentials SET last_login = NOW() WHERE account_id = %s", (account_id,))
                        
                    if user["status"] == "suspended":
                        flash("This account has been suspended. Please contact support.")
                        return redirect(url_for("login"))
                        
                    elif user["status"] == "pending":
                        flash("Your account registration is still pending approval.")
                        return redirect(url_for("login"))
                        
                    else:
                        flash("Account status abnormal. Access denied.")
                        return redirect(url_for("login"))
                else:
                    flash("Invalid username or password.")
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
                    "(email, username) "
                    "VALUES (%s, %s) ",
                    (email, username)
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

                cursor.execute(
                    "INSERT INTO security_audit_logs " #make a sec log
                    "(account_id, action_performed, resource_affected, ip_address, status) "
                    "VALUES (%s, %s, %s, %s, %s) ",
                    (
                        account_id,
                        "Account Registration",
                        "user_accounts",
                        request.remote_addr, #gets the ip address of the registered user
                        "ALLOWED"
                    )
                )

            connection.commit()
            flash("Registration Success! You can now log in.", "success")
            return redirect("/login")

        except pymysql.MySQLError as e:
            connection.rollback()
            print(f"Database error: {e}")
            flash("Registration Failed: Database error occurred.", "danger")
            return "Registration failed.", 500

        finally:
            connection.close()

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear() # added this instead of adding every attribute stored one by one
    
    flash("You have been successfully logged out.")
    
    return redirect(url_for("login"))

#initialize the application
if __name__ == "__main__":
    app.run(debug=False) #made false