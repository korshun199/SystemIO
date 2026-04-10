from flask import Flask, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit, join_room
import database

app = Flask(__name__)
app.config['SECRET_KEY'] = 'boss_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Словарь для хранения активных пользователей: {user_id: sid}
online_users = {}

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path): return send_from_directory('.', path)

@app.route('/api/users')
def get_users(): return jsonify(database.get_users())

@app.route('/api/history')
def get_history():
    t_id = request.args.get('to_id')
    for_user = request.args.get('for_user')
    
    # Если просят общую историю
    if t_id == 'all' or not t_id:
        if for_user and for_user != 'undefined' and for_user != 'null':
            return jsonify(database.get_msgs_combined(int(for_user)))
        return jsonify(database.get_msgs(None))
    
    # Если просят личку с конкретным ID
    return jsonify(database.get_msgs(int(t_id)))

def handle_connect():
    print("Кто-то подключился")

@socketio.on('go_online')
def go_online(data):
    user_id = data['user_id']
    online_users[user_id] = request.sid
    join_room(f"user_{user_id}") # Личная комната для приватных сообщений
    emit('status_update', list(online_users.keys()), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    user_to_remove = None
    for uid, sid in online_users.items():
        if sid == request.sid:
            user_to_remove = uid
            break
    if user_to_remove:
        del online_users[user_to_remove]
        emit('status_update', list(online_users.keys()), broadcast=True)

@socketio.on('send_msg')
def handle_msg(data):
    f_id = data['from_id']
    t_id = data.get('to_id')
    content = data['content']
    
    database.save_msg(f_id, t_id, content)
    
    msg_payload = {
        'from_id': f_id,
        'username': data['username'],
        'content': content,
        'to_id': t_id
    }

    if t_id: # Приватное сообщение
        emit('new_msg', msg_payload, room=f"user_{t_id}")
        emit('new_msg', msg_payload, room=f"user_{f_id}")
    else: # Общий чат
        emit('new_msg', msg_payload, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)