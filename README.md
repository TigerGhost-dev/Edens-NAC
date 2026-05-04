# 🛡️ Eden’s NAC (Network Access Control System)

## 📌 Project Overview

Eden’s NAC is a lightweight, customizable Network Access Control (NAC) system designed for small networks, academic environments, and home use.

The system provides authentication, device visibility, access control, and monitoring within a Local Area Network (LAN) using open-source technologies.

---

## 🎯 Objectives

* Authenticate users before granting network access
* Register and track connected devices
* Provide administrative control over users and hosts
* Monitor network activity and access logs
* Simulate real-world NAC functionality for learning and research

---

## 🚀 Features

### 🔐 Authentication

* Login system for users and administrators
* Session-based access control

### 💻 User & Device Management

* View all registered users and hosts
* Search users by MAC address
* Approve or delete users
* Track:

  * IP Address
  * MAC Address
  * Operating System
  * Access status

### 📊 Dashboard

* NAC-style admin dashboard
* Overview of:

  * Total logs
  * Active devices
  * Users

### 📜 Logging

* Tracks:

  * Login attempts
  * System actions
* Timestamped activity logs

### 🌐 Network Monitoring (Prototype)

* Device detection (LAN scanning)
* Foundation for:

  * Open port scanning
  * Traffic visibility
  * Device profiling

---

## 🏗️ System Architecture

Client Device → NAC Server → Authentication → Access Control → Dashboard

---

## 🛠️ Technologies Used

* Backend: Python (Flask)
* Frontend: HTML, CSS
* Database: SQLite
* Networking: Scapy
* System Tools: iptables (planned for enforcement)

---

## ⚙️ Installation & Setup

### 1. Clone the repository

git clone https://github.com/TigerGhost-dev/Edens-NAC.git
cd Edens-NAC

### 2. Install dependencies

pip install -r requirements.txt

### 3. Run the application

python app.py

### 4. Open in browser

http://localhost:5000

---

## 🔑 Default Credentials

Username: admin
Password: 1234

---

## 📸 Screenshots (Add Later)

* Dashboard
* User Management
* Logs

---

## ⚠️ Limitations

* Prototype-level NAC (not enterprise-grade)
* Limited real-time enforcement
* Requires root privileges for advanced network scanning

---

## 🔮 Future Improvements

* Full captive portal implementation
* Real-time device blocking (firewall integration)
* Open port scanning per device
* Guest access system
* Role-based access control
* Live network traffic visualization
* Integration with authentication servers (RADIUS / LDAP)

---

## 📚 Academic Relevance

This project demonstrates:

* Network security principles
* Access control mechanisms (AAA model)
* Zero Trust concepts
* Practical NAC implementation

---

## 👨‍💻 Author

Eden Nguthi
School of Science, Engineering & Health

---

## 📄 License

This project is for educational purposes.
