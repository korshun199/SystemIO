from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import configparser

# Инициализация конфига
config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)

# Глобальные переменные из config.ini
DATABASE = config.get('DATABASE', 'PATH')
HOST = config.get('SERVER', 'HOST')
PORT = config.getint('SERVER', 'PORT')
DEBUG = config.getboolean('SERVER', 'DEBUG')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        print(f"Критическая ошибка: База {DATABASE} не найдена!")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Список необходимых колонок (точка памяти сохранена)
    required_columns = {
        'is_online': 'INTEGER DEFAULT 0',
        'last_seen': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'deleted': 'INTEGER DEFAULT 0'
    }
    
    try:
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        for col, col_type in required_columns.items():
            if col not in existing_columns:
                print(f"Конфигурация: Добавляю колонку {col} в {DATABASE}")
                conn.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
        
        conn.commit()
    except Exception as e:
        print(f"Ошибка конфигурирования БД: {e}")
    finally:
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# --- API (ВСЕ ПУТИ И ЛОГИКА СОХРАНЕНЫ) ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                       (data['username'], data['password'])).fetchone()
    conn.close()
    if user:
        return jsonify({"status": "ok", "user": dict(user)})
    return jsonify({"status": "error", "message": "Доступ запрещен"})

@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, is_online, deleted FROM users').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_online = 1, last_seen = CURRENT_TIMESTAMP WHERE id = ?', (data['user_id'],))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/chat/main/<int:user_id>')
def get_main_chat(user_id):
    conn = get_db_connection()
    msgs = conn.execute('''
        SELECT m.*, u.username as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE m.receiver_id = 0 ORDER BY timestamp ASC
    ''').fetchall()
    conn.close()
    return jsonify([dict(m) for m in msgs])

@app.route('/api/chat/private/<int:uid>/<int:tid>')
def get_private_chat(uid, tid):
    conn = get_db_connection()
    msgs = conn.execute('''
        SELECT m.*, u.username as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE (sender_id = ? AND receiver_id = ?) 
           OR (sender_id = ? AND receiver_id = ?) 
        ORDER BY timestamp ASC
    ''', (uid, tid, tid, uid)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in msgs])

@app.route('/api/chat/send', methods=['POST'])
def send_msg():
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)',
                (data['sender_id'], data['receiver_id'], data['content']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- API АДМИНКИ (ПОДДЕРЖКА ВЕТКИ admin-dev_conf) ---

@app.route('/api/admin/history/<int:user_id>')
def admin_user_history(user_id):
    conn = get_db_connection()
    msgs = conn.execute('''
        SELECT m.*, u1.username as sender_name, u2.username as receiver_name 
        FROM messages m
        JOIN users u1 ON m.sender_id = u1.id
        LEFT JOIN users u2 ON m.receiver_id = u2.id
        WHERE m.sender_id = ? OR m.receiver_id = ?
        ORDER BY m.timestamp ASC
    ''', (user_id, user_id)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in msgs])

@app.route('/api/admin/user/update', methods=['POST'])
def admin_update_user():
    data = request.json
    conn = get_db_connection()
    conn.execute('UPDATE users SET username = ?, deleted = ? WHERE id = ?', 
                (data['username'], data['deleted'], data['id']))
    if data.get('password') and data['password'].strip():
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (data['password'], data['id']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(debug=DEBUG, host=HOST, port=PORT)