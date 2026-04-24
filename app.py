from flask import Flask, render_template, jsonify, request
import database

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    user = database.verify_user(d['username'], d['password'])
    if user:
        return jsonify({"status": "ok", "user": user})
    return jsonify({"status": "error", "message": "Неверный логин или пароль"}), 401

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    uid = request.json.get('user_id')
    if uid: database.update_last_seen(int(uid))
    return jsonify({"status": "ok"})

@app.route('/api/users')
def get_users():
    return jsonify(database.get_users_with_status())

@app.route('/api/chat/main/<int:my_id>')
def chat_main(my_id):
    return jsonify(database.get_main_messages(my_id))

@app.route('/api/chat/private/<int:my_id>/<int:with_id>')
def chat_private(my_id, with_id):
    return jsonify(database.get_private_chat(my_id, with_id))

@app.route('/api/chat/send', methods=['POST'])
def send_msg():
    d = request.json
    database.add_message(int(d['sender_id']), int(d['receiver_id']), d['content'])
    return jsonify({"status": "sent"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)