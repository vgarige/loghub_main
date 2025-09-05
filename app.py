from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change this in production


# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            department TEXT
        )
    """)

    # Attendance table
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------- Helper Functions ----------
def validate_password(password):
    """Check if password meets criteria"""
    regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$"
    return re.match(regex, password)


# ---------- Routes ----------
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not validate_password(password):
            flash("Password too weak! Must have 8+ chars, 1 uppercase, 1 number, 1 special char.")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for("signup"))

        hashed_pw = generate_password_hash(password)

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            flash("Account created successfully! Please login.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("signup"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"])


@app.route("/mark_attendance")
def mark_attendance():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    today = datetime.today().strftime("%Y-%m-%d")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Check if already marked for today
    c.execute("SELECT * FROM attendance WHERE username=? AND date=?", (username, today))
    record = c.fetchone()

    if record:
        conn.close()
        # Already marked, show confirmation page
        return render_template("mark_attendance.html", username=username, date=today)
    else:
        # Mark attendance
        c.execute("INSERT INTO attendance (username, date, status) VALUES (?, ?, ?)",
                  (username, today, "Present"))
        conn.commit()
        conn.close()

        return render_template("mark_attendance.html", username=username, date=today)

@app.route("/attendance_history")
def attendance_history():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT date, status FROM attendance WHERE username=? ORDER BY date DESC", (username,))
    records = c.fetchall()
    conn.close()

    return render_template("attendance_history.html", records=records)


@app.route("/teachers")
def teachers():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, username, full_name, department FROM users")
    teachers_list = c.fetchall()
    conn.close()

    return render_template("teachers.html", teachers=teachers_list)


@app.route("/add_teacher", methods=["GET", "POST"])
def add_teacher():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        full_name = request.form["full_name"]
        username = request.form["username"]
        password = request.form["password"]
        department = request.form["department"]

        hashed_pw = generate_password_hash(password)

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, full_name, department) VALUES (?, ?, ?, ?)",
                      (username, hashed_pw, full_name, department))
            conn.commit()
            conn.close()
            flash("Teacher added successfully!")
            return redirect(url_for("teachers"))
        except sqlite3.IntegrityError:
            flash("Username already exists!")
            return redirect(url_for("add_teacher"))

    return render_template("add_teacher.html")




@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
