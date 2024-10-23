from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app)

available_users = []
user_rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('find_partner')
def handle_find_partner():
    if available_users:
        partner_sid = available_users.pop(0)
        room_name = request.sid + partner_sid
        join_room(room_name)
        user_rooms[request.sid] = {'room': room_name, 'partner': partner_sid}
        user_rooms[partner_sid] = {'room': room_name, 'partner': request.sid}
        join_room(room_name, sid=partner_sid)
        emit('partner_found', room=request.sid)
        emit('partner_found', room=partner_sid)
    else:
        available_users.append(request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in available_users:
        available_users.remove(request.sid)
    room = user_rooms.get(request.sid)
    if room:
        partner_sid = room['partner']
        emit('partner_left', room=partner_sid)
        leave_room(room['room'])
        del user_rooms[partner_sid]
        del user_rooms[request.sid]

@socketio.on('signal')
def handle_signal(data):
    room = user_rooms.get(request.sid)
    if room:
        partner_sid = room['partner']
        emit('signal', data, room=partner_sid)

@socketio.on('text_message')
def handle_text_message(msg):
    room = user_rooms.get(request.sid)
    if room:
        partner_sid = room['partner']
        emit('text_message', msg, room=partner_sid)

if __name__ == '__main__':
    socketio.run(app, debug=True)
