import React, { useState, useRef, useEffect } from 'react';
import './MorphemeHighlighter.css';
import apiService from '../services/api';

const MorphemeHighlighter = () => {
  const [text, setText] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedWord, setSelectedWord] = useState('');
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const [showPopup, setShowPopup] = useState(false);
  const [isEditMode, setIsEditMode] = useState(true);
  const textAreaRef = useRef(null);

  const handleTextChange = (e) => {
    setText(e.target.value);
    setAnalysis(null);
    setError(null);
  };

  const handleWordClick = async (word, event) => {
    if (!word || word.trim() === '') return;

    const rect = event.target.getBoundingClientRect();
    setPopupPosition({
      x: rect.left + rect.width / 2,
      y: rect.bottom + 10,
    });

    setSelectedWord(word);
    setShowPopup(true);
    setLoading(true);
    setError(null);

    try {
      const result = await apiService.analyzeMorpheme(word);
      setAnalysis(result);
    } catch (err) {
      console.error('Failed to analyze word:', err);
      setError('Failed to analyze word. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClickOutside = (event) => {
    if (textAreaRef.current && !textAreaRef.current.contains(event.target)) {
      setShowPopup(false);
    }
  };

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const renderTextWithClickableWords = () => {
    if (!text) return null;

    const words = text.split(/(\s+)/);
    return words.map((word, index) => {
      if (word.trim() === '') {
        return <span key={index}>{word}</span>;
      }

      return (
        <span
          key={index}
          className="clickable-word"
          onClick={(e) => handleWordClick(word, e)}
          title={`Click to analyze: ${word}`}
        >
          {word}
        </span>
      );
    });
  };

  return (
    <div className="container">
      <div className="header">
        <h1>📚 Morpheme Highlighter</h1>
        <p>Highlight any word or section to break it down or summarize.</p>
      </div>

      <div className="content">
        <div className="text-input-section">
          <label htmlFor="text-input" className="input-label">
            Paste or type your text here:
          </label>
          <div className="text-display" ref={textAreaRef}>
            {!isEditMode && text ? (
              <div className="clickable-text">{renderTextWithClickableWords()}</div>
            ) : (
              <textarea
                id="text-input"
                className="text-input"
                placeholder="Paste or type your text here...Try highlighting a word to see its morphemes."
                value={text}
                onChange={handleTextChange}
              />
            )}
          </div>

          <div className="instructions">
            💡 Highlight a word to see its morphemes.
          </div>

          <div className="button-group">
            {text && (
              <>
                <button
                  className="mode-button"
                  onClick={() => setIsEditMode(!isEditMode)}
                >
                  {isEditMode ? '📖 Read!' : '✏️ Edit Text'}
                </button>
                <button
                  className="clear-button"
                  onClick={() => {
                    setText('');
                    setAnalysis(null);
                    setError(null);
                    setShowPopup(false);
                    setIsEditMode(true);
                  }}
                >
                  Clear Text
                </button>
              </>
            )}
          </div>
        </div>

        {showPopup && (
          <div
            className="analysis-popup"
            style={{ left: `${popupPosition.x}px`, top: `${popupPosition.y}px` }}
          >
            <div className="popup-header">
              <h3>Analysis: "{selectedWord}"</h3>
              <button className="close-button" onClick={() => setShowPopup(false)}>
                ×
              </button>
            </div>
            <div className="analysis-content">
              {loading && (
                <div className="loading">
                  <div className="spinner"></div>
                  <p>Analyzing word structure...</p>
                </div>
              )}
              {error && (
                <div className="error">
                  <p>{error}</p>
                </div>
              )}
              {analysis && !loading && (
                <div className="analysis-content">
                  <div className="morpheme-breakdown">
                    <h4>📚 Morpheme Breakdown:</h4>
                    <div className="morphemes">
                      {Array.isArray(analysis.morphemes) && analysis.morphemes.length > 0
                        ? analysis.morphemes.map((m, idx) => (
                            <div key={idx} className={`morpheme ${m.type || ''}`}>
                              <span className="part">{m.morpheme}</span>
                              {m.type && <span className="type">({m.type})</span>}
                              {m.meaning && <span className="meaning">{m.meaning}</span>}
                            </div>
                          ))
                        : (
                            <>
                              {analysis.prefix && (
                                <div className="morpheme prefix">
                                  <span className="part">{analysis.prefix.part}</span>
                                  <span className="meaning">{analysis.prefix.meaning}</span>
                                </div>
                              )}
                              {analysis.root && (
                                <div className="morpheme root">
                                  <span className="part">{analysis.root.part}</span>
                                  <span className="meaning">{analysis.root.meaning}</span>
                                </div>
                              )}
                              {analysis.suffix1 && (
                                <div className="morpheme suffix">
                                  <span className="part">{analysis.suffix1.part}</span>
                                  <span className="meaning">{analysis.suffix1.meaning}</span>
                                </div>
                              )}
                              {analysis.suffix2 && (
                                <div className="morpheme suffix">
                                  <span className="part">{analysis.suffix2.part}</span>
                                  <span className="meaning">{analysis.suffix2.meaning}</span>
                                </div>
                              )}
                            </>
                          )}
                    </div>
                  </div>

                  {analysis.meaning && (
                    <div className="overall-meaning">
                      <h4>🌟 Overall Meaning:</h4>
                      <p>{analysis.meaning}</p>
                    </div>
                  )}


                  {analysis.morphological_relatives && analysis.morphological_relatives.length > 0 && (
                    <div className="related-section">
                      <h4>⏳ Historical Origin:</h4>
                      <div className="historical-origin">
                        <p>{analysis.historical_origin}</p>
                      </div>
                      <h4>🧬 Morphological Relatives - Same Root:</h4>
                      <div className="related-word-list">
                        {analysis.morphological_relatives.map((word, idx) => (
                          <span key={idx} className="related-word">
                            {word}{idx < analysis.morphological_relatives.length - 1 ? ',' : ''}
                          </span>
                        ))}
                      </div>
                      <h4>📜 Etymological Relatives - Same:</h4>
                      <div className="related-word-list">
                        {analysis.etymological_relatives.map((word, idx) => (
                          <span key={idx} className="related-word">
                            {word}{idx < analysis.etymological_relatives.length - 1 ? ',' : ''}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MorphemeHighlighter;