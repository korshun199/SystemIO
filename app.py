from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'base.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# АВТОМАТИЧЕСКАЯ ПРОВЕРКА И ДОБАВЛЕНИЕ КОЛОНОК
def init_db():
    if not os.path.exists(DATABASE):
        print("База base.db не найдена!")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Список колонок, которые нам жизненно необходимы
    required_columns = {
        'is_online': 'INTEGER DEFAULT 0',
        'last_seen': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'deleted': 'INTEGER DEFAULT 0'
    }
    
    try:
        # Проверяем, что есть в таблице users
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        for col, col_type in required_columns.items():
            if col not in existing_columns:
                print(f"Добавляю отсутствующую колонку: {col}")
                conn.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
        
        conn.commit()
    except Exception as e:
        print(f"Ошибка при настройке колонок: {e}")
    finally:
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# --- API ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                       (data['username'], data['password'])).fetchone()
    conn.close()
    if user:
        return jsonify({"status": "ok", "user": dict(user)})
    return jsonify({"status": "error", "message": "Ошибка авторизации"})

@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    # Теперь колонки точно существуют благодаря init_db
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

# --- АДМИНКА ---

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

@app.route('/api/admin/user/add', methods=['POST'])
def admin_add_user():
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO users (username, password, deleted) VALUES (?, ?, ?)',
                (data['username'], data['password'], data.get('deleted', 0)))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

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
    init_db() # Самолечение базы при старте
    app.run(debug=True, host='0.0.0.0', port=5000)