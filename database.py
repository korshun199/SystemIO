import sqlite3
import os

DB_PATH = 'base.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Удаляем старые таблицы, если они вдруг мешают, 
    # чтобы создать всё с чистого листа с правильными именами
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'employee'
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,  -- Убедились, что имя именно такое
            to_id INTEGER, 
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (from_id) REFERENCES users (id),
            FOREIGN KEY (to_id) REFERENCES users (id)
        );
    ''')
    try:
        conn.execute("INSERT INTO users (username, password, full_name, role) VALUES (?,?,?,?)",
                     ('Oleg_Boss', 'pass123', 'Олег Сергеевич', 'admin'))
        conn.commit()
    except: pass
    conn.close()

def save_msg(f_id, t_id, txt):
    conn = get_db_connection()
    # Здесь тоже используем правильные имена колонок
    conn.execute("INSERT INTO messages (from_id, to_id, content) VALUES (?,?,?)", (f_id, t_id, txt))
    conn.commit()
    conn.close()

def get_msgs(t_id=None):
    conn = get_db_connection()
    if t_id:
        res = conn.execute("""SELECT m.*, u.username FROM messages m JOIN users u ON m.from_id = u.id 
                           WHERE to_id = ? OR (m.from_id = ? AND to_id IS NOT NULL) ORDER BY timestamp ASC""", (t_id, t_id)).fetchall()
    else:
        res = conn.execute("""SELECT m.*, u.username FROM messages m JOIN users u ON m.from_id = u.id 
                           WHERE to_id IS NULL ORDER BY timestamp ASC""").fetchall()
    conn.close()
    return [dict(r) for r in res]

# В файле database.py должна быть именно эта функция:
def get_users():
    conn = get_db_connection()
    # Берем данные так, чтобы они подходили для JSON
    res = conn.execute("SELECT id, username, full_name, role FROM users").fetchall()
    conn.close()
    return [dict(r) for r in res]

# Инициализируем при импорте
init_db()