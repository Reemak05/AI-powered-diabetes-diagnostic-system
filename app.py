from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import pickle
import numpy as np
from datetime import datetime
import json
import hashlib 
import os
from datetime import date
from werkzeug.utils import secure_filename
import uuid


app = Flask(__name__)
app.secret_key = 'secret_key'  
app.config['UPLOAD_FOLDER'] = 'static/img'
# Connect to your MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # your MySQL password here
    database="diabetes1"
)
cursor = db.cursor(buffered=True)

#by default page
@app.route('/')
def index():
    return redirect(url_for('login'))  # Just redirect to login page (index.html)

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT user_id, Username, Password, role FROM user WHERE Email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]


            if user[3] == 'admin':
                return redirect(url_for('manage_user'))
            else:
                return redirect(url_for('homepage'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))

    return render_template('index.html')  

#Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        raw_password = request.form['password']
        email = request.form['email']

        hashed_password = generate_password_hash(raw_password)

        try:
            cursor.execute("INSERT INTO user (Username, Password, Email) VALUES (%s, %s, %s)",
                           (username, hashed_password, email))
            db.commit()
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

#Manager user
@app.route('/manageuser', methods=['GET'])
def manage_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('login'))

    cursor.execute("SELECT user_id, Username, Email FROM user WHERE role = 'user'")
    users = cursor.fetchall()

    return render_template('manageuser.html', users=users)

#Admin delete user account
@app.route('/delete_user/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('login'))

    try:
        cursor.execute("DELETE FROM health_logs WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
        db.commit()
    except mysql.connector.Error as err:
        flash(f"Error deleting user: {err}", "danger")

    return redirect(url_for('manage_user'))

#Home page
@app.route('/homepage')
def homepage():
    if 'user_id' in session:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM settings ORDER BY Update_id DESC LIMIT 1")
        settings = cursor.fetchone()
        return render_template('homepage.html', settings=settings)
    else:
        flash("Please login first", "warning")
        return redirect(url_for('login'))

#
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#About Us page
@app.route('/aboutus')
def about_us():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings ORDER BY Update_id DESC LIMIT 1")
    settings = cursor.fetchone()
    return render_template('aboutus.html', settings=settings)

#Machine learning part using flask and model.py
# Load your trained ML model
scaler, model = pickle.load(open("model.pkl", "rb"))
def predict_diabetes_type(insulin, diabetes_pedigree, age, bmi, glucose, pregnancy):
    if age < 25 and insulin < 50 and bmi < 20:
        return "Type 1 Diabetes"
    if age >= 25 and bmi >= 25 and glucose >= 126:
        return "Type 2 Diabetes"
    if pregnancy > 0 and glucose >= 100 and glucose < 126:
        return "Gestational Diabetes"
    if glucose >= 100 and glucose < 126:
        return "Prediabetes"
    return "no diabetes"

#chat page
@app.route('/chat')
def chat():
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))
    return render_template('chat.html')  # Your chat UI

#result of chat (predicition)
@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    try:
         # Safely extract features from frontend
        pregnancies = float(data.get("pregnancies", 0))
        glucose = float(data.get("glucose", 0))
        blood_pressure = float(data.get("blood_pressure", 0))
        insulin = float(data.get("insulin", 0))
        bmi = float(data.get("bmi", 0))
        diabetes_pedigree = float(data.get("diabetes_pedigree", 0))
        age = float(data.get("age", 0))
        

        # Prepare input for model
        features = np.array([
            pregnancies, glucose, blood_pressure, insulin, bmi, diabetes_pedigree, age
        ]).reshape(1, -1)
        # Apply the same scaler used during training
        scaled_features = scaler.transform(features)

# Predict using scaled features
        prediction = model.predict(scaled_features)[0]
      
        diabetes_type = predict_diabetes_type(insulin, diabetes_pedigree, age, bmi, glucose, pregnancies)


        # Store in health_logs table
        cursor.execute("""
            INSERT INTO health_logs 
            (date, Glucose, age, BMI, Blood_pressure, Diabetes_perdigree, Pregnancies, insulin, prediction, type, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.now().date(),
            data["glucose"],
            data["age"],
            data["bmi"],
            data["blood_pressure"],
            data["diabetes_pedigree"],
            data["pregnancies"],
            data["insulin"],
            int(prediction),
            diabetes_type,
            session["user_id"]
        ))
        db.commit()

        return jsonify({"result": int(prediction)})
    except Exception as e:
        print("Error in prediction:", e)
        return jsonify({"error": str(e)}), 400
    
#health logs page
@app.route('/health_logs')
def health_logs():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor()
    cursor.execute("""
        SELECT date, age, blood_pressure, bmi, glucose, insulin, Pregnancies, type
        FROM health_logs
        WHERE user_id = %s
        ORDER BY date DESC
    """, (user_id,))
    logs = cursor.fetchall()
    cursor.close()

    # Prepare data for charts from the logs
    dates = [log[0].strftime('%Y-%m-%d') if hasattr(log[0], 'strftime') else log[0] for log in logs]  # Format dates if datetime
    blood_pressures = [log[2] for log in logs]
    glucoses = [log[4] for log in logs]
    bmis = [log[3] for log in logs]
    insulins = [log[5] for log in logs]
    pregnancies = [log[6] for log in logs]

    return render_template('health_logs.html', logs=logs,
                           dates=json.dumps(dates),
                           blood_pressures=json.dumps(blood_pressures),
                           glucoses=json.dumps(glucoses),
                           bmis=json.dumps(bmis),
                           insulins=json.dumps(insulins),
                           pregnancies=json.dumps(pregnancies))

#Symptoms page
@app.route('/symptoms')
def symptoms():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings ORDER BY Update_id DESC LIMIT 1")
    settings = cursor.fetchone()
    return render_template('symptoms.html', settings=settings)

#Risk page
@app.route('/risk')
def risk():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings ORDER BY Update_id DESC LIMIT 1")
    settings = cursor.fetchone()
    return render_template('risk.html', settings=settings)

#prevention Tips page
@app.route('/preventiontips')
def preventiontips():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings ORDER BY Update_id DESC LIMIT 1")
    settings = cursor.fetchone()
    return render_template('preventiontips.html', settings=settings)

#Analystics page
@app.route('/analytics')
def analytics():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    # 1. Total unique users who have predictions
    cursor.execute("SELECT COUNT(*) AS total_users FROM user WHERE role = 'user'")
    total_users = cursor.fetchone()['total_users']
    

    # 2. Latest prediction per user
    cursor.execute("""
        SELECT hl.user_id, hl.prediction
        FROM health_logs hl
        INNER JOIN (
            SELECT user_id, MAX(date) AS max_date
            FROM health_logs
            GROUP BY user_id
        ) latest ON hl.user_id = latest.user_id AND hl.date = latest.max_date
    """)
    user_predictions = cursor.fetchall()

    diabetic_count = sum(1 for u in user_predictions if u['prediction'] == 1)
    non_diabetic_count = sum(1 for u in user_predictions if u['prediction'] == 0)

    # 3. Number of predictions over last 30 days (group by date)
    cursor.execute("""
        SELECT date, COUNT(*) as count
        FROM health_logs
        WHERE date >= CURDATE() - INTERVAL 30 DAY
        GROUP BY date
        ORDER BY date
    """)
    predictions_over_time = cursor.fetchall()
    dates = [str(row['date']) for row in predictions_over_time]
    prediction_counts = [row['count'] for row in predictions_over_time]

    # 4. Average health metrics over last 30 days
    cursor.execute("""
        SELECT date,
               AVG(glucose) as avg_glucose,
               AVG(bmi) as avg_bmi,
               AVG(blood_pressure) as avg_bp
        FROM health_logs
        WHERE date >= CURDATE() - INTERVAL 30 DAY
        GROUP BY date
        ORDER BY date
    """)
    metrics = cursor.fetchall()
    metric_dates = [str(row['date']) for row in metrics]
    avg_glucose = [round(row['avg_glucose'], 2) if row['avg_glucose'] is not None else 0 for row in metrics]
    avg_bmi = [round(row['avg_bmi'], 2) if row['avg_bmi'] is not None else 0 for row in metrics]
    avg_bp = [round(row['avg_bp'], 2) if row['avg_bp'] is not None else 0 for row in metrics]

    cursor.close()

    return render_template('analytics.html',
                           total_users=total_users,
                           diabetic_count=diabetic_count,
                           non_diabetic_count=non_diabetic_count,
                           dates=dates,
                           prediction_counts=prediction_counts,
                           metric_dates=metric_dates,
                           avg_glucose=avg_glucose,
                           avg_bmi=avg_bmi,
                           avg_bp=avg_bp)


#profile page
@app.route("/profile")
def profile():
    user_id = session["user_id"]
    cursor = db.cursor()
    cursor.execute("SELECT username, email, phone, gender FROM user WHERE user_id = %s", (user_id,))
    data = cursor.fetchone()
    cursor.close()
    
    user = {
        "username": data[0],
        "email": data[1],
        "phone": data[2],
        "gender": data[3]
    }
    return render_template("profile.html", user=user)

#update profile page
@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    username = request.form["username"]
    email = request.form["email"]
    phone = request.form.get("phone")
    gender = request.form.get("gender")

    cursor = db.cursor()
    cursor.execute("""
        UPDATE user
        SET username=%s, email=%s, phone=%s, gender=%s
        WHERE user_id=%s
    """, (username, email, phone, gender, user_id))
    db.commit()
    cursor.close()

    flash("Profile updated successfully!", "success")
    return redirect("/profile")

#admin profile
@app.route('/admin/profile')
def admin_profile():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session["user_id"]
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT username, email, role FROM user WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if not user or user['role'] != 'admin':
        return "Access denied", 403

    return render_template("admin_profile.html", user=user)


#change password
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user_id = session['user_id']

        cursor = db.cursor()
        cursor.execute("SELECT password FROM user WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()

        if result is None:
            flash("User not found.", "danger")
            return redirect(url_for("login"))

        db_password_hash = result[0]

        if not check_password_hash(db_password_hash, current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("change_password"))

        new_password_hash = generate_password_hash(new_password)

        cursor = db.cursor()
        cursor.execute("UPDATE user SET password = %s WHERE user_id = %s", (new_password_hash, user_id))
        db.commit()
        cursor.close()

        flash("Password changed successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("change_password.html")

#clear health logs
@app.route('/clear_health_logs', methods=['POST'])
def clear_health_logs():
    if 'user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor()
    cursor.execute("DELETE FROM health_logs WHERE user_id = %s", (user_id,))
    db.commit()
    flash("All health logs deleted successfully.", "success")
    return redirect(url_for('profile'))

#delete my account
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor()
    
    # Delete health logs first (to satisfy FK constraint)
    cursor.execute("DELETE FROM health_logs WHERE user_id = %s", (user_id,))
    # Delete user account
    cursor.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
    db.commit()
    
    session.clear()
    flash("Your account and health logs have been deleted.", "success")
    return redirect(url_for('login'))

#manage user "view"
@app.route('/admin/user_logs/<int:user_id>')
def admin_user_logs(user_id):
    cursor = db.cursor()

    # Get user info
    cursor.execute("SELECT username, email FROM user WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    # Get health logs
    cursor.execute("SELECT date, age, blood_pressure, bmi, glucose, insulin, Pregnancies, type FROM health_logs WHERE user_id = %s", (user_id,))

    logs = cursor.fetchall()
    
    cursor.close()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('manage_user'))

    return render_template("admin_user_logs.html", user=user, logs=logs)


#Setting page
@app.route('/admin/settings')
def admin_settings():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings ORDER BY Update_id DESC LIMIT 1")
    settings = cursor.fetchone()
    return render_template('admin_settings.html', settings=settings)

# Handle section update
@app.route('/admin/settings/update/<section>', methods=['POST'])
def update_section(section):
    valid_sections = ['home', 'risk', 'prevention', 'symptoms', 'about']
    if section not in valid_sections:
        return "Invalid section", 400

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings ORDER BY Update_id DESC LIMIT 1")
    current = cursor.fetchone()

    # Get form data
    title = request.form.get(f"{section}_title")
    text = request.form.get(f"{section}_text")
    image_file = request.files.get(f"{section}_image")

    if not title or not text:
       flash("Title and Text are required.", "error")
       return redirect(url_for('admin_settings'))

# Use new image if uploaded, otherwise keep old one
 

    if image_file and image_file.filename != '':
      ext = os.path.splitext(image_file.filename)[1]
      filename = f"{uuid.uuid4().hex}{ext}"
      image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      image_file.save(image_path)
    else:
      filename = current[f"{section}_image"]



    # Prepare full data
    update_data = {
        's_date': date.today()
    }

    for sec in valid_sections:
        update_data[f'{sec}_title'] = title if sec == section else current[f'{sec}_title']
        update_data[f'{sec}_text'] = text if sec == section else current[f'{sec}_text']
        update_data[f'{sec}_image'] = filename if sec == section else current[f'{sec}_image']

    sql = """
        INSERT INTO settings (
            s_date,
            home_title, home_text, home_image,
            risk_title, risk_text, risk_image,
            prevention_title, prevention_text, prevention_image,
            symptoms_title, symptoms_text, symptoms_image,
            about_title, about_text, about_image
        ) VALUES (
            %(s_date)s,
            %(home_title)s, %(home_text)s, %(home_image)s,
            %(risk_title)s, %(risk_text)s, %(risk_image)s,
            %(prevention_title)s, %(prevention_text)s, %(prevention_image)s,
            %(symptoms_title)s, %(symptoms_text)s, %(symptoms_image)s,
            %(about_title)s, %(about_text)s, %(about_image)s
        )
    """

    cursor.execute(sql, update_data)
    db.commit()

    flash(f"{section.capitalize()} page updated successfully!", "success")
    return redirect(url_for('admin_settings'))

if __name__ == '__main__':
    app.run(debug=True)



