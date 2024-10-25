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
        # Jumelage avec un utilisateur déjà en attente
        partner_sid = available_users.pop()
        room_name = request.sid + partner_sid
        print(f"Jumelage : {request.sid} avec {partner_sid} dans la room {room_name}")
        join_room(room_name)

        # Sauvegarder les informations de la room
        user_rooms[request.sid] = {'room': room_name, 'partner': partner_sid}
        user_rooms[partner_sid] = {'room': room_name, 'partner': request.sid}

        # Faire rejoindre les deux utilisateurs à la room
        socketio.emit('partner_found', to=request.sid)
        socketio.emit('partner_found', to=partner_sid)
    else:
        # Ajouter l'utilisateur à la liste d'attente
        available_users.append(request.sid)
        print(f"Ajout de {request.sid} dans la file d'attente.")

@socketio.on('connect')
def handle_connect():
    print(f"Client {request.sid} connected")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client {request.sid} disconnected")
    if request.sid in available_users:
        available_users.remove(request.sid)
    if request.sid in user_rooms:
        partner_sid = user_rooms[request.sid]['partner']
        if partner_sid in user_rooms:
            socketio.emit('partner_left', to=partner_sid)
            del user_rooms[partner_sid]
        del user_rooms[request.sid]



@socketio.on('signal')
def handle_signal(data):
    room = user_rooms.get(request.sid)
    if room:
        partner_sid = room['partner']
        emit('signal', data, to=partner_sid)

@socketio.on('text_message')
def handle_text_message(msg):
    room = user_rooms.get(request.sid)
    if room:
        partner_sid = room['partner']
        emit('text_message', msg, room=partner_sid)

if __name__ == '__main__':
    socketio.run(app, debug=True)
