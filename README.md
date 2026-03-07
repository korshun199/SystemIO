# SystemIO

SystemIO — персональный мессенджер с веб-интерфейсом.

## Архитектура

Client (HTML / JS)
        │
        │ HTTP API
        ▼
Flask Backend
        │
        ▼
SQLite Database

## Возможности

- регистрация пользователей
- личные диалоги
- обмен сообщениями
- история сообщений
- realtime обновление (polling)

## Запуск программы V2

pip install flask
python backend/app.py