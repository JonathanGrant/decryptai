import os
import random
import string
import json
import threading
import functools
import structlog
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
from flasgger import Swagger
from ai_player import DecryptoAI

logger = structlog.getLogger()

# Paths for deployment
prefix = '/root/decryptai/'
if not os.path.exists(prefix):
    prefix = '/Users/jong/Documents/decryptai/'
if not os.path.exists(prefix):
    prefix = '/app/'

app = Flask(__name__, static_folder=prefix+'ui/build')
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = 'decrypto_secret'
socketio = SocketIO(app, cors_allowed_origins="*")
swagger = Swagger(app)

# Load code words
code_words = []
try:
    with open(prefix + 'code_words.txt', 'r') as f:
        code_words = [word.strip().upper() for word in f.readlines() if word.strip()]
    logger.info(f"Loaded {len(code_words)} code words")
except FileNotFoundError:
    logger.error("code_words.txt not found")
    code_words = ['OCEAN', 'GUITAR', 'THUNDER', 'CASTLE']  # Fallback

# Game state storage
rooms = {}

# Game constants
TEAM_COLORS = ['red', 'blue']
GAME_PHASES = ['setup', 'clue_giving', 'guessing', 'scoring', 'finished']
CODE_WORDS_PER_TEAM = 4
CODES_TO_WIN = 8
INTERCEPTIONS_TO_LOSE = 2

class DecryptoGame:
    def __init__(self, room_code):
        self.room_code = room_code
        self.teams = {
            'red': {
                'players': [],
                'code_words': [],
                'successful_codes': 0,
                'interception_tokens': 0,
                'ai_players': []
            },
            'blue': {
                'players': [],
                'code_words': [],
                'successful_codes': 0,
                'interception_tokens': 0,
                'ai_players': []
            }
        }
        self.current_round = 1
        self.current_team = 'red'  # Which team is giving clues
        self.phase = 'setup'
        self.current_code = None  # 3-digit code like [4, 2, 1]
        self.current_clues = []   # Clues for current code
        self.team_guesses = {}    # Guesses from both teams
        self.round_history = []   # History of all rounds
        self.winner = None

    def to_dict(self):
        """Convert game state to dictionary for API responses"""
        return {
            'room_code': self.room_code,
            'teams': self.teams,
            'current_round': self.current_round,
            'current_team': self.current_team,
            'phase': self.phase,
            'current_code': self.current_code if self.phase in ['clue_giving', 'guessing'] else None,
            'current_clues': self.current_clues,
            'team_guesses': self.team_guesses,
            'winner': self.winner,
            'round_history': self.round_history
        }

    def add_player(self, player_name, team_color):
        """Add a player to a team"""
        if team_color in self.teams:
            if player_name not in self.teams[team_color]['players']:
                self.teams[team_color]['players'].append(player_name)
                return True
        return False

    def add_ai_players(self, team_color, count=2):
        """Add AI players to a team"""
        if team_color in self.teams:
            ai_names = [f"AI {i+1}" for i in range(count)]
            self.teams[team_color]['ai_players'].extend(ai_names)
            return True
        return False

    def generate_code_words(self, team_color):
        """Generate 4 random code words for a team"""
        if team_color in self.teams and len(code_words) >= CODE_WORDS_PER_TEAM:
            selected_words = random.sample(code_words, CODE_WORDS_PER_TEAM)
            self.teams[team_color]['code_words'] = selected_words
            logger.info(f"Generated code words for team {team_color}: {selected_words}")
            return selected_words
        return []

    def set_code_words(self, team_color, words):
        """Set the 4 code words for a team"""
        if team_color in self.teams and len(words) == CODE_WORDS_PER_TEAM:
            self.teams[team_color]['code_words'] = words
            return True
        return False

    def generate_code(self):
        """Generate a random 3-digit code"""
        return random.choices(range(1, CODE_WORDS_PER_TEAM + 1), k=3)

    def start_round(self):
        """Start a new round"""
        if self.phase == 'setup' and self.all_teams_ready():
            self.current_code = self.generate_code()
            self.current_clues = []
            self.team_guesses = {}
            self.phase = 'clue_giving'
            logger.info(f"Round {self.current_round} started for team {self.current_team}, code: {self.current_code}")
            
            # If current team is AI, generate clues automatically
            if self.teams[self.current_team].get('ai_players'):
                threading.Thread(target=self._ai_generate_clues).start()
                
            return True
        return False

    def _ai_generate_clues(self):
        """Have AI team generate clues for their code"""
        try:
            ai = DecryptoAI(self.current_team)
            clues = ai.generate_clues(self.teams[self.current_team]['code_words'], self.current_code)
            self.submit_clues(clues)
            logger.info(f"AI team {self.current_team} generated clues: {clues}")
        except Exception as e:
            logger.error(f"Error in AI clue generation: {e}")
            # Fallback simple clues
            fallback_clues = [f"word{i}" for i in self.current_code]
            self.submit_clues(fallback_clues)

    def all_teams_ready(self):
        """Check if both teams have code words set"""
        for team in self.teams.values():
            if len(team['code_words']) != CODE_WORDS_PER_TEAM:
                return False
        return True

    def submit_clues(self, clues):
        """Submit clues for the current code"""
        if self.phase == 'clue_giving' and len(clues) == 3:
            self.current_clues = clues
            self.phase = 'guessing'
            logger.info(f"Clues submitted: {clues}")
            
            # Trigger AI guessing for opposing team
            other_team = 'blue' if self.current_team == 'red' else 'red'
            if self.teams[other_team].get('ai_players'):
                threading.Thread(target=self._ai_guess_code, args=(other_team,)).start()
                
            return True
        return False

    def _ai_guess_code(self, team_color):
        """Have AI team make a guess"""
        try:
            ai = DecryptoAI(team_color)
            
            # Get opponent's code words if any have been revealed through play
            opponent_team = 'red' if team_color == 'blue' else 'blue'
            opponent_words = self.teams[opponent_team]['code_words'] if len(self.round_history) > 2 else None
            
            guess = ai.guess_code(self.current_clues, opponent_words, self.round_history)
            self.submit_guess(team_color, guess)
            logger.info(f"AI team {team_color} guessed: {guess}")
        except Exception as e:
            logger.error(f"Error in AI guess: {e}")
            # Fallback random guess
            fallback_guess = random.choices(range(1, 5), k=3)
            self.submit_guess(team_color, fallback_guess)

    def submit_guess(self, team_color, guess):
        """Submit a guess from a team"""
        if self.phase == 'guessing' and len(guess) == 3:
            self.team_guesses[team_color] = guess
            logger.info(f"Team {team_color} guessed: {guess}")
            
            # Check if both teams have guessed
            if len(self.team_guesses) == 2:
                self.evaluate_round()
            return True
        return False

    def evaluate_round(self):
        """Evaluate the round and update scores"""
        self.phase = 'scoring'
        
        current_team_guess = self.team_guesses.get(self.current_team, [])
        other_team = 'blue' if self.current_team == 'red' else 'red'
        other_team_guess = self.team_guesses.get(other_team, [])
        
        # Check if current team guessed correctly
        if current_team_guess == self.current_code:
            self.teams[self.current_team]['successful_codes'] += 1
            logger.info(f"Team {self.current_team} successfully communicated!")
        
        # Check if other team intercepted
        if other_team_guess == self.current_code:
            self.teams[other_team]['interception_tokens'] += 1
            logger.info(f"Team {other_team} intercepted the code!")
        
        # Add to history
        self.round_history.append({
            'round': self.current_round,
            'team': self.current_team,
            'code': self.current_code,
            'clues': self.current_clues.copy(),
            'guesses': self.team_guesses.copy()
        })
        
        # Check win conditions
        if self.check_win_conditions():
            self.phase = 'finished'
        else:
            self.next_round()

    def check_win_conditions(self):
        """Check if game should end"""
        for team_color, team in self.teams.items():
            # Win by successful communication
            if team['successful_codes'] >= CODES_TO_WIN:
                self.winner = team_color
                logger.info(f"Team {team_color} wins by successful communication!")
                return True
            
            # Lose by too many interceptions
            if team['interception_tokens'] >= INTERCEPTIONS_TO_LOSE:
                other_team = 'blue' if team_color == 'red' else 'red'
                self.winner = other_team
                logger.info(f"Team {other_team} wins by intercepting team {team_color}!")
                return True
        
        return False

    def next_round(self):
        """Advance to next round"""
        # Switch teams
        self.current_team = 'blue' if self.current_team == 'red' else 'red'
        self.current_round += 1
        self.phase = 'clue_giving'
        
        # Generate new code
        self.current_code = self.generate_code()
        self.current_clues = []
        self.team_guesses = {}
        
        logger.info(f"Round {self.current_round} - Team {self.current_team}'s turn")
        
        # If new current team is AI, generate clues automatically
        if self.teams[self.current_team].get('ai_players'):
            threading.Thread(target=self._ai_generate_clues).start()

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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'game': 'decrypto'}), 200

@app.route('/api/create_room', methods=['POST'])
def create_room():
    """Create a new game room"""
    room_code = generate_room_code()
    rooms[room_code] = DecryptoGame(room_code)
    logger.info(f"Created room {room_code}")
    return jsonify({'room_code': room_code, 'status': 'created'}), 200

@app.route('/api/join_room/<room_code>/<team_color>/<player_name>', methods=['POST'])
def join_room(room_code, team_color, player_name):
    """Join a game room as a specific team"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    if team_color not in TEAM_COLORS:
        return jsonify({'error': 'Invalid team color'}), 400
    
    game = rooms[room_code]
    if game.add_player(player_name, team_color):
        logger.info(f"Player {player_name} joined team {team_color} in room {room_code}")
        return jsonify({'status': 'joined', 'game_state': game.to_dict()}), 200
    else:
        return jsonify({'error': 'Could not join team'}), 400

@app.route('/api/room/<room_code>', methods=['GET'])
def get_room(room_code):
    """Get current state of a room"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    game = rooms[room_code]
    return jsonify(game.to_dict()), 200

@app.route('/api/room/<room_code>/set_words/<team_color>', methods=['POST'])
def set_code_words(room_code, team_color):
    """Set code words for a team"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    if team_color not in TEAM_COLORS:
        return jsonify({'error': 'Invalid team color'}), 400
    
    data = request.get_json()
    words = data.get('words', [])
    
    game = rooms[room_code]
    if game.set_code_words(team_color, words):
        logger.info(f"Set code words for team {team_color} in room {room_code}")
        return jsonify({'status': 'words_set', 'game_state': game.to_dict()}), 200
    else:
        return jsonify({'error': 'Invalid words'}), 400

@app.route('/api/room/<room_code>/start_round', methods=['POST'])
def start_round(room_code):
    """Start a new round"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    game = rooms[room_code]
    if game.start_round():
        return jsonify({'status': 'round_started', 'game_state': game.to_dict()}), 200
    else:
        return jsonify({'error': 'Cannot start round'}), 400

@app.route('/api/room/<room_code>/submit_clues', methods=['POST'])
def submit_clues(room_code):
    """Submit clues for the current code"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    data = request.get_json()
    clues = data.get('clues', [])
    
    game = rooms[room_code]
    if game.submit_clues(clues):
        return jsonify({'status': 'clues_submitted', 'game_state': game.to_dict()}), 200
    else:
        return jsonify({'error': 'Invalid clues'}), 400

@app.route('/api/room/<room_code>/submit_guess/<team_color>', methods=['POST'])
def submit_guess(room_code, team_color):
    """Submit a guess for the current code"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    if team_color not in TEAM_COLORS:
        return jsonify({'error': 'Invalid team color'}), 400
    
    data = request.get_json()
    guess = data.get('guess', [])
    
    game = rooms[room_code]
    if game.submit_guess(team_color, guess):
        return jsonify({'status': 'guess_submitted', 'game_state': game.to_dict()}), 200
    else:
        return jsonify({'error': 'Invalid guess'}), 400

@app.route('/api/room/<room_code>/add_ai/<team_color>', methods=['POST'])
def add_ai_team(room_code, team_color):
    """Add AI players to a team"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    if team_color not in TEAM_COLORS:
        return jsonify({'error': 'Invalid team color'}), 400
    
    game = rooms[room_code]
    if game.add_ai_players(team_color, 2):
        logger.info(f"Added AI players to team {team_color} in room {room_code}")
        return jsonify({'status': 'ai_added', 'game_state': game.to_dict()}), 200
    else:
        return jsonify({'error': 'Could not add AI players'}), 400

@app.route('/api/room/<room_code>/generate_words/<team_color>', methods=['POST'])
def generate_words(room_code, team_color):
    """Generate random code words for a team"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    if team_color not in TEAM_COLORS:
        return jsonify({'error': 'Invalid team color'}), 400
    
    game = rooms[room_code]
    words = game.generate_code_words(team_color)
    if words:
        return jsonify({'status': 'words_generated', 'words': words, 'game_state': game.to_dict()}), 200
    else:
        return jsonify({'error': 'Could not generate words'}), 400

@app.route('/api/room/<room_code>/ai_clues', methods=['POST'])
def generate_ai_clues(room_code):
    """Manually trigger AI clue generation (for testing)"""
    if room_code not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    game = rooms[room_code]
    if game.phase != 'clue_giving':
        return jsonify({'error': 'Not in clue giving phase'}), 400
    
    if not game.teams[game.current_team].get('ai_players'):
        return jsonify({'error': 'Current team is not AI'}), 400
    
    threading.Thread(target=game._ai_generate_clues).start()
    return jsonify({'status': 'ai_clues_generating'}), 200

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host="0.0.0.0", port=port)

print("DecryptAI server initialized successfully!")