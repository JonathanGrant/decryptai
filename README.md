# DecryptAI - AI-Powered Decrypto Game

A web-based implementation of the popular code-breaking game Decrypto, enhanced with AI players that can give clever clues and attempt to intercept codes.

## Game Rules

### Overview
Decrypto is a competitive code-breaking game where two teams try to communicate secret codes while preventing the opposing team from intercepting them.

### Setup
- **Teams**: Two teams (Red and Blue), each with 2-8 players
- **Code Words**: Each team receives 4 secret code words (numbered 1, 2, 3, 4) that only their team can see
- **Barriers**: Teams sit with barriers to hide their code words from opponents

### Gameplay

#### Round Structure
1. **Code Assignment**: The active team receives a 3-digit code (e.g., 4-2-1 or 3-1-4)
2. **Clue Giving**: One designated "Encryptor" gives one clue for each number in the code
   - Clues must relate to their team's secret code words
   - Clues cannot be too obvious or contain the actual word
   - Example: If code word #2 is "OCEAN", clue might be "waves" or "salty"
3. **Guessing Phase**: 
   - **Team Guessing**: The Encryptor's teammates try to guess the 3-digit code
   - **Interception Attempt**: The opposing team simultaneously tries to guess the code

#### Clue Guidelines
- ✅ **Good clues**: Related but not obvious (for "PIANO" → "Chopsticks")
- ❌ **Bad clues**: Too obvious ("KEYS" for "PIANO"), rhyming, translations, or containing the word

#### Scoring
- **Successful Communication**: If the active team guesses their code correctly, they earn 1 point
- **Interception**: If the opposing team guesses the code correctly, they earn 1 interception token
- **Failed Communication**: If neither team guesses correctly, no points awarded

#### Turn Rotation
Teams alternate being the active team each round.

### Winning Conditions
- **Victory**: First team to successfully communicate 8 codes wins
- **Defeat**: First team to receive 2 interception tokens loses (they've been "decoded")

### AI Enhancement Features
- **AI Encryptors**: AI players can give contextual, clever clues
- **AI Guessers**: AI can attempt to guess codes based on clue patterns
- **Difficulty Levels**: AI can be tuned for different skill levels
- **Learning**: AI adapts to team's cluing patterns over time

## Technical Implementation

### Game Modes
1. **Human vs AI Team**: Player team vs full AI opposition
2. **Mixed Teams**: Human players with AI teammates
3. **Spectator Mode**: Watch two AI teams compete
4. **Training Mode**: Practice with helpful AI hints

### Features
- Real-time multiplayer with WebSocket support
- AI-powered clue generation using GPT models
- Pattern recognition for interception attempts
- Mobile-responsive interface
- Game history and statistics
- Custom word lists and themes

## Getting Started

### Installation
```bash
npm install
pip install -r requirements.txt
```

### Development
```bash
# Start backend server
python server.py

# Start frontend development server
cd ui && npm start
```

### Deployment
Deployed on Railway with automatic builds from GitHub.

## Technology Stack
- **Backend**: Python Flask with SocketIO
- **Frontend**: React with Material-UI
- **AI**: OpenAI GPT models for clue generation
- **Deployment**: Railway
- **Database**: In-memory game state (Redis for production)

## Contributing
This is a learning project exploring AI game mechanics and real-time multiplayer functionality.