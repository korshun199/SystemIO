import sqlite3
import random
from datetime import datetime, timedelta

def seed_messages(count=100):
    conn = sqlite3.connect('base.db')
    cursor = conn.cursor()

    # 1. Получаем список всех живых ID из базы
    cursor.execute('SELECT id, username FROM users')
    users = cursor.fetchall()
    
    if not users:
        print("Ошибка: В таблице users никого нет. Сначала добавь людей!")
        return

    user_ids = [u[0] for u in users]
    
    # Фразы для создания "атмосферы"
    phrases = [
        "Всем привет!", "Кто на связи?", "Босс, всё готово.", "Где отчет по геометрии?",
        "Система работает стабильно.", "Кто-нибудь видел Олега?", "Маша, ты тут?",
        "Тестирую соединение...", "Опять рекурсия...", "Linux — сила!",
        "Скоро будем во втором классе.", "Не забывайте про дедлайны.",
        "Я зашел с телефона.", "Как дела в Термуксе?", "База обновлена."
    ]

    print(f"Начинаю генерацию {count} сообщений...")

    # Очистим старые сообщения, чтобы не путаться
    cursor.execute('DELETE FROM messages')

    now = datetime.now()

    for i in range(count):
        sender = random.choice(user_ids)
        # 30% шанса, что сообщение в общий канал (0), иначе — случайному юзеру
        is_private = random.random() > 0.3
        receiver = random.choice(user_ids) if is_private else 0
        
        # Чтобы не писать самому себе в личку
        if is_private and receiver == sender:
            receiver = 0
            
        content = random.choice(phrases) + f" (msg_{i})"
        # Раскидаем сообщения по времени за последние 24 часа
        time_offset = timedelta(minutes=random.randint(0, 1440))
        msg_time = (now - time_offset).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            INSERT INTO messages (sender_id, receiver_id, content, timestamp) 
            VALUES (?, ?, ?, ?)
        ''', (sender, receiver, content, msg_time))

    conn.commit()
    conn.close()
    print(f"Готово! База наполнена. Твой чат теперь выглядит как настоящий хаос. 🫦")

if __name__ == "__main__":
    seed_messages(100)