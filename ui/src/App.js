import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Container from '@mui/material/Container';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

import GameAppBar from './AppBar';
import GameSetup from './GameSetup';
import GameGuess from './GameGuess';

axios.defaults.withCredentials = true;


const URL = "/api"

const App = () => {
  const [playerName, setPlayerName] = useState('');
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
      const response = await axios.post(`${URL}/room/${roomCode}/guess`, {guess: guess, player_name: playerName});
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
    // ONLOAD Call
    // Fetch the player name from the server when the component mounts
    axios.get(`${URL}/player_name`)
      .then(response => {
        // Set the player name in the state
        setPlayerName(response.data.player_name);
      })
      .catch(error => {
        console.error('There was an error fetching the player name:', error);
      });
  }, []);

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
    <div>
      <GameAppBar playerName={playerName} />
    <Container>
      <Typography variant="h4">wAIvelength Game</Typography>

      <TextField
        label="Player Name"
        value={playerName}
        onChange={(e) => setPlayerName(e.target.value)}
      />
      <Button variant="contained" color="primary" onClick={setPlayer}>
        Set Player Name
      </Button>

      <TextField
        label="Room Code"
        value={roomCode}
        onChange={(e) => setRoomCode(e.target.value)}
      />
      <Button variant="contained" color="primary" onClick={joinRoom}>
        Join Room
      </Button>

      {roomData && roomData.game_state === 'Waiting' ? (<Button variant="contained" color="secondary" onClick={startGame}>
        Start Game
      </Button>) : null}

      {roomData && (
        <div>
          <Typography variant="h6">Room Data:</Typography>
          <Typography variant="body1">Game State: {roomData.game_state}</Typography>
          <Typography variant="body1">Score: {roomData.score}</Typography>
          <Typography variant="body1">Players:</Typography>
          {Object.keys(roomData.players).map((player) => (
            <Typography key={player} variant="body2">
              {player}: {roomData.players[player].score}
            </Typography>
          ))}
        </div>
      )}

      {roomData && roomData.game_state === 'Setup' && !setupGame ? (<GameSetup playerName={playerName} rounds={roomData.rounds} submit={submitClues}/>) : null}

      {roomData && roomData.game_state === 'Guessing' ? (<GameGuess myName={playerName} game_idx={roomData.game_idx} guesses={roomData.guesses} rounds={roomData.rounds} updateGuess={updateGuess} submitGuess={submitGuess} />) : null}
    </Container>
    </div>
  );
};

export default App;
