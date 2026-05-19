import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect
import pymysql

load_dotenv()   # reads .env and puts values into os.environment

app = Flask(__name__)

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
    #we added this block to fetch data from the users table
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
    connection.close()
    #until here
    return render_template("index.html", users=users)

#add a search route sql syntax still
@app.route("/search")
def search():
    query = request.args.get("q", "")   # reads ?q=Alice from the URL
    connection = get_connection()
    results = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE name LIKE %s",
                (f"%{query}%",)
            )
            results = cursor.fetchall()

    except Exception as e:
        print(f"Database error occured: {e}")
        return "An error occurred while searching.", 400

    finally:    
        connection.close()

    return render_template("search.html", results=results, query=query)

#add a post Route ADDING/CREATING
@app.route("/add", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form["name"]    # reads from the form
        email = request.form["email"]

        connection = get_connection()
        try: #changed the logic to use a try catch error or a transaction equivalent
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (name, email) VALUES (%s, %s)",
                    (name, email)
                )
                new_user_id = cursor.lastrowid 

                cursor.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (new_user_id, 3)
                )

            connection.commit()   #save the change AFTER its done
            return redirect("/")  # go back to home page IF THE TRANSACTION IS SUCNESFUL

        except Exception as e:
            connection.rollback() #rollback when the transaction fails
            print(f"Database error occured: {e}")
            return "An error occurred while creating the user.", 500

        finally:    
            connection.close()
           
    return render_template("add.html")
    #add redirect import at the top 

#delete route, note that a route is like a function
@app.route("/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

        connection.commit()

    except Exception as e:
        connection.rollback()
        print (f"Database error occured: {e}")
        return "An error occured while deleting a user.", 500

    finally:
        connection.close()

    return redirect("/")

#initialize the application
if __name__ == "__main__":
    app.run(debug=False) #made false