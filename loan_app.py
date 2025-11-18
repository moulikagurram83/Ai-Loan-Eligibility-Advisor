from flask import Flask, request, render_template, jsonify, redirect, session, url_for
from flask_bcrypt import Bcrypt
import sqlite3
import pickle
import numpy as np
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "loan_app_secret_key"

bcrypt = Bcrypt(app)
model = pickle.load(open("model.pkl", "rb"))

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect("loan_app.db", timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            data_json TEXT,
            result TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users(username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed)
            )
            conn.commit()

            user = conn.execute(
                "SELECT * FROM users WHERE email=?", (email,)
            ).fetchone()

        except sqlite3.IntegrityError:
            return render_template("register.html", error="⚠ Email already exists")

        finally:
            conn.close()

        session["logged_in"] = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect(url_for("profile"))

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user["password"], password):
            session["logged_in"] = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("profile"))

        return render_template("login.html", error="Invalid Email or Password")

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- PROFILE ----------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    try:
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        
        if not user:
            conn.close()
            return redirect("/login")
        
        # Fetch prediction history
        predictions = conn.execute(
            "SELECT * FROM predictions WHERE user_id=? ORDER BY timestamp DESC LIMIT 10",
            (session["user_id"],)
        ).fetchall()
        
        conn.close()

        # Calculate statistics
        total_predictions = len(predictions) if predictions else 0
        approved_count = sum(1 for p in predictions if p["result"] == "Approved") if predictions else 0
        rejected_count = total_predictions - approved_count

        user_data = {
            "name": user["username"] if user["username"] else "Unknown",
            "email": user["email"] if user["email"] else "Unknown",
            "member_since": "N/A"
        }
        
        stats = {
            "total": total_predictions,
            "approved": approved_count,
            "rejected": rejected_count
        }

        return render_template("profile.html", user=user_data, predictions=predictions, stats=stats)
    
    except Exception as e:
        print(f"Profile Error: {str(e)}")
        return redirect("/login")

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

        if not user:
            return render_template("forgot_password.html", error="Email not found!")

        # store email temporarily
        session['reset_email'] = email
        return redirect('/reset-password')

    return render_template("forgot_password.html")

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        return redirect('/forgot-password')

    if request.method == 'POST':
        new_password = request.form['new_password']
        email = session['reset_email']

        # HASH THE PASSWORD BEFORE SAVING
        hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')

        conn = get_db()
        conn.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hashed, email)
        )
        conn.commit()

        session.pop('reset_email', None)

        return redirect('/login')

    return render_template("reset_password.html")

# ---------------- ABOUT ----------------
@app.route("/about")
def about():
    return render_template("about.html")


# ---------------- PREDICT ----------------
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if not session.get("logged_in"):
        return redirect("/login")

    if request.method == "POST":

        form = request.form.to_dict()

        ApplicantIncomeLog = np.log(float(form["ApplicantIncome"]))
        LoanAmountLog = np.log(float(form["LoanAmount"]))
        LoanTermLog = np.log(float(form["Loan_Amount_Term"]))
        totalIncomeLog = np.log(float(form["ApplicantIncome"]) + float(form["CoapplicantIncome"]))

        credit = float(form["credit"])
        male = 1 if form["gender"] == "Male" else 0
        married_yes = 1 if form["married"] == "Yes" else 0
        dependents = form["dependents"]

        dependents_1 = 1 if dependents == "1" else 0
        dependents_2 = 1 if dependents == "2" else 0
        dependents_3 = 1 if dependents == "3" else 0

        not_graduate = 1 if form["education"] == "Not Graduate" else 0
        employed_yes = 1 if form["employed"] == "Yes" else 0
        semiurban = 1 if form["area"] == "Semiurban" else 0
        urban = 1 if form["area"] == "Urban" else 0

        prediction = model.predict([[
            credit,
            ApplicantIncomeLog,
            LoanAmountLog,
            LoanTermLog,
            totalIncomeLog,
            male,
            married_yes,
            dependents_1,
            dependents_2,
            dependents_3,
            not_graduate,
            employed_yes,
            semiurban,
            urban
        ]])

        result = "Approved" if prediction[0] == "Y" else "Rejected"

        conn = get_db()
        conn.execute(
            "INSERT INTO predictions(user_id, data_json, result, timestamp) VALUES (?, ?, ?, ?)",
            (
                session["user_id"],
                json.dumps(form),
                result,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        conn.commit()
        conn.close()

        return render_template("prediction.html", prediction_text=f"Loan Status: {result}")

    return render_template("prediction.html")


# ---------------- CHATBOT ----------------
@app.route("/chatbot")
def chatbot_page():
    if not session.get("logged_in"):
        return redirect("/login")
    return render_template("chatbot.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    step = data.get("step", 0)

    questions = [
        "What is your gender? (Male/Female)",
        "Are you married? (Yes/No)",
        "How many dependents do you have? (0/1/2/3+)",
        "What is your education level? (Graduate/Not Graduate)",
        "Are you self-employed? (Yes/No)",
        "What is your monthly applicant income?",
        "What is your monthly co-applicant income?",
        "What is the loan amount you want?",
        "What is your loan term?",
        "Credit history? (0 or 1)",
        "What is the property area? (Urban/Semiurban/Rural)"
    ]

    if step == 0:
        return jsonify({"reply": "Let's begin!\n" + questions[0], "next_step": 1})

    if step < len(questions):
        return jsonify({"reply": questions[step], "next_step": step + 1})

    return jsonify({"reply": "All questions completed!", "done": True})


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
