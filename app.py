from flask import Flask, render_template, request, redirect, url_for, session, jsonify 
from flask_mysqldb import MySQL
import os 
from datetime import date
import json 
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

app = Flask(__name__)

# Use Railway's environment variables for MySQL

app.config["MYSQL_HOST"] = os.environ.get("MYSQLHOST")
app.config["MYSQL_USER"] = os.environ.get("MYSQLUSER")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQLPASSWORD")
app.config["MYSQL_DB"] = os.environ.get("MYSQLDATABASE")
app.config["MYSQL_PORT"] = int(os.environ.get("MYSQLPORT", 3306))  # default to 3306 if not provided
"""
app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'

app.config["MYSQL_DB"] = 'life'
"""

app.config['SECRET_KEY'] = os.urandom(24)
# Create mysql obkect
mysql = MySQL(app)

# Sign in page
@app.route("/")
def home():
    return render_template("sign_in.html")


# Sending data to sign in
@app.route("/sign_in_data", methods=["POST"])
def sign_in_data():
    if request.method == "POST":
        cursor = mysql.connection.cursor()
        name = request.form["username"]
        password = request.form["password"]

        try:
            cursor.execute("SELECT id FROM user WHERE username = %s AND password = %s", (name, password))
            user = cursor.fetchone()
            cursor.close()
            #print(user)
            if user: 
               # print("In sign_in_data:",user[0])
                session["user_id"] = user[0]
                return redirect(url_for("dashboard"))
            else:
                #print("Invalid")
                return "Failed"
        except Exception as e:
            print("Error", str(e))
    return redirect(url_for("home"))

# Sign up page
@app.route("/sign_up_page")
def sign_up_page():
    return render_template("sign_up.html")

# Sending data to sign up
@app.route("/sign_up_data", methods=["POST"])
def sign_up_data():
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        try:
            with mysql.connection.cursor() as cursor:
                cursor.execute("INSERT INTO user (name, username, password) VALUES (%s, %s, %s)", (name, username, password))
                mysql.connection.commit()
            return redirect(url_for("home"))
        except Exception as e:
            #print(str(e))
            return "Sign up failure"
    return "Invalid request method"

def convert_date_to_str(row):
    row_list = list(row)
    row_list[4] = row_list[4].strftime('%Y-%m-%d')
    return row_list

# User dashboard
@app.route("/dashboard", methods=["GET"])
def dashboard():

    user_id = session.get('user_id')
    print("In dashboard:",user_id)

    if user_id:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE id = %s', (user_id,))
        user_data = cursor.fetchone()

        cursor.execute('SELECT * FROM habits WHERE id = %s', (user_id,))
        habit_data = cursor.fetchall()
        session["habit_data"] = habit_data
        cursor.close()
        #print(habit_data)
        if user_data:
            #print("Data grab successfully and transferred over")
            
            if user_data[4] == 0:
                return render_template('add_habit.html', user_data=user_data[1], habit_data=habit_data, status=user_data[4])
            else:
                cleaned_habit_data = [convert_date_to_str(row) for row in habit_data]
                habit_data_json = json.dumps(cleaned_habit_data)
                
                predict_habit = machine_learning_integration(user_id)
                
                result = display_result(predict_habit)
                #print(result)
                return render_template('dashboard.html', user_data=user_data[1], habit_data = habit_data, data=habit_data_json, status=user_data[4],prediction=result)
    return redirect(url_for("home"))


@app.route("/create_habit", methods=["POST"])
def create_habit():
    if request.method == "POST":
        habit1 = request.form["habit1"]
        habit2 = request.form["habit2"]
        habit3 = request.form["habit3"]
        user_id = session.get("user_id")
        today = date.today()
        
        try:
            with mysql.connection.cursor() as cursor:
                cursor.execute("INSERT INTO habits (habit_1_name, habit_2_name, habit_3_name, id, habit_date) VALUES (%s, %s, %s, %s, %s)", (habit1, habit2, habit3, user_id, today))
                mysql.connection.commit()
                cursor.execute("UPDATE user SET new_status = 1 WHERE id = %s", (user_id,))
                mysql.connection.commit()
            return redirect(url_for("dashboard"))
        except Exception as e:
            print(str(e))
            mysql.connection.rollback()
        
        return "Failed to create habit"

    return "Invalid request method"


@app.route("/send_habit", methods=["GET", "POST"])
def send_habit():

    # Grab data
    today = date.today()
    user_id = session.get("user_id")
    habit1 = request.form.get("habit1")
    habit2 = request.form.get("habit2")
    habit3 = request.form.get("habit3")
    habit_data = session["habit_data"]

    # Check for values and add T or F
    habit1 = True if habit1 == "checked" else False
    habit2 = True if habit2 == "checked" else False
    habit3 = True if habit3 == "checked" else False

    print(habit1)
    print(habit2)
    print(habit3)
    print(today)
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM habits WHERE id = %s AND habit_date = %s", (user_id, today))
            data = cursor.fetchone()

            # Check if data exists
            if data:
                cursor.execute("UPDATE habits SET habit_1 = %s, habit_2 = %s, habit_3 = %s WHERE id = %s AND habit_date = %s", (habit1, habit2, habit3, user_id, today))
                mysql.connection.commit()
            else:
                cursor.execute("INSERT INTO habits (habit_1, habit_2, habit_3, habit_1_name, habit_2_name, habit_3_name, id, habit_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (habit1, habit2, habit3, habit_data[0][6], habit_data[0][7], habit_data[0][8], user_id, today))
                mysql.connection.commit()

    except Exception as e:
        print(str(e))
        mysql.connection.rollback()

    return redirect(url_for('dashboard'))  # Assuming your dashboard function is named 'dashboard'


def machine_learning_integration(id):
    cursor = mysql.connection.cursor()
    user_id = id
   #print(user_id)
    cursor.execute("SELECT COUNT(*) FROM habits WHERE id = %s", (user_id,))
    count = cursor.fetchone()
    print('Line 193',count)
    if count[0] >= 7:
        cursor.execute("SELECT * FROM habits WHERE id = %s", (user_id,))
        habit_data = cursor.fetchall()
        #print(habit_data)


        data_list = list(habit_data)
        column1 = []
        column2 = []
        column3 = []
        column_date = []
        is_completed = []
        for data in data_list:
            column1.append(data[1])
            column2.append(data[2])
            column3.append(data[3])
            column_date.append(data[4])
            if data[1] == 1 and data[2] == 1 and data[3] == 1:
                is_completed.append(1)
            else:
                is_completed.append(0)

        # Construct the dataframe
        data = {
            'Year': [d.year for d in column_date],
            'Month': [d.month for d in column_date],
            'Day': [d.day for d in column_date],
            'DayOfWeek': [d.weekday() for d in column_date],
            'Habit_1': column1,
            'Habit_2': column2,
            'Habit_3': column3,
            'Is_completed': is_completed
        }
        
        df = pd.DataFrame(data)

        # Split the data into training and testing sets
        X = df.drop('Is_completed', axis=1)
        y = df['Is_completed']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    
        # Train the classifier
        classifier = RandomForestClassifier(n_estimators=100, random_state=0)
        classifier.fit(X_train, y_train)

        # Predict on the test set
        y_pred = classifier.predict(X_test)

        # Predict for the next day
        today = date.today()
        next_day = {
            'Year': [today.year],
            'Month': [today.month],
            'Day': [today.day + 1],
            'DayOfWeek': [(today.weekday() + 1) % 7],
            'Habit_1': [0],  # Assumed values, replace as needed
            'Habit_2': [0],  # Assumed values, replace as needed
            'Habit_3': [0]   # Assumed values, replace as needed
        }
        next_day_df = pd.DataFrame(next_day)
        prediction_for_next_day = classifier.predict(next_day_df)
        print(next_day_df)
        print(prediction_for_next_day)
        accuracy = accuracy_score(y_test, y_pred)
        #print(f"Model Accuracy: {accuracy * 100:.2f}%")
        return prediction_for_next_day
    else:
        return "Require more data for prediction."

def display_result(prediction):
    if prediction != False:
        if prediction[0] == 1:
            return "You will complete your goal"
        
        else:
            return "You wont complete your goal"
    else:
        return "Not enough data"

# Run the app
if __name__ == '__main__':
    app.run(debug=False,host="0.0.0.0", port=int(os.environ.get('PORT',3000)))
