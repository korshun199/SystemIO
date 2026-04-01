from flask import Flask, request, jsonify, send_from_directory
import os
import database  # Импортируем наш файл с SQL-логикой

app = Flask(__name__)

# Путь к папке с фронтендом
CLIENT_DIR = os.path.join(os.getcwd(), 'client')

# 1. Главная страница (отдаем твой index.html)
@app.route('/')
def index():
    return send_from_directory(CLIENT_DIR, 'index.html')

# 2. Отдача статики (CSS, JS из папки client)
@app.route('/<path:path>')
def send_static(path):
    return send_from_directory(CLIENT_DIR, path)

# 3. API: Получить всех пользователей
@app.route('/api/users', methods=['GET'])
def get_users():
    users = database.get_all_users()
    return jsonify(users)

# 4. API: Добавить нового пользователя
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    success = database.add_user(
        username=data.get('username'),
        password_hash=data.get('password'), # В будущем добавим хэширование
        full_name=data.get('fullname'),
        role=data.get('role', 'employee')
    )
    
    if success:
        return jsonify({"status": "ok", "message": "User created"}), 201
    else:
        return jsonify({"status": "error", "message": "User already exists"}), 400

if __name__ == '__main__':

    print("🚀 SystemIO Server запущен на http://127.0.0.1:5000")
    app.run(debug=True, port=5000)