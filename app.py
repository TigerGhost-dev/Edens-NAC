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

###############################################################
# LOGIN
###############################################################

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"].strip()
    password = request.form["password"].strip()

    conn = db()
    c = conn.cursor()

    ####################################################
    # Verify User
    ####################################################

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

    if user is None:

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
    # Find Device By Client IP
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

    if device is None:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Device not registered with the NAC"
        })

    mac = device[0]

    ####################################################
    # Associate Device With User
    ####################################################

    c.execute(
        """
        UPDATE devices
        SET
            username=?,
            authenticated=1,
            last_seen=CURRENT_TIMESTAMP
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
    # Authorize Firewall
    ####################################################

    authenticate_user(username)

    ####################################################
    # Create Session
    ####################################################

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

    username = request.form["username"].strip()
    password = request.form["password"].strip()

    conn = db()
    c = conn.cursor()

    c.execute(
        """
        SELECT id, username
        FROM admins
        WHERE username=?
        AND password=?
        """,
        (
            username,
            password
        )
    )

    admin_user = c.fetchone()

    conn.close()

    if admin_user is None:
        return "Invalid administrator login", 401

    session["admin"] = admin_user[1]

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
    pending_count=pending,
    active_page="dashboard"
)



###############################################################
# LIVE DASHBOARD API
###############################################################

@app.route("/api/dashboard")
def dashboard_api():

    if "admin" not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    conn = db()
    c = conn.cursor()

    ###########################################################
    # Total devices
    ###########################################################

    c.execute(
        """
        SELECT COUNT(*)
        FROM devices
        """
    )

    device_count = c.fetchone()[0]

    ###########################################################
    # Active authenticated devices
    ###########################################################

    c.execute(
        """
        SELECT
            username,
            ip,
            mac
        FROM devices
        WHERE authenticated=1
        ORDER BY last_seen DESC
        """
    )

    active_devices = []

    for row in c.fetchall():

        active_devices.append({
            "username": row[0],
            "ip": row[1],
            "mac": row[2]
        })

    ###########################################################
    # Successful login count
    ###########################################################

    c.execute(
        """
        SELECT COUNT(*)
        FROM logs
        WHERE action='LOGIN'
        """
    )

    successful_logins = c.fetchone()[0]

    ###########################################################
    # Recent successful logins
    ###########################################################

    c.execute(
        """
        SELECT
            username,
            action,
            time
        FROM logs
        WHERE action='LOGIN'
        ORDER BY id DESC
        LIMIT 10
        """
    )

    recent_logins = []

    for row in c.fetchall():

        recent_logins.append({
            "username": row[0],
            "action": row[1],
            "time": row[2]
        })

    ###########################################################
    # Pending registrations
    ###########################################################

    c.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE status='pending'
        """
    )

    pending_count = c.fetchone()[0]

    conn.close()

    ###########################################################
    # Return dashboard data
    ###########################################################

    return jsonify({

        "success": True,

        "device_count": device_count,

        "active_users": len(active_devices),

        "successful_logins": successful_logins,

        "pending_count": pending_count,

        "active_devices": active_devices,

        "recent_logins": recent_logins

    })


###############################################################
# ADMIN LOGOUT
###############################################################

@app.route("/admin_logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/portal")

###############################################################
# USERS
###############################################################

@app.route("/users")
def users():

    if "admin" not in session:
        return redirect("/admin")

    search_mac = request.args.get("mac", "").strip().lower()

    conn = db()
    c = conn.cursor()

    if search_mac:

        c.execute(
            """
            SELECT
                u.id,
                u.username,
                u.role,
                d.mac,
                d.ip,
                d.authenticated,
                u.status
            FROM users u
            LEFT JOIN devices d
                ON u.username = d.username
            WHERE LOWER(d.mac) LIKE ?
            ORDER BY u.id
            """,
            (
                f"%{search_mac}%",
            )
        )

    else:

        c.execute(
            """
            SELECT
                u.id,
                u.username,
                u.role,
                d.mac,
                d.ip,
                d.authenticated,
                u.status
            FROM users u
            LEFT JOIN devices d
                ON u.username = d.username
            ORDER BY u.id
            """
        )

    users = c.fetchall()

    conn.close()

    return render_template(
        "admin/users.html",
        users=users,
        search_mac=search_mac,
        active_page="users"
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