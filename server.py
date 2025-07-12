import os
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
from flasgger import Swagger
import json
import random
import string
import retrying
import threading
import functools
import structlog

logger = structlog.getLogger()

from ChatPodcastGPT import Chat


prefix = '/root/waivelength/'
if not os.path.exists(prefix):
    prefix = '/Users/jong/Documents/waivelength/'
if not os.path.exists(prefix):
    prefix = '/app/'
AI_PREFIX = "[AI] "

app = Flask(__name__, static_folder=prefix+'ui/build')
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins="*")
swagger = Swagger(app)

nouns      = open(prefix+'nouns.txt'     ).read().split('\n')
adjectives = open(prefix+'adjectives.txt').read().split('\n')
ais        = open(prefix+'ais.txt'       ).read().split('\n')
scales = [l.replace('\n', '').split(';', maxsplit=1) for l in open(prefix+'scales.txt')]

rooms = {}  # Store room data here

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(prefix+"ui/build/" + path):
        return send_from_directory(prefix+'ui/build', path)
    else:
        return send_from_directory(prefix+'ui/build', 'index.html')

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
        # Create room with 3 AI players
        ai_players = {}
        for i in range(3):
            ai_name = AI_PREFIX + random.choice(adjectives) + ' ' + random.choice(ais)
            ai_players[ai_name] = {'score': 0, 'last_score': 0}
        rooms[room_code] = {'players': ai_players, 'game_state': 'Waiting', 'score': 0}
    rooms[room_code]['players'][player_name] = {'score': 0, 'last_score': 0}
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
    return jsonify({"player_name": random.choice(adjectives) + ' ' + random.choice(nouns)}), 200


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


def begin_guessing(room_code):
    rooms[room_code]['game_state'] = 'Guessing'
    sorted_players = sorted(rooms[room_code]['players'].keys())
    rooms[room_code]['game_idx'] = [0, 0, sorted_players[0]]
    rooms[room_code]['guesses'] = {
        p: 0.5
        for p in sorted_players
        if p != rooms[room_code]['game_idx'][2]
    }
    rooms[room_code]['guess_count'] = 0
    rooms[room_code]['guess_reason'] = {}
    threading.Thread(target=functools.partial(ai_guess, room_code)).start()


def ai_guess(room_code):
    ai_player = [p for p in rooms[room_code]['players'] if p.startswith(AI_PREFIX)][0]
    round_idx, player_idx, player = rooms[room_code]['game_idx']
    if ai_player == player: return
    ai = AIPlayer(personality=ai_player.split(AI_PREFIX)[1])
    data = rooms[room_code]['rounds'][round_idx]['players'][player]
    ai_guess_data = ai.guess(data['scale'], data['clue'])
    rooms[room_code]['guesses'][ai_player] = ai_guess_data['guess']
    rooms[room_code]['guess_reason'][ai_player] = ai_guess_data['reason']
    rooms[room_code]['guess_count'] += 1
    check_for_next_round(room_code)

def ai_clue(room_code, round, player):
    data = rooms[room_code]['rounds'][-1]['players'][player]
    ai = AIPlayer(personality=player.split(AI_PREFIX)[1])
    rooms[room_code]['rounds'][round]['players'][player]['clue'] = ai.give_clue(data['scale'], data['point'])
    if all(round_data['players'][player].get('clue') is not None for round_data in rooms[room_code]['rounds']):
        if all(p.get('clue') is not None for p in rooms[room_code]['rounds'][0]['players'].values()):
            begin_guessing(room_code)

def setup_game(room_code):
    n_players = len(rooms[room_code]['players'])
    if n_players <= 1:
        raise Exception('Need at least 2 players.')
    n_rounds = 3
    if n_players >= 4:
        n_rounds -= 1
    if n_players >= 6:
        n_rounds -= 1

    rooms[room_code]['rounds'] = []
    for round in range(n_rounds):
        rooms[room_code]['rounds'].append({'players': {}})
        for player in rooms[room_code]['players'].keys():
            rooms[room_code]['rounds'][-1]['players'][player] = {
                'scale': random.choice(scales),
                'point': random.uniform(0.0, 1.0),
            }
            if player.startswith(AI_PREFIX):
                threading.Thread(target=functools.partial(ai_clue, room_code, round, player)).start()

@app.route('/api/room/<room_code>/clues', methods=['POST'])
def submit_clues(room_code):
    for i, clue in enumerate(request.json['clues']):
        rooms[room_code]['rounds'][i]['players'][request.json['player']]['clue'] = clue
    if all(p.get('clue') is not None for p in rooms[room_code]['rounds'][0]['players'].values()):
        begin_guessing(room_code)
    return jsonify(rooms[room_code]), 200

@app.route('/api/room/<room_code>/guess', methods=['POST'])
def update_guess(room_code):
    player_name = request.json['player']
    if player_name != rooms[room_code]['game_idx'][2]:
        rooms[room_code]['guesses'][player_name] = request.json['guess']
    return jsonify(rooms[room_code]), 200


def check_for_next_round(room_code):
    round_idx, clue_player_idx, clue_player_name = rooms[room_code]['game_idx']
    n_players = len(rooms[room_code]['players'])
    if rooms[room_code]['guess_count'] >= n_players - 1:
        # Add score
        real_point = rooms[room_code]['rounds'][round_idx]['players'][clue_player_name]['point']
        overall_points = 0
        for player, guess in rooms[room_code]['guesses'].items():
            player_points = 100 * (1 - abs(real_point - float(guess)))
            overall_points += player_points
            rooms[room_code]['players'][player]['score'] += player_points
            rooms[room_code]['players'][player]['last_score'] = player_points
        rooms[room_code]['score'] += overall_points / (n_players - 1)
        rooms[room_code]['players'][clue_player_name]['score'] += overall_points / (n_players - 1)
        rooms[room_code]['players'][clue_player_name]['last_score'] = overall_points / (n_players - 1)

        # Next round
        clue_player_idx += 1
        if clue_player_idx >= n_players:
            clue_player_idx = 0
            round_idx += 1
        if round_idx >= len(rooms[room_code]['rounds']):
            # Game over
            rooms[room_code]['game_state'] = 'Waiting'
            for k in ['guesses', 'game_idx', 'guess_count', 'guess_reason', 'rounds']:
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
            rooms[room_code]['guess_reason'] = {}
            threading.Thread(target=functools.partial(ai_guess, room_code)).start()

@app.route('/api/room/<room_code>/submit_guess', methods=['POST'])
def submit_guess(room_code):
    round_idx, clue_player_idx, clue_player_name = rooms[room_code]['game_idx']
    rooms[room_code]['guess_count'] += 1
    check_for_next_round(room_code)
    return jsonify(rooms[room_code]), 200


class AIPlayer:
    def __init__(self, skill_level = 'expert', personality = 'Elon Musk'):
        self.skill_level = skill_level
        self.personality = personality

    @retrying.retry(stop_max_attempt_number=5, wait_fixed=2000)
    def give_clue(self, scale, point):
        chat = Chat(f"""You are an {self.skill_level} clue giver with the strong personality of {self.personality}.
Respond in plaintext, only your clue, nothing else.
Your clue cannot explicitly mention the scale.""".replace('\n', ' '))
        return chat.message(f"""Give a clue for a point {point} on the scale of "{scale[0]}" to "{scale[1]}".""")

    @retrying.retry(stop_max_attempt_number=5, wait_fixed=2000)
    def guess(self, scale, clue):
        chat = Chat(f"""You are an {self.skill_level} clue guesser with the strong personality of {self.personality}.
Respond in JSON with your reasoning (string) and guess (a float from 0.0-1.0), nothing else.
Example: {{"reason": "...", "guess": 0.53}}.
Only respond in JSON and nothing else.
Your reasoning must be overwhelmingly in the voice of {self.personality}""")
        data = chat.message(f"""Given this clue "{clue}" on this scale "{scale[0]}" (0) to "{scale[1]}" (1), what is your best guess for the point along the scale?""")
        try:
            data = json.loads(data)
        except:
            logger.error("Cannot parse JSON data from Chat: " + data)
            raise
        if 'reason' not in data or 'guess' not in data:
            logger.error("Missing reason or guess in JSON data from Chat: " + data)
            raise Exception("Missing reason or guess in JSON data from Chat: " + data)
        data['guess'] = float(data['guess'])
        return data


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host="0.0.0.0", port=port)

# For gunicorn
print("Flask app initialized successfully!")
