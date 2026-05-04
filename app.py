from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

from db import init_db

# ⚠️ temporarily disable scanner + firewall (we'll re-enable later safely)
# from nac.scanner import scan_network
# from nac.firewall import block_device, allow_device

app = Flask(__name__)
app.secret_key = "eden_secret"

init_db()

# ---------- LOGGING ----------
def log_event(user, action):
    try:
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO logs (username, action, time) VALUES (?, ?, ?)",
                  (user, action, str(datetime.now())))
        conn.commit()
        conn.close()
    except Exception as e:
        print("LOG ERROR:", e)

# ---------- HOME ----------
@app.route('/')
def home():
    return redirect('/login')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')

            print("LOGIN:", username, password)

            conn = sqlite3.connect("database.db")
            c = conn.cursor()

            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()

            print("DB RESULT:", user)

            if user:
                session['user'] = username
                log_event(username, "LOGIN SUCCESS")
                return redirect('/dashboard')
            else:
                log_event(username, "LOGIN FAILED")
                return "Login Failed"

        except Exception as e:
            print("LOGIN ERROR:", e)
            return "Login Error"

    return render_template("login.html")

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    try:
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM logs")
        logs = c.fetchall()

        # 🔥 SAFE: no scanning yet
        devices = []

        return render_template("dashboard.html", logs=logs, devices=devices)

    except Exception as e:
        print("DASHBOARD ERROR:", e)
        return f"Dashboard Error: {e}"

# ---------- BLOCK ----------
@app.route('/block/<mac>')
def block(mac):
    return "Block feature coming soon"

# ---------- ALLOW ----------
@app.route('/allow/<mac>')
def allow(mac):
    return "Allow feature coming soon"

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


# ---------- MANAGE USERS ----------
@app.route('/users')
def users():
    if 'user' not in session:
        return redirect('/login')

    search = request.args.get('mac')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if search:
        c.execute("SELECT * FROM users WHERE mac LIKE ?", ('%' + search + '%',))
    else:
        c.execute("SELECT * FROM users")

    users = c.fetchall()
    conn.close()

    return render_template("users.html", users=users)

# ---------- DELETE USER ----------
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect('/users')

# ---------- APPROVE USER ----------
@app.route('/approve_user/<int:user_id>')
def approve_user(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE users SET status='approved' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect('/users')