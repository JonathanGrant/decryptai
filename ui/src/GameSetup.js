import React, { useState } from 'react';
import Button from '@mui/material/Button';
import DraggableSemiCircle from './Semicircle';


const GameSetup = ({ playerName, rounds, submit }) => {
  const [clues, setClues] = useState(Array(rounds.length).fill(null));

  const handleClueChange = (roundIndex, clue) => {
    const newClues = [...clues];
    newClues[roundIndex] = clue;
    setClues(newClues);
  };

  return (
    <div>
      <h1>Welcome, {playerName}</h1>

      {rounds.map((round, index) => {
        const playerData = round.players[playerName];
        if (!playerData) {
          return <div key={index}>No data for this round.</div>;
        }

        const { point, scale } = playerData;
        return (
          <div key={index}>
            <h2>Round {index + 1}</h2>
            <DraggableSemiCircle value={point} locked />
            <p>Scale: {scale.join(' <---> ')}</p>
            <input
              type="text"
              placeholder="Enter your clue"
              value={clues[index] || ''}
              onChange={(e) => handleClueChange(index, e.target.value)}
            />
          </div>
        );
      })}

      <Button variant="contained" color="primary" onClick={() => submit(clues)}>Submit</Button>
    </div>
  );
};

export default GameSetup;
