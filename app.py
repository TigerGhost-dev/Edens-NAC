from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from datetime import datetime
from db import init_db

app = Flask(__name__)
app.secret_key = "eden_secret"

init_db()

# ---------------- LOGGING ----------------
def log_event(user, action):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (username, action, time) VALUES (?, ?, ?)",
              (user, action, str(datetime.now())))
    conn.commit()
    conn.close()


# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/portal')


# =====================================================
# 🔵 USER SIDE (CAPTIVE PORTAL)
# =====================================================

# ---------- PORTAL ----------
@app.route('/portal')
def portal():
    return render_template("user/portal.html")


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        ip = request.remote_addr

        if len(password) < 8:
            return "Password must be at least 8 characters"

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if c.fetchone():
            conn.close()
            return "Username already exists"

        c.execute("""
        INSERT INTO users (username, password, mac, ip, os, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            username,
            password,
            role,
            ip,
            "Unknown",
            "pending"
        ))

        conn.commit()
        conn.close()

        log_event(username, "REGISTERED")

        return redirect(f"/waiting/{username}")

    return render_template("user/register.html")


# ---------- WAITING ----------
@app.route('/waiting/<username>')
def waiting(username):
    return render_template("user/waiting.html", username=username)


# ---------- LOGIN (PORTAL AUTH) ----------
@app.route('/portal_login', methods=['POST'])
def portal_login():

    username = request.form.get('username')
    password = request.form.get('password')
    ip = request.remote_addr

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, password))

    user = c.fetchone()

    if user:
        if user[6] == "approved":

            # Bind IP
            c.execute("UPDATE users SET ip=? WHERE id=?", (ip, user[0]))
            conn.commit()

            log_event(username, f"PORTAL LOGIN SUCCESS {ip}")

            conn.close()

            return "ACCESS_GRANTED"

        else:
            conn.close()
            return "PENDING"

    conn.close()
    return "INVALID"


# ---------- CHECK APPROVAL ----------
@app.route('/check/<username>')
def check(username):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT status FROM users WHERE username=?", (username,))
    user = c.fetchone()

    conn.close()

    if user and user[0] == "approved":
        return jsonify({"approved": True})

    return jsonify({"approved": False})


# =====================================================
# 🔴 ADMIN SIDE
# =====================================================

# ---------- ADMIN LOGIN ----------
@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("""
        SELECT * FROM users
        WHERE username=? AND password=? AND status='approved'
        """, (username, password))

        admin = c.fetchone()

        conn.close()

        if admin:
            session['admin'] = username
            return redirect('/dashboard')

        return "Invalid admin credentials"

    return render_template("admin/login.html")


# ---------- ADMIN AUTH ----------
def admin_required():
    if 'admin' not in session:
        return False
    return True


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():

    if not admin_required():
        return redirect('/admin')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM logs")
    logs = c.fetchall()

    c.execute("SELECT COUNT(*) FROM users WHERE status='pending'")
    pending = c.fetchone()[0]

    conn.close()

    return render_template("admin/dashboard.html",
                           logs=logs,
                           pending=pending)


# ---------- USERS ----------
@app.route('/users')
def users():

    if not admin_required():
        return redirect('/admin')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    users = c.fetchall()

    conn.close()

    return render_template("admin/users.html", users=users)


# ---------- APPROVE ----------
@app.route('/approve/<int:id>')
def approve(id):

    if not admin_required():
        return redirect('/admin')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE users SET status='approved' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/users')


# ---------- DELETE ----------
@app.route('/delete/<int:id>')
def delete(id):

    if not admin_required():
        return redirect('/admin')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/users')


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin')


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)