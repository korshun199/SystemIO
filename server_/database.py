import sqlite3
import os

# Определяем пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'base.db')


def get_db_connection():
    """Устанавливает соединение с SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn



def get_all_users():
    """Получает всех пользователей для админки."""
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, full_name, role, status FROM users').fetchall()
    conn.close()
    return [dict(user) for user in users]

def add_user(username, password_hash, full_name, role='employee'):
    """Добавляет нового юзера."""
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)',
            (username, password_hash, full_name, role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()