-- Очистка старых данных
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS users;

-- СТРУКТУРА
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'employee',
    status TEXT DEFAULT 'offline',
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES users (id)
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER NOT NULL,
    to_user_id INTEGER DEFAULT NULL,
    room_id INTEGER DEFAULT NULL,
    content TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (from_user_id) REFERENCES users (id),
    FOREIGN KEY (to_user_id) REFERENCES users (id),
    FOREIGN KEY (room_id) REFERENCES rooms (id)
);

-- НАПОЛНЕНИЕ (10 ПОЛЬЗОВАТЕЛЕЙ)
INSERT INTO users (username, password_hash, full_name, role) VALUES 
('Oleg_Boss', 'pass123', 'Олег Сергеевич', 'admin'),
('Anna_Mgr', 'pass123', 'Анна Волкова', 'manager'),
('Ivan_Dev', 'pass123', 'Иван Петров', 'employee'),
('Dmitry_Dev', 'pass123', 'Дмитрий Соколов', 'employee'),
('Elena_HR', 'pass123', 'Елена Кузнецова', 'manager'),
('Alex_Sales', 'pass123', 'Алексей Морозов', 'employee'),
('Maria_Design', 'pass123', 'Мария Лисицына', 'employee'),
('Sergey_Tech', 'pass123', 'Сергей Попов', 'employee'),
('Olga_Support', 'pass123', 'Ольга Новикова', 'employee'),
('Pavel_QA', 'pass123', 'Павел Васильев', 'employee');

-- КОМНАТЫ
INSERT INTO rooms (name, description, created_by) VALUES 
('Общий', 'Чат для всех', 1),
('Разработка', 'Только код', 3);

-- СООБЩЕНИЯ (10 ШТУК)
INSERT INTO messages (from_user_id, room_id, content) VALUES 
(1, 1, 'Всем привет! SystemIO официально запущена.'),
(2, 1, 'Ура! Анна на связи.'),
(3, 2, 'Дмитрий, ты проверил последний пулл-реквест?');

-- Личные сообщения (тет-а-тет)
INSERT INTO messages (from_user_id, to_user_id, content) VALUES 
(1, 2, 'Анна, зайди ко мне через 5 минут.'),
(5, 1, 'Олег, списки новых сотрудников готовы.'),
(7, 3, 'Иван, скинь исходники иконок.'),
(4, 3, 'Да, Иван, сейчас смотрю код.'),
(9, 1, 'В офисе закончился кофе! Кто заказывает?'),
(10, 4, 'Дмитрий, баг в админке подтвержден.'),
(1, 10, 'Павел, проверь нагрузку на базу данных.');