import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)
socketio = SocketIO(app, cors_allowed_origins="*",logger=True, engineio_logger=True)

gps_data = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/gps_data', methods=['GET'])
def get_gps_data():
    return jsonify(gps_data)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('gps_data')
def handle_gps_data(json_data):
    global gps_data
    gps_data = json_data
    print('Received GPS data:', gps_data)  # Log received GPS data
    emit('update_map', gps_data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000,cors_allowed_origins='*',async_mode='eventlet')
