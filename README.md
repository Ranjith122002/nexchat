# NexChat — Real-Time Chat App

WhatsApp-style real-time chat built with Python + Flask + Socket.IO

---

## Requirements
- Python 3.9 or higher (3.13 supported)
- pip

---

## Setup (VS Code)

### 1. Open Folder
File > Open Folder > select the `chatapp` folder

### 2. Create Virtual Environment
```
python -m venv venv
```

### 3. Activate Virtual Environment
Windows:
```
venv\Scripts\activate
```
Mac/Linux:
```
source venv/bin/activate
```

### 4. Install Dependencies
```
pip install -r requirements.txt
```

### 5. Run
```
python app.py
```

### 6. Open Browser
http://127.0.0.1:5000

---

## How to Chat with Others

### Same computer (testing):
1. Open http://127.0.0.1:5000 in a normal window — register Account A
2. Open http://127.0.0.1:5000 in an Incognito window — register Account B
3. Both join the same group → messages appear in real time!

### From another device on your WiFi:
- Share your IP address URL: http://192.168.x.x:5000
- The other person registers and joins the same group

---

## Features
- Real-time messaging (WebSockets)
- Group chats (create unlimited rooms)
- Direct Messages (private 1-on-1)
- Typing indicators
- Message history (stored in SQLite)
- User profiles
- Mobile responsive
- WhatsApp-style dark UI

---

## Project Structure
```
chatapp/
  app.py               - Flask app, routes, socket events, DB models
  requirements.txt     - Python packages
  nexchat.db           - SQLite database (auto-created)
  templates/
    base.html          - Base layout
    login.html         - Login page
    register.html      - Register page
    chat.html          - Main chat UI
    profile.html       - Profile page
  static/
    css/style.css      - All styles (WhatsApp dark theme)
    js/chat.js         - Socket.IO client logic
```

---

## Libraries Used
| Library          | Purpose                    |
|------------------|----------------------------|
| Flask            | Web framework              |
| Flask-SocketIO   | Real-time WebSockets       |
| Flask-SQLAlchemy | Database ORM (SQLite)      |
| Flask-Login      | User sessions              |
| Flask-Bcrypt     | Password hashing           |
| simple-websocket | Async WebSocket support    |
