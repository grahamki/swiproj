import React, { useEffect, useState } from 'react';
import apiService from '../services/api';

function WordFamilyGame({ word, onExit }) {
  const [root, setRoot] = useState('');
  const [words, setWords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [guess, setGuess] = useState('');
  const [guessedWords, setGuessedWords] = useState([]);
  const [feedback, setFeedback] = useState('');
  const [score, setScore] = useState(0);

  useEffect(() => {
    async function fetchGameData() {
      setLoading(true);
      setError(null);
      try {
        const rootRes = await apiService.makeRequest('/extract-root', {
          method: 'POST',
          body: JSON.stringify({ word }),
        });
        setRoot(rootRes.root);
        const familyRes = await apiService.makeRequest('/word-family', {
          method: 'POST',
          body: JSON.stringify({ root: rootRes.root }),
        });
        setWords(familyRes.words || []);
      } catch (err) {
        setError('Failed to load game data.');
      } finally {
        setLoading(false);
      }
    }
    fetchGameData();
  }, [word]);

  const handleGuess = (e) => {
    e.preventDefault();
    const cleanGuess = guess.trim().toLowerCase();
    if (!cleanGuess) return;
    if (guessedWords.includes(cleanGuess)) {
      setFeedback('You already guessed that word!');
      setGuess('');
      return;
    }
    if (words.includes(cleanGuess)) {
      setGuessedWords([...guessedWords, cleanGuess]);
      setScore(score + 1);
      setFeedback('✅ Correct!');
    } else {
      setFeedback('❌ Not in the word family. Try again!');
    }
    setGuess('');
  };

  if (loading) return <div className="game-screen"><h2>Word Family Game</h2><p>Loading...</p></div>;
  if (error) return <div className="game-screen"><h2>Word Family Game</h2><p style={{color:'#dc2626'}}>{error}</p><button className="mode-button" onClick={onExit}>Back</button></div>;

  return (
    <div className="game-screen" style={{ maxWidth: 600, margin: '40px auto', background: 'white', borderRadius: 16, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', padding: 32 }}>
      <h2>Word Family Game</h2>
      <p>Root: <span style={{ color: '#10b981', fontWeight: 600 }}>{root}</span></p>
      <p>Guess words that use this root! ({score} / {words.length} found)</p>
      <form onSubmit={handleGuess} style={{ marginBottom: 12 }}>
        <input
          type="text"
          value={guess}
          onChange={e => setGuess(e.target.value)}
          placeholder="Type a word..."
          style={{ padding: 8, borderRadius: 6, border: '1px solid #e2e8f0', marginRight: 8 }}
        />
        <button type="submit" className="mode-button">Guess</button>
      </form>
      {feedback && <div style={{ marginBottom: 8, color: feedback.startsWith('✅') ? '#10b981' : '#dc2626' }}>{feedback}</div>}
      <div style={{ marginBottom: 8 }}>
        <strong>Guessed:</strong> {guessedWords.length === 0 ? 'None yet' : guessedWords.join(', ')}
      </div>
      <div style={{ marginBottom: 8 }}>
        <strong>Word Family:</strong> {words.map((w, i) => (
          <span key={w} style={{
            marginRight: 6,
            color: guessedWords.includes(w) ? '#10b981' : '#64748b',
            textDecoration: guessedWords.includes(w) ? 'none' : 'line-through',
            fontWeight: guessedWords.includes(w) ? 600 : 400
          }}>{w}</span>
        ))}
      </div>
      {score === words.length && <div style={{ color: '#10b981', fontWeight: 600 }}>🎉 You found all the words!</div>}
      <div style={{ marginTop: 24 }}>
        <button className="mode-button" onClick={onExit}>Back</button>
      </div>
    </div>
  );
}

export default WordFamilyGame; 