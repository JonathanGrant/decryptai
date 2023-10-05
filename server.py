import os
from flask import Flask, request, jsonify, session, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
from flasgger import Swagger
import random
import string
from datetime import timedelta


app = Flask(__name__, static_folder='ui/build')
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = 'mysecret'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SAMESITE'] = "None"
app.config['SESSION_COOKIE_SECURE'] = True
socketio = SocketIO(app, cors_allowed_origins="*")
swagger = Swagger(app)

nouns      = open('nouns.txt'     ).read().split('\n')
adjectives = open('adjectives.txt').read().split('\n')
scales = [l.replace('\n', '').split(';', maxsplit=1) for l in open('scales.txt')]

rooms = {}  # Store room data here

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists("ui/build/" + path):
        return send_from_directory('ui/build', path)
    else:
        return send_from_directory('ui/build', 'index.html')

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/api/join_room/<room_code>/<player_name>', methods=['POST'])
def join_room(room_code, player_name):
    """
    Join an existing room
    ---
    parameters:
        - name: room_code
          in: path
          required: true
        - name: player_name
          in: path
          required: true
    responses:
        200:
            description: Successfully joined the room
        404:
            description: Room not found
    """
    if room_code not in rooms:
        rooms[room_code] = {'players': {}, 'game_state': 'Waiting', 'score': 0}
    rooms[room_code]['players'][player_name] = {'score': 0}
    return jsonify({'status': 'joined', 'room_code': room_code}), 200

@app.route('/api/get_room/<room_code>', methods=['GET'])
def get_room(room_code):
    """
    Get room data
    ---
    parameters:
        - name: room_code
          in: path
          required: true
    responses:
        200:
            description: Room data
        404:
            description: Room not found
    """
    room_data = rooms.get(room_code)
    if room_data:
        return jsonify(room_data), 200
    else:
        return jsonify({'status': 'Room not found'}), 404

@app.route('/api/player_name', methods=['POST'])
def set_player_name():
    """
    Set player name
    ---
    parameters:
        - name: player_name
          in: formData
          required: true
    responses:
        200:
            description: Name set successfully
    """
    player_name = request.form.get('player_name')
    session['player_name'] = player_name
    return jsonify({'status': 'Name set'}), 200

@app.route('/api/player_name', methods=['GET'])
def get_player_name():
    """
    Set player name
    ---
    parameters:
        - name: player_name
          in: formData
          required: true
    responses:
        200:
            description: Name set successfully
    """
    if 'player_name' not in session:
        session['player_name'] = random.choice(adjectives) + ' ' + random.choice(nouns)
    return jsonify({"player_name": session['player_name']}), 200


@app.route('/api/room/<room_code>', methods=['POST'])
def change_room_state(room_code):
    """
    Set room state
    ---
    parameters:
        - name: gameState
          in: formData
          required: true
    responses:
        200:
            description: State set successfully
    """
    if request.json['gameState'] == 'Setup':
        setup_game(room_code)
    rooms[room_code]['game_state'] = request.json['gameState']
    return jsonify(rooms[room_code]), 200


def setup_game(room_code):
    n_players = len(rooms[room_code]['players'])
    if n_players <= 1:
        raise Exception('Need at least 2 players.')
    n_rounds = 3
    if n_players >= 4:
        n_rounds -= 1
    if n_players >= 6:
        n_rounds -= 1

    rounds_data = []
    for round in range(n_rounds):
        rounds_data.append({'players': {}})
        for player in rooms[room_code]['players'].keys():
            rounds_data[-1]['players'][player] = {
                'scale': random.choice(scales),
                'point': random.uniform(0.0, 1.0),
            }
    rooms[room_code]['rounds'] = rounds_data

@app.route('/api/room/<room_code>/clues', methods=['POST'])
def submit_clues(room_code):
    for i, clue in enumerate(request.json['clues']):
        rooms[room_code]['rounds'][i]['players'][request.json['player']]['clue'] = clue
    if all(p.get('clue') is not None for p in rooms[room_code]['rounds'][0]['players'].values()):
        rooms[room_code]['game_state'] = 'Guessing'
        sorted_players = sorted(rooms[room_code]['players'].keys())
        rooms[room_code]['game_idx'] = [0, 0, sorted_players[0]]
        rooms[room_code]['guesses'] = {
            p: 0.5
            for p in sorted_players
            if p != rooms[room_code]['game_idx'][2]
        }
        rooms[room_code]['guess_count'] = 0
    return jsonify(rooms[room_code]), 200

@app.route('/api/room/<room_code>/guess', methods=['POST'])
def update_guess(room_code):
    player_name = session['player_name']
    if player_name != rooms[room_code]['game_idx'][2]:
        rooms[room_code]['guesses'][player_name] = request.json['guess']
    return jsonify(rooms[room_code]), 200

@app.route('/api/room/<room_code>/submit_guess', methods=['POST'])
def submit_guess(room_code):
    round_idx, clue_player_idx, clue_player_name = rooms[room_code]['game_idx']
    rooms[room_code]['guess_count'] += 1
    n_players = len(rooms[room_code]['players'])
    if rooms[room_code]['guess_count'] >= n_players - 1:
        # Add score
        real_point = rooms[room_code]['rounds'][round_idx]['players'][clue_player_name]['point']
        overall_points = 0
        for player, guess in rooms[room_code]['guesses'].items():
            player_points = 100 * (1 - abs(real_point - float(guess)))
            overall_points += player_points
            rooms[room_code]['players'][player]['score'] += player_points
        rooms[room_code]['score'] += overall_points / (n_players - 1)
        rooms[room_code]['players'][clue_player_name]['score'] += overall_points / (n_players - 1)

        # Next round
        clue_player_idx += 1
        if clue_player_idx >= n_players:
            clue_player_idx = 0
            round_idx += 1
        if round_idx >= len(rooms[room_code]['rounds']):
            # Game over
            rooms[room_code]['game_state'] = 'Waiting'
            for k in ['guesses', 'game_idx', 'guess_count', 'rounds']:
                rooms[room_code].pop(k)
        else:
            sorted_players = sorted(rooms[room_code]['players'].keys())
            rooms[room_code]['game_idx'] = [round_idx, clue_player_idx, sorted_players[clue_player_idx]]
            rooms[room_code]['guesses'] = {
                p: 0.5
                for p in sorted_players
                if p != rooms[room_code]['game_idx'][2]
            }
            rooms[room_code]['guess_count'] = 0
        print('AAAAAAA', round_idx, clue_player_idx, rooms[room_code])
    return jsonify(rooms[room_code]), 200

if __name__ == '__main__':
    socketio.run(app, debug=True)
