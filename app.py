from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexchat-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexchat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db       = SQLAlchemy(app)
bcrypt   = Bcrypt(app)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ─────────────── Models ───────────────────────────────────

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio      = db.Column(db.String(300), default='')
    created  = db.Column(db.DateTime, default=datetime.utcnow)
    sent_messages     = db.relationship('Message', foreign_keys='Message.sender_id',   backref='sender',    lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy=True)

class Room(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created    = db.Column(db.DateTime, default=datetime.utcnow)
    messages   = db.relationship('Message', backref='room', lazy=True)

class Message(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    content      = db.Column(db.Text, nullable=False)
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id      = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

# ─────────────── Auth Routes ──────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('chat') if current_user.is_authenticated else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'].strip()).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('chat'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
        else:
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed)
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─────────────── Chat Routes ──────────────────────────────

@app.route('/chat')
@login_required
def chat():
    rooms = Room.query.order_by(Room.created.desc()).all()
    users = User.query.filter(User.id != current_user.id).order_by(User.username).all()
    return render_template('chat.html',
                           rooms=rooms,
                           users=users,
                           current_user=current_user)

@app.route('/create_room', methods=['POST'])
@login_required
def create_room():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Room name cannot be empty.', 'error')
    elif Room.query.filter_by(name=name).first():
        flash(f'Room "{name}" already exists.', 'error')
    else:
        room = Room(name=name, created_by=current_user.id)
        db.session.add(room)
        db.session.commit()
    return redirect(url_for('chat'))

@app.route('/history/<room_type>/<int:rid>')
@login_required
def history(room_type, rid):
    msgs = []
    if room_type == 'room':
        msgs = Message.query.filter_by(room_id=rid).order_by(Message.timestamp).limit(100).all()
    elif room_type == 'dm':
        msgs = Message.query.filter(
            Message.room_id == None,
            db.or_(
                db.and_(Message.sender_id == current_user.id, Message.recipient_id == rid),
                db.and_(Message.sender_id == rid,             Message.recipient_id == current_user.id)
            )
        ).order_by(Message.timestamp).limit(100).all()
    result = [{
        'username':  m.sender.username,
        'message':   m.content,
        'timestamp': m.timestamp.strftime('%H:%M'),
        'own':       m.sender_id == current_user.id
    } for m in msgs]
    return jsonify(result)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio', '').strip()
        db.session.commit()
        flash('Profile updated!', 'success')
    return render_template('profile.html')

# ─────────────── Socket Events ────────────────────────────

@socketio.on('join')
def on_join(data):
    join_room(data['room'])

@socketio.on('leave')
def on_leave(data):
    leave_room(data['room'])

@socketio.on('message')
def on_message(data):
    content   = data.get('content', '').strip()
    room_key  = data.get('room', '')
    if not content or not room_key:
        return

    msg = Message(content=content, sender_id=current_user.id)

    if room_key.startswith('room_'):
        room_id  = int(room_key.split('_')[1])
        msg.room_id = room_id
    elif room_key.startswith('dm_'):
        other_id = int(room_key.split('_')[1])
        msg.recipient_id = other_id

    db.session.add(msg)
    db.session.commit()

    emit('message', {
        'username':  current_user.username,
        'message':   content,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'room':      room_key,
        'uid':       current_user.id
    }, to=room_key)

@socketio.on('typing')
def on_typing(data):
    emit('typing', {'username': current_user.username}, to=data['room'], include_self=False)

@socketio.on('stop_typing')
def on_stop_typing(data):
    emit('stop_typing', {'username': current_user.username}, to=data['room'], include_self=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
