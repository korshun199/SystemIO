from flask import Flask, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit
import database
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- МАРШРУТЫ ДЛЯ СТАТИКИ ---

@app.route('/')
def index():
    # Отдаем index.html из корня
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Эта функция ищет ЛЮБОЙ файл (style.css, script.js) в корневой папке
    return send_from_directory('.', filename)

# --- API ---

@app.route('/api/users')
def get_users():
    return jsonify(database.get_users())

@app.route('/api/history')
def get_history():
    t_id = request.args.get('to_id')
    t_id = int(t_id) if t_id and t_id != 'all' else None
    return jsonify(database.get_msgs(t_id))

# --- SOCKETS ---

@socketio.on('send_msg')
def handle_msg(data):
    database.save_msg(data['from_id'], data.get('to_id'), data['content'])
    emit('new_msg', data, broadcast=True)

if __name__ == '__main__':
    # Убедись, что база создана перед запуском
    database.init_db()
    socketio.run(app, debug=True, port=5000)