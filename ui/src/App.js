import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Container from '@mui/material/Container';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import './App.css';

import GameAppBar from './AppBar';
import GameSetup from './GameSetup';
import GameGuess from './GameGuess';

axios.defaults.withCredentials = true;


const URL = "/api"

const App = () => {
  const [playerName, setPlayerName] = useState('');
  const [playerNameHasSet, setPlayerNameHasSet] = useState(false);
  const [roomCode, setRoomCode] = useState('');
  const [roomData, setRoomData] = useState(null);
  const [setupGame, setSetupGame] = useState(false);

  const startGame = async () => {
    try {
      const response = await axios.post(`${URL}/room/${roomCode}`, {gameState: 'Setup'});
      setSetupGame(false)
      setRoomData(response.data);
    } catch (error) {
      console.error('Could not create room:', error);
    }
  };

  const joinRoom = async () => {
    try {
      await axios.post(`${URL}/join_room/${roomCode}/${playerName}`);
      getRoomData();
    } catch (error) {
      console.error('Could not join room:', error);
    }
  };

  const getRoomData = async () => {
    try {
      const response = await axios.get(`${URL}/get_room/${roomCode}`);
      setRoomData(response.data);
    } catch (error) {
      console.error('Could not get room data:', error);
    }
  };

  const setPlayer = async () => {
    try {
      setPlayerNameHasSet(true)
      await axios.post(`${URL}/player_name`, { player_name: playerName });
    } catch (error) {
      console.error('Could not set player name:', error);
    }
  };

  const submitClues = async (clues) => {
    try {
      const response = await axios.post(`${URL}/room/${roomCode}/clues`, {clues: clues, player: playerName});
      setRoomData(response.data);
      setSetupGame(true);
    } catch (error) {
      console.error('Could not submit clues:', error);
    }
  }

  const updateGuess = async (guess) => {
    try {
      const response = await axios.post(`${URL}/room/${roomCode}/guess`, {guess: guess, player: playerName});
      setRoomData(response.data);
    } catch (error) {
      console.error('Could not updateGuess:', error);
    }
  }

  const submitGuess = async () => {
    try {
      const response = await axios.post(`${URL}/room/${roomCode}/submit_guess`);
      setRoomData(response.data);
    } catch (error) {
      console.error('Could not submitGuess:', error);
    }
  }

  useEffect(() => {
    const fetchRoomInfo = async () => {
      try {
        const response = await axios.get(`${URL}/get_room/${roomCode}`);
        setRoomData(response.data);
        console.log(response.data)
      } catch (error) {
        console.error('Error fetching room info:', error);
      }
    };

    const intervalId = setInterval(() => {
      if (roomCode) fetchRoomInfo();
    }, 2000); // polling every 2 seconds

    // Cleanup: clear the interval when the component is unmounted
    return () => clearInterval(intervalId);
  }, [roomCode]);

  return (
    <div className="App">
      <GameAppBar playerName={playerName} />
      <Container>
        <div className="game-container">
          <Typography variant="h3" className="game-title">🎯 wAIvelength Game</Typography>

          {!playerNameHasSet ? (
            <div style={{ marginBottom: '20px' }}>
              <TextField
                label="Player Name"
                value={playerName}
                onChange={(e) => {setPlayerName(e.target.value);}}
                className="input-field"
                variant="outlined"
              />
              <br />
              <Button className="game-button" onClick={setPlayer}>
                Set Player Name
              </Button>
            </div>
          ) : null}

          <div style={{ marginBottom: '20px' }}>
            <TextField
              label="Room Code"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value)}
              className="input-field"
              variant="outlined"
            />
            <br />
            <Button className="game-button" onClick={joinRoom}>
              Join Room
            </Button>
          </div>

          {roomData && roomData.game_state === 'Waiting' ? (
            <div className="status-waiting">
              <Typography variant="h6">🎮 Ready to Play!</Typography>
              <Button className="game-button" onClick={startGame}>
                Start Game
              </Button>
            </div>
          ) : null}

          {roomData && roomData.game_state === 'Setup' && (
            <div className="status-setup">
              <Typography variant="h6">📝 Setting Up Game</Typography>
            </div>
          )}

          {roomData && roomData.game_state === 'Guessing' && (
            <div className="status-guessing">
              <Typography variant="h6">🤔 Guessing Phase</Typography>
            </div>
          )}

          {roomData && (
            <div className="score-display">
              <Typography variant="h6">🏆 Game Status</Typography>
              <Typography variant="h4" style={{ color: '#667eea', fontWeight: 'bold' }}>
                Total Score: {roomData.score.toFixed(2)}
              </Typography>
              <Typography variant="h6" style={{ marginTop: '20px' }}>👥 Players:</Typography>
              {Object.keys(roomData.players).map((player) => (
                <div 
                  key={player} 
                  className={player.startsWith('[AI]') ? 'ai-player-card' : 'player-card'}
                >
                  <Typography variant="h6">
                    {player.startsWith('[AI]') ? '🤖 ' : '👤 '}{player}
                  </Typography>
                  <Typography variant="body1">
                    Score: {roomData.players[player].score.toFixed(2)} 
                    <span style={{ color: '#ffeb3b' }}>
                      (+{roomData.players[player].last_score.toFixed(2)})
                    </span>
                  </Typography>
                </div>
              ))}
            </div>
          )}

          {roomData && roomData.game_state === 'Setup' && !setupGame ? (
            <GameSetup playerName={playerName} rounds={roomData.rounds} submit={submitClues}/>
          ) : null}

          {roomData && roomData.game_state === 'Guessing' ? (
            <GameGuess 
              myName={playerName} 
              game_idx={roomData.game_idx} 
              guesses={roomData.guesses} 
              guessReasons={roomData.guess_reason} 
              rounds={roomData.rounds} 
              updateGuess={updateGuess} 
              submitGuess={submitGuess} 
            />
          ) : null}
        </div>
      </Container>
    </div>
  );
};

export default App;
