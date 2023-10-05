import React, {useState, useEffect} from 'react';
import DraggableSemiCircle from './Semicircle';


const GameGuess = ({ myName, game_idx, guesses, rounds, updateGuess, submitGuess }) => {
  const [round_number, player_number, currPlayer] = game_idx;
  const currentRound = rounds[round_number]['players'][currPlayer];

  const allGuesses = Object.values(guesses);
  const averageGuess = allGuesses.reduce((a, b) => a + b, 0) / allGuesses.length;

  const [localGuess, setLocalGuess] = useState(0.5);
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    const sendData = setTimeout(() => {
        if (!isSubmitted && (myName in guesses)) {
         updateGuess(localGuess);
        }
    }, 250)

    return () => clearTimeout(sendData)
  }, [localGuess, isSubmitted, updateGuess]);

  useEffect(() => {
    setLocalGuess(0.5)
    setIsSubmitted(false)
  }, [currPlayer])

  return (
    <div>
      <h2>Round {round_number + 1}</h2>
      <p>{currentRound.scale.join(' <---> ')}</p>
      <p>Clue: {currentRound.clue}</p>

      <div>
        {myName in guesses ? (
          isSubmitted ? (
            <p>Your guess is locked: {guesses[myName]}</p>
          ) : (
            <>
              <DraggableSemiCircle value={localGuess} onChange={(e) => setLocalGuess(e)} locked={isSubmitted} />
              <button onClick={() => { submitGuess(localGuess); setIsSubmitted(true); }}>
                Submit
              </button>
            </>
          )
        ) : (
          <p>This is your clue, you cannot submit</p>
        )}
      </div>

      <div>
        <h3>All Guesses</h3>
        {Object.entries(guesses).map(([name, guess], index) => (
          <p key={index}>
            {name}: {guess}
          </p>
        ))}
      </div>

      <div>
        <h3>Average Guess: {averageGuess.toFixed(3)}</h3>
      </div>
    </div>
  );
};

export default GameGuess;
