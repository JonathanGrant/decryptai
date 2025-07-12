from openai import OpenAI
import json
import os
import structlog
import retrying

logger = structlog.getLogger()

# Initialize OpenAI client
try:
    api_key = os.environ.get("OPENAI_KEY", None)
    if not api_key:
        try:
            api_key = open('/root/decryptai/.openai_key').read().strip()
        except:
            try:
                api_key = open('/Users/jong/.openai_key').read().strip()
            except:
                api_key = open('/app/.openai_key').read().strip()
    client = OpenAI(api_key=api_key)
except Exception as e:
    logger.error(f"Could not initialize OpenAI client: {e}")
    client = None

DEFAULT_MODEL = 'gpt-4o-mini'

class DecryptoAI:
    def __init__(self, team_color, difficulty='normal'):
        self.team_color = team_color
        self.difficulty = difficulty
        self.personality = self.get_personality()
    
    def get_personality(self):
        personalities = [
            "clever and creative wordsmith",
            "strategic puzzle solver", 
            "witty and playful communicator",
            "methodical pattern analyzer",
            "intuitive word association expert"
        ]
        import random
        return random.choice(personalities)

    @retrying.retry(stop_max_attempt_number=3, wait_fixed=2000)
    def generate_clues(self, code_words, code_sequence):
        """
        Generate clues for a 3-digit code sequence
        
        Args:
            code_words: List of 4 code words for the team
            code_sequence: List of 3 numbers (1-4) indicating which words to give clues for
        
        Returns:
            List of 3 clues corresponding to the code sequence
        """
        if not client:
            return ["connection", "mystery", "puzzle"]  # Fallback
            
        # Create the prompt
        prompt = f"""You are a {self.personality} playing Decrypto. You need to give clues for a secret code.

Your team's 4 code words are:
1. {code_words[0]}
2. {code_words[1]} 
3. {code_words[2]}
4. {code_words[3]}

You need to give clues for the sequence: {code_sequence}
This means give a clue for word #{code_sequence[0]}, then word #{code_sequence[1]}, then word #{code_sequence[2]}.

RULES:
- Give exactly 3 clues, one for each position in the sequence
- Clues should help your teammates guess the correct numbers
- Clues cannot contain the actual code words
- Clues should be 1-3 words each
- Make clues helpful but not too obvious (opposing team is listening!)
- Be creative but clear

Respond with a JSON array of exactly 3 clues:
["clue1", "clue2", "clue3"]"""

        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            clues_text = response.choices[0].message.content.strip()
            clues = json.loads(clues_text)
            
            if isinstance(clues, list) and len(clues) == 3:
                logger.info(f"AI generated clues for {code_sequence}: {clues}")
                return clues
            else:
                raise ValueError("Invalid clues format")
                
        except Exception as e:
            logger.error(f"Error generating clues: {e}")
            # Fallback clues
            fallback_clues = []
            for pos in code_sequence:
                word = code_words[pos - 1]
                fallback_clues.append(f"related-to-{word[:3]}")
            return fallback_clues

    @retrying.retry(stop_max_attempt_number=3, wait_fixed=2000)
    def guess_code(self, clues, opponent_code_words=None, round_history=None):
        """
        Guess a 3-digit code based on clues
        
        Args:
            clues: List of 3 clues
            opponent_code_words: List of opponent's code words (if known)
            round_history: Previous rounds for pattern recognition
        
        Returns:
            List of 3 numbers (1-4) representing the guessed code
        """
        if not client:
            import random
            return random.choices(range(1, 5), k=3)  # Fallback
            
        # Build context from round history
        history_context = ""
        if round_history:
            history_context = "\nPrevious rounds:\n"
            for round_data in round_history[-3:]:  # Last 3 rounds
                history_context += f"Clues: {round_data['clues']} → Code: {round_data['code']}\n"
        
        # Build opponent words context
        words_context = ""
        if opponent_code_words:
            words_context = f"\nOpponent's code words:\n"
            for i, word in enumerate(opponent_code_words, 1):
                words_context += f"{i}. {word}\n"
        
        prompt = f"""You are a {self.personality} playing Decrypto. You need to guess a 3-digit code based on clues.

The clues given were: {clues}

{words_context}
{history_context}

You need to guess which 3 code words (numbered 1-4) these clues refer to, in order.

STRATEGY:
- Analyze each clue and think what code word it might refer to
- Consider the patterns from previous rounds
- Each number in your guess should be 1, 2, 3, or 4
- The same number can appear multiple times in a code

Think through each clue carefully and respond with a JSON array of exactly 3 numbers:
[number1, number2, number3]

Example: [2, 1, 4]"""

        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            guess_text = response.choices[0].message.content.strip()
            guess = json.loads(guess_text)
            
            if (isinstance(guess, list) and len(guess) == 3 and 
                all(isinstance(x, int) and 1 <= x <= 4 for x in guess)):
                logger.info(f"AI guessed code: {guess} for clues: {clues}")
                return guess
            else:
                raise ValueError("Invalid guess format")
                
        except Exception as e:
            logger.error(f"Error guessing code: {e}")
            # Fallback random guess
            import random
            return random.choices(range(1, 5), k=3)