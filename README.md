# 💬 NexChat — Real-Time Chat Application

A WhatsApp-style real-time chat application built with Python + Flask + Socket.IO

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![SocketIO](https://img.shields.io/badge/Socket.IO-4.6-black)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🌍 Live Demo
👉 [https://nexchat-vm6z.onrender.com](https://nexchat-vm6z.onrender.com) — Register and start chatting instantly!
---

## ✨ Features

- ⚡ Real-time messaging using WebSockets
- 👥 Group chats — create unlimited rooms
- 💬 Direct messages — private 1-on-1 chats
- ✍️ Typing indicators
- 📜 Message history
- 🔒 Secure login with encrypted passwords
- 📱 Mobile responsive (WhatsApp-style UI)
- 🔐 Admin panel with login history & IP tracking
- 🗑️ Admin can delete users and messages

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + Flask |
| Real-time | Flask-SocketIO + Socket.IO |
| Database | SQLite (local) / PostgreSQL (production) |
| Auth | Flask-Login + Flask-Bcrypt |
| Frontend | HTML + CSS + JavaScript |
| Hosting | Render (free) |

---

## 🚀 Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/Ranjith122002/nexchat.git
cd nexchat
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```

### 5. Open browser
```
http://127.0.0.1:5000
```

---

## 🔐 Admin Panel

Access the admin panel at:
```
http://127.0.0.1:5000/admin
```

Admin features:
- View all registered users
- View all messages (group + DM)
- View login history with IP addresses
- Delete users and messages

---

## 📁 Project Structure
```
nexchat/
├── app.py                  ← Flask app, routes, socket events, DB models
├── requirements.txt        ← Python dependencies
├── Procfile               ← Render deployment config
├── templates/
│   ├── base.html          ← Base layout
│   ├── login.html         ← Login page
│   ├── register.html      ← Register page
│   ├── chat.html          ← Main chat UI
│   ├── profile.html       ← Profile page
│   ├── admin_login.html   ← Admin login
│   └── admin_dashboard.html ← Admin panel
└── static/
    ├── css/style.css      ← WhatsApp dark theme
    └── js/chat.js         ← Socket.IO client
```

---

## 🌐 Deploy on Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect GitHub repo
4. Set environment variables:
   - `SECRET_KEY` = your secret key
   - `FLASK_ENV` = production
   - `ADMIN_PASSWORD` = your admin password
5. Click Deploy!

---

## 📦 Dependencies
```
flask
flask-socketio
flask-sqlalchemy
flask-login
flask-bcrypt
python-socketio
simple-websocket
psycopg2-binary
```

---

## 👨‍💻 Developer

**Ranjith R**
- GitHub: [@Ranjith122002](https://github.com/Ranjith122002)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
