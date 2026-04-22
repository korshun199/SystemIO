import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
import database as db
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here' # Обязательно смени потом на свою!
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10) # Тот самый таймаут "как в банке"
socketio = SocketIO(app)

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        pin = request.form.get('pin') # Получаем ПИН из формы

        user = db.get_db_connection().execute(
            'SELECT * FROM users WHERE username = ? AND password = ?', 
            (username, password)
        ).fetchone()

        if user:
            # 1. Проверка на твой "бан"
            if not user['is_active']:
                return "Ваш аккаунт заблокирован администратором", 403
            
            # 2. Проверка ПИН-кода (если он установлен в базе)
            if user['pin_code'] and user['pin_code'] != pin:
                return "Неверный ПИН-код", 401

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
            
        return "Неверный логин или пароль", 401
    return render_template('login.html')

# --- АДМИНСКАЯ ЧАСТЬ (Твой пульт) ---

@app.route('/admin/users')
def admin_panel():
    if session.get('role') != 'admin':
        return "Доступ только для Олега Сергеевича!", 403
    
    users = db.admin_get_all_users()
    return jsonify([dict(u) for u in users]) # Пока отдаем просто списком

@app.route('/admin/block/<int:user_id>', methods=['POST'])
def block_user(user_id):
    if session.get('role') == 'admin':
        db.admin_update_user_status(user_id, 0)
        return jsonify({"status": "blocked"})
    return "Forbidden", 403

# Socket.io события
@socketio.on('message')
def handle_message(data):
    # Тут твоя логика чата
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)