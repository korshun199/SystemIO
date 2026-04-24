import sqlite3

conn = sqlite3.connect('base.db')
cursor = conn.cursor()

# Удаляем старую таблицу сообщений, чтобы создать новую с правильными колонками
cursor.execute('DROP TABLE IF EXISTS messages')

# Создаем заново с нужными колонками: sender_id и receiver_id
cursor.execute('''
    CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# На всякий случай проверим таблицу пользователей
try:
    cursor.execute('ALTER TABLE users ADD COLUMN last_seen INTEGER')
except:
    pass # Если колонка уже есть — всё ок

conn.commit()
conn.close()
print("База данных приведена в порядок! Таблица messages пересоздана.")