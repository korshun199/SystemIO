import sqlite3

DATABASE = 'base.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Проверка ПИН-кода (локально или через базу)
def check_user_pin(user_id, pin):
    conn = get_db_connection()
    user = conn.execute('SELECT pin_code FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user and user['pin_code'] == pin:
        return True
    return False

# ПОЛНЫЙ ДОСТУП ДЛЯ АДМИНА (Твое управление)
def admin_get_all_users():
    """Возвращает список всех пользователей для админки"""
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, full_name, role, is_active FROM users').fetchall()
    conn.close()
    return users

def admin_update_user_status(user_id, status):
    """Блокировка/Разблокировка пользователя (status: 1 или 0)"""
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_active = ? WHERE id = ?', (status, user_id))
    conn.commit()
    conn.close()

def admin_delete_user(user_id):
    """Полное удаление пользователя из системы"""
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

# Добавление нового пользователя (только через тебя)
def add_new_user(username, password, full_name, role='user'):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO users (username, password, full_name, role, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (username, password, full_name, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()