import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Button,
  TextField,
  Card,
  CardContent,
  Grid,
  Box,
  Chip,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import './App.css';

axios.defaults.withCredentials = true;

const API_URL = '/api';

interface GameState {
  room_code: string;
  teams: {
    red: {
      players: string[];
      code_words: string[];
      successful_codes: number;
      interception_tokens: number;
      ai_players: string[];
    };
    blue: {
      players: string[];
      code_words: string[];
      successful_codes: number;
      interception_tokens: number;
      ai_players: string[];
    };
  };
  current_round: number;
  current_team: 'red' | 'blue';
  phase: 'setup' | 'clue_giving' | 'guessing' | 'scoring' | 'finished';
  current_code?: number[];
  current_clues: string[];
  team_guesses: Record<string, number[]>;
  winner?: string;
  round_history?: Array<{
    round: number;
    team: string;
    code: number[];
    clues: string[];
    guesses: Record<string, number[]>;
  }>;
}

const App: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [roomCode, setRoomCode] = useState('');
  const [playerName, setPlayerName] = useState('');
  const [selectedTeam, setSelectedTeam] = useState<'red' | 'blue'>('red');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentGuess, setCurrentGuess] = useState<number[]>([1, 1, 1]);

  const createRoom = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/create_room`);
      setRoomCode(response.data.room_code);
      setError('');
    } catch (err) {
      setError('Failed to create room');
    } finally {
      setLoading(false);
    }
  };

  const joinRoom = async () => {
    if (!roomCode || !playerName || !selectedTeam) {
      setError('Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(
        `${API_URL}/join_room/${roomCode}/${selectedTeam}/${playerName}`
      );
      setGameState(response.data.game_state);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to join room');
    } finally {
      setLoading(false);
    }
  };

  const addAIToTeam = async (teamColor: 'red' | 'blue') => {
    if (!gameState) return;
    
    try {
      const response = await axios.post(`${API_URL}/room/${gameState.room_code}/add_ai/${teamColor}`);
      setGameState(response.data.game_state);
    } catch (err) {
      setError('Failed to add AI to team');
    }
  };

  const generateWords = async (teamColor: 'red' | 'blue') => {
    if (!gameState) return;
    
    try {
      const response = await axios.post(`${API_URL}/room/${gameState.room_code}/generate_words/${teamColor}`);
      setGameState(response.data.game_state);
    } catch (err) {
      setError('Failed to generate words');
    }
  };

  const startGame = async () => {
    if (!gameState) return;
    
    try {
      const response = await axios.post(`${API_URL}/room/${gameState.room_code}/start_round`);
      setGameState(response.data.game_state);
    } catch (err) {
      setError('Failed to start game');
    }
  };

  const submitGuess = async () => {
    if (!gameState) return;
    
    const myTeam = gameState.teams.red.players.includes(playerName) ? 'red' : 'blue';
    
    try {
      const response = await axios.post(
        `${API_URL}/room/${gameState.room_code}/submit_guess/${myTeam}`,
        { guess: currentGuess }
      );
      setGameState(response.data.game_state);
    } catch (err) {
      setError('Failed to submit guess');
    }
  };

  // Poll for game state updates
  useEffect(() => {
    if (!gameState) return;

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/room/${gameState.room_code}`);
        setGameState(response.data);
      } catch (err) {
        console.error('Failed to fetch game state');
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [gameState?.room_code]);

  const renderTeamCard = (teamColor: 'red' | 'blue') => {
    if (!gameState) return null;

    const team = gameState.teams[teamColor];
    const isMyTeam = team.players.includes(playerName);

    return (
      <Card sx={{ bgcolor: teamColor === 'red' ? '#ffebee' : '#e3f2fd' }}>
        <CardContent>
          <Typography variant="h6" sx={{ color: teamColor, fontWeight: 'bold' }}>
            Team {teamColor.toUpperCase()}
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2">Players:</Typography>
            {team.players.map((player) => (
              <Chip 
                key={player} 
                label={player} 
                size="small" 
                sx={{ mr: 1, mb: 1 }}
                color={player === playerName ? 'primary' : 'default'}
              />
            ))}
            {team.ai_players.map((ai) => (
              <Chip 
                key={ai} 
                label={`🤖 ${ai}`} 
                size="small" 
                sx={{ mr: 1, mb: 1 }}
                color="secondary"
              />
            ))}
          </Box>

          <Box sx={{ mt: 2 }}>
            <Typography variant="body2">
              Successful Codes: {team.successful_codes} | Interceptions: {team.interception_tokens}
            </Typography>
          </Box>

          {isMyTeam && team.code_words.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Your Code Words:</Typography>
              {team.code_words.map((word, index) => (
                <Chip 
                  key={index} 
                  label={`${index + 1}. ${word}`} 
                  sx={{ mr: 1, mb: 1 }}
                  variant="outlined"
                />
              ))}
            </Box>
          )}

          <Box sx={{ mt: 2 }}>
            {team.ai_players.length === 0 && (
              <Button 
                variant="outlined" 
                size="small" 
                onClick={() => addAIToTeam(teamColor)}
                sx={{ mr: 1 }}
              >
                Add AI Players
              </Button>
            )}
            {team.code_words.length === 0 && (
              <Button 
                variant="outlined" 
                size="small" 
                onClick={() => generateWords(teamColor)}
              >
                Generate Words
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  if (!gameState) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Typography variant="h3" align="center" gutterBottom>
          🔓 DecryptAI
        </Typography>
        
        <Card sx={{ mt: 4, p: 3 }}>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Create New Game</Typography>
                <Button 
                  variant="contained" 
                  fullWidth 
                  onClick={createRoom}
                  disabled={loading}
                >
                  Create Room
                </Button>
                {roomCode && (
                  <Alert severity="success" sx={{ mt: 2 }}>
                    Room created: {roomCode}
                  </Alert>
                )}
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Join Game</Typography>
                <TextField
                  label="Room Code"
                  value={roomCode}
                  onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                  fullWidth
                  sx={{ mb: 2 }}
                />
                <TextField
                  label="Your Name"
                  value={playerName}
                  onChange={(e) => setPlayerName(e.target.value)}
                  fullWidth
                  sx={{ mb: 2 }}
                />
                <Box sx={{ mb: 2 }}>
                  <Button
                    variant={selectedTeam === 'red' ? 'contained' : 'outlined'}
                    color="error"
                    onClick={() => setSelectedTeam('red')}
                    sx={{ mr: 1 }}
                  >
                    Red Team
                  </Button>
                  <Button
                    variant={selectedTeam === 'blue' ? 'contained' : 'outlined'}
                    color="primary"
                    onClick={() => setSelectedTeam('blue')}
                  >
                    Blue Team
                  </Button>
                </Box>
                <Button 
                  variant="contained" 
                  fullWidth 
                  onClick={joinRoom}
                  disabled={loading}
                >
                  Join Room
                </Button>
              </Grid>
            </Grid>
            
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </CardContent>
        </Card>
      </Container>
    );
  }

  const canStartGame = gameState.teams.red.code_words.length === 4 && 
                      gameState.teams.blue.code_words.length === 4 &&
                      gameState.phase === 'setup';

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h4" align="center" gutterBottom>
        🔓 DecryptAI - Room {gameState.room_code}
      </Typography>
      
      <Box sx={{ mb: 3, textAlign: 'center' }}>
        <Typography variant="h6">
          Round {gameState.current_round} - {gameState.current_team.toUpperCase()} Team's Turn
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Phase: {gameState.phase.replace('_', ' ').toUpperCase()}
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          {renderTeamCard('red')}
        </Grid>
        <Grid item xs={12} md={6}>
          {renderTeamCard('blue')}
        </Grid>
      </Grid>

      {gameState.phase === 'setup' && (
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button 
            variant="contained" 
            size="large"
            onClick={startGame}
            disabled={!canStartGame}
          >
            {canStartGame ? 'Start Game!' : 'Waiting for both teams to set up...'}
          </Button>
        </Box>
      )}

      {gameState.phase === 'clue_giving' && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6">
              Team {gameState.current_team.toUpperCase()} is giving clues...
            </Typography>
            {gameState.current_code && (() => {
              const myTeam = gameState.teams.red.players.includes(playerName) ? 'red' : 'blue';
              const isMyTeamGiving = myTeam === gameState.current_team;
              
              return isMyTeamGiving ? (
                <Typography variant="body2">
                  Your code: {gameState.current_code.join('-')}
                </Typography>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Waiting for clues...
                </Typography>
              );
            })()}
          </CardContent>
        </Card>
      )}

      {gameState.phase === 'guessing' && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6">Guessing Phase</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Clues: <strong>{gameState.current_clues.join(' | ')}</strong>
            </Typography>
            
            {(() => {
              const myTeam = gameState.teams.red.players.includes(playerName) ? 'red' : 'blue';
              const hasGuessed = gameState.team_guesses[myTeam];
              
              return (
                <Box>
                  {hasGuessed ? (
                    <Typography variant="body2" color="text.secondary">
                      Your team has submitted a guess: {hasGuessed.join('-')}
                    </Typography>
                  ) : (
                    <Box>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        Make your guess for the 3-digit code:
                      </Typography>
                      <Grid container spacing={2} sx={{ mb: 2 }}>
                        {[0, 1, 2].map((index) => (
                          <Grid item key={index}>
                            <FormControl size="small" sx={{ minWidth: 80 }}>
                              <InputLabel>Pos {index + 1}</InputLabel>
                              <Select
                                value={currentGuess[index]}
                                onChange={(e) => {
                                  const newGuess = [...currentGuess];
                                  newGuess[index] = e.target.value as number;
                                  setCurrentGuess(newGuess);
                                }}
                                label={`Pos ${index + 1}`}
                              >
                                <MenuItem value={1}>1</MenuItem>
                                <MenuItem value={2}>2</MenuItem>
                                <MenuItem value={3}>3</MenuItem>
                                <MenuItem value={4}>4</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                        ))}
                      </Grid>
                      <Button 
                        variant="contained" 
                        onClick={submitGuess}
                        size="large"
                      >
                        Submit Guess: {currentGuess.join('-')}
                      </Button>
                    </Box>
                  )}
                  
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      Waiting for {Object.keys(gameState.team_guesses).length}/2 teams to guess...
                    </Typography>
                  </Box>
                </Box>
              );
            })()}
          </CardContent>
        </Card>
      )}

      {gameState.winner && (
        <Alert severity="success" sx={{ mt: 3 }}>
          🎉 Team {gameState.winner.toUpperCase()} wins!
        </Alert>
      )}

      {/* Game History */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Game History
          </Typography>
          {(() => {
            const history = gameState.round_history || [];
            
            return history.length > 0 ? (
              <Box>
                {history.map((round, index) => (
                  <Box key={index} sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, mb: 1 }}>
                    <Typography variant="body2" fontWeight="bold">
                      Round {round.round} - Team {round.team.toUpperCase()}
                    </Typography>
                    <Typography variant="body2">
                      Clues: {round.clues.join(' | ')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Code: {round.code.join('-')} | 
                      Red guess: {round.guesses.red?.join('-') || 'None'} | 
                      Blue guess: {round.guesses.blue?.join('-') || 'None'}
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No history yet. Start the game to see round history here.
              </Typography>
            );
          })()}
        </CardContent>
      </Card>
    </Container>
  );
};

export default App;