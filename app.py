import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexchat-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///nexchat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db       = SQLAlchemy(app)
bcrypt   = Bcrypt(app)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')
login_manager = LoginManager(app)
login_manager.login_view = 'login'

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Ranjith@2002')

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio      = db.Column(db.String(300), default='')
    created  = db.Column(db.DateTime, default=datetime.utcnow)
    sent_messages     = db.relationship('Message', foreign_keys='Message.sender_id',    backref='sender',    lazy=True)
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

class LoginHistory(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username   = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    status     = db.Column(db.String(10), nullable=False)

@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))

@app.route('/')
def index():
    return redirect(url_for('chat') if current_user.is_authenticated else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        username   = request.form['username'].strip()
        password   = request.form['password']
        ip_address = request.remote_addr or 'Unknown'
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            log = LoginHistory(user_id=user.id, username=username, ip_address=ip_address, status='success')
            db.session.add(log)
            db.session.commit()
            return redirect(url_for('chat'))
        else:
            if user:
                log = LoginHistory(user_id=user.id, username=username, ip_address=ip_address, status='failed')
                db.session.add(log)
                db.session.commit()
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
        else:
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, password=hashed)
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

@app.route('/chat')
@login_required
def chat():
    rooms = Room.query.order_by(Room.created.desc()).all()
    users = User.query.filter(User.id != current_user.id).order_by(User.username).all()
    return render_template('chat.html', rooms=rooms, users=users, current_user=current_user)

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

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Wrong admin password.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    users          = User.query.order_by(User.created.desc()).all()
    messages       = Message.query.order_by(Message.timestamp.desc()).limit(100).all()
    rooms          = Room.query.all()
    login_logs     = LoginHistory.query.order_by(LoginHistory.timestamp.desc()).limit(100).all()
    total_users    = User.query.count()
    total_messages = Message.query.count()
    total_rooms    = Room.query.count()
    total_logins   = LoginHistory.query.filter_by(status='success').count()
    return render_template('admin_dashboard.html',
                           users=users, messages=messages, rooms=rooms,
                           login_logs=login_logs,
                           total_users=total_users,
                           total_messages=total_messages,
                           total_rooms=total_rooms,
                           total_logins=total_logins)

@app.route('/admin/delete_user/<int:uid>', methods=['POST'])
def admin_delete_user(uid):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    user = db.session.get(User, uid)
    if user:
        Message.query.filter_by(sender_id=uid).delete()
        Message.query.filter_by(recipient_id=uid).delete()
        LoginHistory.query.filter_by(user_id=uid).delete()
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_message/<int:mid>', methods=['POST'])
def admin_delete_message(mid):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    msg = db.session.get(Message, mid)
    if msg:
        db.session.delete(msg)
        db.session.commit()
        flash('Message deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@socketio.on('join')
def on_join(data):
    join_room(data['room'])

@socketio.on('leave')
def on_leave(data):
    leave_room(data['room'])

@socketio.on('message')
def on_message(data):
    content  = data.get('content', '').strip()
    room_key = data.get('room', '')
    if not content or not room_key:
        return
    msg = Message(content=content, sender_id=current_user.id)
    if room_key.startswith('room_'):
        msg.room_id = int(room_key.split('_')[1])
    elif room_key.startswith('dm_'):
        msg.recipient_id = int(room_key.split('_')[1])
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

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)