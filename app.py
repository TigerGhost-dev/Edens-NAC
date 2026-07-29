from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify
)

import sqlite3
import threading
from datetime import datetime

from db import init_db
from nac.controller import (
    controller,
    authenticate_user,
    logout_user
)

app = Flask(__name__)
app.secret_key = "eden_secret"

init_db()

###############################################################
# Start NAC Controller
###############################################################

threading.Thread(
    target=controller,
    daemon=True
).start()

###############################################################
# Database
###############################################################

def db():
    return sqlite3.connect("database.db")

###############################################################
# Logging
###############################################################

def log_event(username, action):

    conn = db()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO logs
        (
            username,
            action,
            time
        )
        VALUES
        (
            ?,?,?
        )
        """,
        (
            username,
            action,
            str(datetime.now())
        )
    )

    conn.commit()
    conn.close()

###############################################################
# HOME
###############################################################

@app.route("/")
def home():

    return redirect("/portal")

###############################################################
# USER PORTAL
###############################################################

@app.route("/portal")
def portal():

    return render_template("user/portal.html")

###############################################################
# REGISTER
###############################################################

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":

        return render_template("user/register.html")

    username = request.form["username"]
    password = request.form["password"]

    conn = db()
    c = conn.cursor()

    c.execute(
        "SELECT id FROM users WHERE username=?",
        (username,)
    )

    if c.fetchone():

        conn.close()

        return jsonify({

            "success": False,
            "message": "Username already exists"

        })

    c.execute(
        """
        INSERT INTO users
        (
            username,
            password,
            role,
            status
        )
        VALUES
        (
            ?,?,
            'user',
            'pending'
        )
        """,
        (
            username,
            password
        )
    )

    conn.commit()
    conn.close()

    log_event(username, "REGISTERED")

    return jsonify({

        "success": True,
        "message": "Registration submitted"

    })

###############################################################
# LOGIN
###############################################################

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = db()
    c = conn.cursor()

    c.execute(
        """
        SELECT
            id,
            password,
            status
        FROM users
        WHERE username=?
        """,
        (username,)
    )

    user = c.fetchone()

    if not user:

        conn.close()

        return jsonify({

            "success": False,
            "message": "User not found"

        })

    if user[1] != password:

        conn.close()

        return jsonify({

            "success": False,
            "message": "Wrong password"

        })

    if user[2] != "approved":

        conn.close()

        return jsonify({

            "success": False,
            "message": "Waiting for administrator approval"

        })

    ####################################################
    # Find client's MAC using its IP
    ####################################################

    ip = request.remote_addr

    c.execute(
        """
        SELECT mac
        FROM devices
        WHERE ip=?
        """,
        (ip,)
    )

    device = c.fetchone()

    if not device:

        conn.close()

        return jsonify({

            "success": False,
            "message": "Device not registered"

        })

    mac = device[0]

    ####################################################
    # Update device
    ####################################################

    c.execute(
        """
        UPDATE devices
        SET
            username=?,
            authenticated=1
        WHERE mac=?
        """,
        (
            username,
            mac
        )
    )

    conn.commit()
    conn.close()

    ####################################################
    # Allow Internet
    ####################################################

    authenticate_user(username)

    session["username"] = username

    log_event(username, "LOGIN")

    return jsonify({

        "success": True,
        "message": "Access Granted"

    })


 ###############################################################
# LOGOUT
###############################################################

@app.route("/logout")
def logout():

    username = session.get("username")

    if username:

        logout_user(username)

        log_event(username, "LOGOUT")

    session.clear()

    return redirect("/portal")

###############################################################
# ADMIN LOGIN
###############################################################

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "GET":

        return render_template("admin/login.html")

    username = request.form["username"]
    password = request.form["password"]

    conn = db()
    c = conn.cursor()

    c.execute(
        """
        SELECT role
        FROM users
        WHERE
            username=?
        AND
            password=?
        """,
        (
            username,
            password
        )
    )

    admin = c.fetchone()

    conn.close()

    if not admin:

        return "Invalid Login"

    if admin[0] != "admin":

        return "Not an administrator"

    session["admin"] = username

    return redirect("/dashboard")

###############################################################
# DASHBOARD
###############################################################

@app.route("/dashboard")
def dashboard():

    if "admin" not in session:

        return redirect("/admin")

    conn = db()
    c = conn.cursor()

    c.execute(
        """
        SELECT *
        FROM logs
        ORDER BY id DESC
        """
    )

    logs = c.fetchall()

    c.execute(
        """
        SELECT *
        FROM devices
        ORDER BY id DESC
        """
    )

    devices = c.fetchall()

    c.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE status='pending'
        """
    )

    pending = c.fetchone()[0]

    conn.close()

    return render_template(

        "admin/dashboard.html",

        logs=logs,

        devices=devices,

        pending_count=pending

    )

###############################################################
# USERS
###############################################################

@app.route("/users")
def users():

    if "admin" not in session:

        return redirect("/admin")

    conn = db()
    c = conn.cursor()

    c.execute(
        """
        SELECT
            u.id,
            u.username,
            u.role,
            d.mac,
            d.ip,
            d.os,
            u.status
        FROM users u

        LEFT JOIN devices d

        ON u.username=d.username

        ORDER BY u.id
        """
    )

    users = c.fetchall()

    conn.close()

    return render_template(

        "admin/users.html",

        users=users

    )

###############################################################
# APPROVE USER
###############################################################

@app.route("/approve_user/<int:id>")
def approve_user(id):

    if "admin" not in session:

        return redirect("/admin")

    conn = db()
    c = conn.cursor()

    c.execute(

        """
        UPDATE users
        SET status='approved'
        WHERE id=?
        """,

        (id,)

    )

    conn.commit()
    conn.close()

    return redirect("/users")

###############################################################
# DELETE USER
###############################################################

@app.route("/delete_user/<int:id>")
def delete_user(id):

    if "admin" not in session:

        return redirect("/admin")

    conn = db()
    c = conn.cursor()

    c.execute(

        "DELETE FROM users WHERE id=?",

        (id,)

    )

    conn.commit()
    conn.close()

    return redirect("/users")

###############################################################
# HEALTH CHECK
###############################################################

@app.route("/health")
def health():

    return jsonify({

        "status": "running",
        "portal": "online"

    })

###############################################################
# RUN
###############################################################

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False,

        use_reloader=False

    )   