import sqlite3
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'base.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  full_name TEXT, 
                  role TEXT, 
                  last_seen INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  sender_id INTEGER, 
                  receiver_id INTEGER, 
                  content TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    return dict(user) if user else None

def update_last_seen(user_id):
    conn = get_db_connection()
    conn.execute('UPDATE users SET last_seen = ? WHERE id = ?', (int(time.time()), user_id))
    conn.commit()
    conn.close()

def get_users_with_status():
    conn = get_db_connection()
    now = int(time.time())
    users = conn.execute('SELECT id, username, last_seen, full_name, role FROM users').fetchall()
    conn.close()
    result = []
    for u in users:
        d = dict(u)
        ls = d.get('last_seen') or 0
        d['is_online'] = (now - ls) < 60 if ls > 0 else False
        result.append(d)
    return result

def get_main_messages(my_id):
    conn = get_db_connection()
    # Логика: сообщения ВСЕМ (0) ИЛИ сообщения МНЕ ИЛИ сообщения ОТ МЕНЯ
    query = '''SELECT m.*, u.username as sender_name FROM messages m 
               JOIN users u ON m.sender_id = u.id
               WHERE m.receiver_id = 0 
                  OR m.receiver_id = ? 
                  OR m.sender_id = ?
               ORDER BY m.timestamp ASC'''
    msgs = conn.execute(query, (my_id, my_id)).fetchall()
    conn.close()
    return [dict(m) for m in msgs]

def get_private_chat(my_id, with_id):
    conn = get_db_connection()
    query = '''SELECT m.*, u.username as sender_name FROM messages m 
               JOIN users u ON m.sender_id = u.id
               WHERE (m.sender_id = ? AND m.receiver_id = ?) 
               OR (m.sender_id = ? AND m.receiver_id = ?) 
               ORDER BY m.timestamp ASC'''
    msgs = conn.execute(query, (my_id, with_id, with_id, my_id)).fetchall()
    conn.close()
    return [dict(m) for m in msgs]

def add_message(sender_id, receiver_id, content):
    conn = get_db_connection()
    conn.execute('INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)', 
                 (sender_id, receiver_id, content))
    conn.commit() # ВОТ ОН, ГЛАВНЫЙ ФИКС!
    conn.close()

init_db()