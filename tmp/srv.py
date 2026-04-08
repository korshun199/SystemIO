from flask import Flask, jsonify, request

app = Flask(__name__)

# Состояние машинки
current_command = {
    "action": "stop",
    "speed": 90
}

# ESP32 будет стучаться сюда
@app.route('/api/car/get_command', methods=['GET'])
def get_command():
    return jsonify(current_command)

# Android-пульт будет слать команды сюда
@app.route('/api/phone/send_command', methods=['POST'])
def update_command():
    global current_command
    data = request.get_json() # Получаем JSON от пульта
    
    current_command["action"] = data.get("action", "stop")
    current_command["speed"] = data.get("speed", 90)
    
    return jsonify({
        "status": "success", 
        "message": "Команда принята", 
        "current_state": current_command
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)