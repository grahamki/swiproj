import React, { useState, useRef, useEffect, useMemo } from 'react';
import './MorphemeHighlighter.css';
import apiService from '../services/api';

// Add simple affix lists for hint dots
const KNOWN_PREFIXES = ['un','re','pre','mis','dis','non','sub','trans','inter','over','under','super','anti','auto','bi','co','contra','de','en','em','ex','fore','im','in','pro'];
const KNOWN_SUFFIXES = ['able','ible','tion','ment','ness','less','ful','ize','ing','ed','ly','ous','ive','ity','al','er','est','ion','ation','s','es'];

// naive tokenizer that preserves whitespace and assigns word indices
function tokenize(text) {
  const parts = text.split(/(\s+)/);
  const tokens = [];
  let widx = 0;
  for (const p of parts) {
    const isWord = /^[A-Za-z'-]+$/.test(p);
    tokens.push({ text: p, isWord, idx: isWord ? widx++ : null });
  }
  return tokens;
}

// segmenter: left-to-right best-effort alignment; fallback = whole word as root
function segmentWord(word, morphemes) {
  if (!Array.isArray(morphemes) || morphemes.length === 0) {
    return [{ text: word, role: 'root', meaning: 'root/base' }];
  }
  const segs = [];
  let cursor = 0;
  const lower = word.toLowerCase();
  for (const m of morphemes) {
    const piece = String(m?.morpheme || '');
    if (!piece) continue;
    const at = lower.indexOf(piece.toLowerCase(), cursor);
    if (at === -1) continue;
    if (at > cursor) segs.push({ text: word.slice(cursor, at), role: 'root', meaning: '' });
    segs.push({ text: word.slice(at, at + piece.length), role: m?.type || 'root', meaning: m?.meaning || '' });
    cursor = at + piece.length;
  }
  if (cursor < word.length) segs.push({ text: word.slice(cursor), role: 'root', meaning: '' });
  return segs.length ? segs : [{ text: word, role: 'root', meaning: 'root/base' }];
}

const MorphemeHighlighter = () => {
  const [text, setText] = useState('');
  // cache: Map<string, MorphemeAnalysis>
  const [analysisCache, setAnalysisCache] = useState(() => new Map());
  // overlays: Record<number, Seg[]>
  const [overlays, setOverlays] = useState({});
  const [analysisData, setAnalysisData] = useState({
    morphemes: null,
    meaning: null,
    etymology: null,
    graphemes: null,
    relatives: null
  });
  const [loadingTabs, setLoadingTabs] = useState({
    morphemes: false,
    meaning: false, 
    etymology: false,
    graphemes: false,
    relatives: false
  });
  // Remove unused loading state
  // const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedWord, setSelectedWord] = useState('');
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const [showPopup, setShowPopup] = useState(false);
  const [isEditMode, setIsEditMode] = useState(true);
  const [activeView, setActiveView] = useState('morphemes');
  const textAreaRef = useRef(null);
  const popupRef = useRef(null);

  // Dots toggle (persist)
  const [showHintDots, setShowHintDots] = useState(() => {
    try { const v = localStorage.getItem('mh.hintDots'); return v === null ? true : JSON.parse(v); } catch { return true; }
  });
  useEffect(() => { try { localStorage.setItem('mh.hintDots', JSON.stringify(showHintDots)); } catch {} }, [showHintDots]);

  // Finish Reading / Practice tray
  const [clickedWords, setClickedWords] = useState(() => {
    try { const v = JSON.parse(localStorage.getItem('mh.clickedWords')); return Array.isArray(v) ? v : []; } catch { return []; }
  });
  const [showPractice, setShowPractice] = useState(false);
  useEffect(() => { try { localStorage.setItem('mh.clickedWords', JSON.stringify(clickedWords)); } catch {} }, [clickedWords]);

  // Left side panel instead of centered popup
  const [leftOpen, setLeftOpen] = useState(false);

  const handleTextChange = (e) => {
    setText(e.target.value);
    setOverlays({}); // reset inline overlays on text change
    setAnalysisData({
      morphemes: null,
      meaning: null,
      etymology: null,
      graphemes: null,
      relatives: null
    });
    setError(null);
  };

  // Heuristic: likely complex -> show hint dots
  const hasKnownAffix = (w) => {
    const lc = String(w || '').toLowerCase();
    return KNOWN_PREFIXES.some(p => lc.startsWith(p)) || KNOWN_SUFFIXES.some(s => lc.endsWith(s));
  };
  const isComplex = (w) => {
    const s = String(w || '');
    if (s.length < 7) return false;
    const cached = analysisCache.get(s.toLowerCase());
    const hasMultiFromCache = Array.isArray(cached?.morphemes) && cached.morphemes.length >= 2;
    return hasKnownAffix(s) || hasMultiFromCache;
  };

  // Save clicked word (dedupe, preserve casing)
  const addClickedWord = (w) => {
    const s = String(w || '').trim();
    if (!s) return;
    setClickedWords(prev => prev.some(p => p.toLowerCase() === s.toLowerCase()) ? prev : [...prev, s]);
  };

  // Use side panel: open panel and load all tabs
  const handleWordClick = async (word, event) => {
    if (!word || word.trim() === '') return;
    addClickedWord(word);
    setSelectedWord(word);
    setActiveView('morphemes');
    setLeftOpen(true);

    // Reset data + set all tabs loading
    setAnalysisData({ morphemes: null, meaning: null, etymology: null, graphemes: null, relatives: null });
    setLoadingTabs({ morphemes: true, meaning: true, etymology: true, graphemes: true, relatives: true });
    setError(null);

    try {
      const tabTypes = ['morphemes', 'meaning', 'etymology', 'graphemes', 'relatives'];
      // Fail fast: let any request rejection bubble up to catch
      const results = await Promise.all(
        tabTypes.map(type =>
          apiService.analyzeMorpheme(word, type).then(result => ({ type, result }))
        )
      );

      const newData = { ...analysisData };
      results.forEach(({ type, result }) => {
        if (type === 'morphemes') {
          newData[type] = result;
        } else if (type === 'meaning') {
          newData[type] = result;
        } else if (type === 'etymology') {
          // Keep minimal shaping, no heuristic text
          newData[type] = {
            historical_origin: result.historical_origin || "",
            morphological_relatives: result.morphological_relatives || [],
            etymological_relatives: result.etymological_relatives || [],
            notAvailable: false
          };
        } else if (type === 'graphemes') {
          newData[type] = { graphemes: result.graphemes || [] };
        } else if (type === 'relatives') {
          newData[type] = {
            morphological_relatives: result.morphological_relatives || [],
            etymological_relatives: result.etymological_relatives || []
          };
        }
      });

      setAnalysisData(newData);
    } catch (err) {
      console.error('Analyze error:', err);
      // No fallback content; show a single error message
      setError('ERROR TRY AGAIN');
      setAnalysisData({ morphemes: null, meaning: null, etymology: null, graphemes: null, relatives: null });
    } finally {
      setLoadingTabs({ morphemes: false, meaning: false, etymology: false, graphemes: false, relatives: false });
    }
  };

  const handleClickOutside = (event) => {
    // Check if click is outside both the textAreaRef and popupRef
    if ((textAreaRef.current && !textAreaRef.current.contains(event.target)) && 
        (!document.querySelector('.mh-left-panel') || !document.querySelector('.mh-left-panel').contains(event.target))) {
      setLeftOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Log which backend is reachable (proxy /api or :5001) to verify connectivity
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/api/health');
        if (r.ok) {
          console.log('API reachable at /api (dev proxy).');
          return;
        }
      } catch {}
      try {
        const host = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : 'localhost';
        const r2 = await fetch(`http://${host}:5001/api/health`);
        if (r2.ok) {
          console.log(`API reachable at http://${host}:5001/api.`);
        } else {
          console.warn('API health on :5001 failed.');
        }
      } catch (e) {
        console.warn('API not reachable on /api or :5001. Check server or proxy.', e);
      }
    })();
  }, []);

  // Update the handleTabChange function to not make API calls since data is already loaded
  const handleTabChange = (tabName, e) => {
    // Stop event propagation to prevent handleClickOutside from being triggered
    if (e) e.stopPropagation();
    setActiveView(tabName);
  };

  // INLINE overlay click handler (no popup, cached)
  const handleWordClickInline = async (word, idx) => {
    if (!word || word.trim() === '') return;
    // If this specific word index already has an overlay, don't re-fetch or change
    if (overlays[idx]) return;

    const key = word.toLowerCase();
    let data = analysisCache.get(key);
    try {
      if (!data) {
        data = await apiService.analyzeMorpheme(word, 'morphemes');
        const next = new Map(analysisCache);
        next.set(key, data);
        setAnalysisCache(next);
      }
      const segs = segmentWord(word, data?.morphemes || []);
      // If unsegmentable, leave as-is
      const unchanged = segs.length === 1 && segs[0].text === word && segs[0].role === 'root' && !data?.morphemes?.length;
      if (unchanged) return;

      setOverlays(prev => ({ ...prev, [idx]: segs }));
    } catch (err) {
      console.error('Inline analyze error:', err);
    }
  };

  const tokens = useMemo(() => tokenize(text), [text]);

  const renderTextWithClickableWords = () => {
    if (!text) return null;
    return tokens.map((t, i) => {
      if (!t.isWord) return <span key={i}>{t.text}</span>;
      const segs = overlays[t.idx];
      const dotted = showHintDots && isComplex(t.text);
      return (
        <span
          key={i}
          data-idx={t.idx}
          className={`clickable-word mh-word ${dotted ? 'has-morph' : ''}`}
          // Call both: fast inline segmentation + open side panel + load tabs
          onClick={(e) => { handleWordClickInline(t.text, t.idx); handleWordClick(t.text, e); }}
          role="button"
          tabIndex={0}
          aria-label={dotted ? 'Likely morphologically complex' : undefined}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleWordClickInline(t.text, t.idx);
              handleWordClick(t.text, e);
            }
          }}
          title={`Click to analyze: ${t.text}`}
        >
          {segs
            ? segs.map((s, k) => (
                <span key={k} className={`seg ${s.role}`} title={s.meaning || s.role}>
                  {s.text}
                </span>
              ))
            : t.text}
        </span>
      );
    });
  };

  // Practice tray component
  const PracticePanel = ({ words, onClose }) => (
    <div className="practice-panel" onMouseDown={(e) => e.stopPropagation()}>
      <div className="practice-header">
        <span>Word Bank</span>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      <div className="practice-body">
        {(!words || words.length === 0) ? (
          <p className="practice-empty">No saved words yet.</p>
        ) : (
          <ul style={{ paddingLeft: 16, margin: '8px 0' }}>
            {words.map((w, i) => (<li key={`${w}-${i}`} style={{ marginBottom: 6 }}>{w}</li>))}
          </ul>
        )}
      </div>
    </div>
  );

  return (
    // Wrap with a shell that allows left panel to slide in
    <div className="mh-shell" style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
      {/* LEFT SIDE PANEL (replaces centered popup) */}
      <aside
        className={`mh-left-panel ${leftOpen ? 'open' : ''}`}
        aria-labelledby="mh-panel-title"
        role="dialog"
        aria-modal="false"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: 380,
          height: '100vh',
          background: '#fff',
          borderRight: '1px solid #e5e7eb',
          boxShadow: '2px 0 20px rgba(0,0,0,.08)',
          transform: leftOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform .2s ease-out',
          zIndex: 50
        }}
      >
        <div className="mh-panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '.75rem 1rem', borderBottom: '1px solid #f0f0f0', background: '#10b981', color: '#fff' }}>
          <h3 id="mh-panel-title" style={{ margin: 0 }}>Analysis: "{selectedWord || ''}"</h3>
          <button className="mh-panel-close" onClick={() => setLeftOpen(false)} aria-label="Close panel" style={{ fontSize: '1.25rem', lineHeight: 1, background: 'none', border: 'none', cursor: 'pointer', color: '#fff' }}>×</button>
        </div>

        {/* Tabs */}
        <div className="view-selector" style={{ display: 'flex', gap: 8, padding: '8px 10px', borderBottom: '1px solid #eef2f7' }}>
          <button className={`view-tab ${activeView === 'morphemes' ? 'active' : ''}`} onClick={(e) => handleTabChange('morphemes', e)}>📚 Morphemes</button>
          <button className={`view-tab ${activeView === 'meaning' ? 'active' : ''}`} onClick={(e) => handleTabChange('meaning', e)}>🌟 Meaning</button>
          <button className={`view-tab ${activeView === 'etymology' ? 'active' : ''}`} onClick={(e) => handleTabChange('etymology', e)}>📜 Etymology</button>
          <button className={`view-tab ${activeView === 'graphemes' ? 'active' : ''}`} onClick={(e) => handleTabChange('graphemes', e)}>📝 Graphemes</button>
          <button className={`view-tab ${activeView === 'relatives' ? 'active' : ''}`} onClick={(e) => handleTabChange('relatives', e)}>👪 Relatives</button>
        </div>

        {/* Panel Body (reuse your existing tab render blocks) */}
        <div className="mh-panel-body" style={{ padding: '.75rem 1rem', overflow: 'auto', height: 'calc(100vh - 92px)' }}>
          {/* ...existing analysis-content/tab rendering you already have, but without the centered popup wrapper... */}
          <div className="analysis-content">
            {loadingTabs[activeView] && (
              <div className="loading">
                <div className="spinner"></div>
                <p>Analyzing {activeView}...</p>
              </div>
            )}
            {error && (
              <div className="error"><p>{error}</p></div>
            )}
            {!loadingTabs[activeView] && analysisData[activeView] && (
              <>
                {activeView === 'morphemes' && (
                  <div className="morpheme-breakdown">
                    <h4>📚 Morpheme Breakdown:</h4>
                    <div className="morphemes">
                      {analysisData.morphemes?.morphemes && Array.isArray(analysisData.morphemes.morphemes) ? 
                        // If morphemes is an array inside the response object
                        analysisData.morphemes.morphemes.map((m, idx) => (
                          <div key={idx} className={`morpheme ${m.type || ''}`}>
                            <span className="part">{m.morpheme}</span>
                            {m.type && <span className="type">({m.type})</span>}
                            {m.meaning && <span className="meaning">{m.meaning}</span>}
                          </div>
                        ))
                        : analysisData.morphemes ? 
                          // If direct access to morphemes as an object with prefix/root/suffix
                          <>
                            {analysisData.morphemes.prefix && (
                              <div className="morpheme prefix">
                                <span className="part">{analysisData.morphemes.prefix.part}</span>
                                <span className="type">(prefix)</span>
                                <span className="meaning">{analysisData.morphemes.prefix.meaning}</span>
                              </div>
                            )}
                            {analysisData.morphemes.root && (
                              <div className="morpheme root">
                                <span className="part">{analysisData.morphemes.root.part}</span>
                                <span className="type">(root)</span>
                                <span className="meaning">{analysisData.morphemes.root.meaning}</span>
                              </div>
                            )}
                            {analysisData.morphemes.suffix && (
                              <div className="morpheme suffix">
                                <span className="part">{analysisData.morphemes.suffix.part}</span>
                                <span className="type">(suffix)</span>
                                <span className="meaning">{analysisData.morphemes.suffix.meaning}</span>
                              </div>
                            )}
                          </>
                          : <p>No morpheme data available</p>
                      }
                    </div>
                  </div>
                )}
                
                {activeView === 'meaning' && (
                  <div className="overall-meaning">
                    <h4>🌟 Overall Meaning:</h4>
                    {analysisData.meaning?.meaning?.meaning || analysisData.meaning?.meaning ? (
                      <p>{analysisData.meaning?.meaning?.meaning || analysisData.meaning?.meaning}</p>
                    ) : (
                      <p>No meaning data available for this word.</p>
                    )}
                  </div>
                )}
                
                {activeView === 'etymology' && (
                  <div className="related-section">
                    {/* Etymology content */}
                    {analysisData.etymology?.notAvailable ? (
                      <div className="etymology-not-available">
                        <h4>📜 Etymology Information</h4>
                        <div className="historical-origin not-available-message">
                          <p>{analysisData.etymology.historical_origin}</p>
                        </div>
                      </div>
                    ) : (
                      <>
                        <h4>⏳ Historical Origin:</h4>
                        <div className="historical-origin">
                          {analysisData.etymology?.historical_origin ? (
                            <p>{analysisData.etymology.historical_origin}</p>
                          ) : (
                            <p>No historical origin data available for this word.</p>
                          )}
                        </div>
                        
                        {/* Only show relatives sections if we have data AND notAvailable is NOT true */}
                        {analysisData.etymology?.morphological_relatives?.length > 0 && (
                          <>
                            <h4>🧬 Morphological Relatives:</h4>
                            <div className="related-word-list">
                              {analysisData.etymology.morphological_relatives.map((word, idx) => (
                                <span 
                                  key={idx} 
                                  className="related-word clickable-word"
                                  onClick={(e) => handleWordClick(word, e)}
                                >
                                  {word}{idx < analysisData.etymology.morphological_relatives.length - 1 ? ', ' : ''}
                                </span>
                              ))}
                            </div>
                          </>
                        )}
                        
                        {analysisData.etymology?.etymological_relatives?.length > 0 && (
                          <>
                            <h4>📜 Etymological Relatives:</h4>
                            <div className="related-word-list">
                              {analysisData.etymology.etymological_relatives.map((word, idx) => (
                                <span 
                                  key={idx} 
                                  className="related-word clickable-word"
                                  onClick={(e) => handleWordClick(word, e)}
                                >
                                  {word}{idx < analysisData.etymology.etymological_relatives.length - 1 ? ', ' : ''}
                                </span>
                              ))}
                            </div>
                          </>
                        )}
                      </>
                    )}
                  </div>
                )}
                
                {activeView === 'graphemes' && (
                  <div className="graphemes-section">
                    <h4>📝 Grapheme Breakdown:</h4>
                    {analysisData.graphemes?.graphemes?.length > 0 ? (
                      <div className="graphemes-container">
                        {analysisData.graphemes.graphemes.map((grapheme, idx) => (
                          <div key={idx} className="grapheme-item">
                            <span className="grapheme">{grapheme.grapheme}</span>
                            <span className="ipa">{grapheme.ipa}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p>No grapheme data available for this word.</p>
                    )}
                  </div>
                )}
                
                {activeView === 'relatives' && (
                  <div className="related-section">
                    {analysisData.relatives?.morphological_relatives?.length > 0 ? (
                      <>
                        <h4>🧬 Morphological Relatives:</h4>
                        <div className="related-word-list">
                          {analysisData.relatives.morphological_relatives.map((word, idx) => (
                            <span 
                              key={idx} 
                              className="related-word clickable-word"
                              onClick={(e) => handleWordClick(word, e)}
                            >
                              {word}{idx < analysisData.relatives.morphological_relatives.length - 1 ? ', ' : ''}
                            </span>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="related-subsection">
                        <h4>🧬 Morphological Relatives:</h4>
                        <p>No morphological relatives found for this word.</p>
                      </div>
                    )}
                    
                    {analysisData.relatives?.etymological_relatives?.length > 0 ? (
                      <>
                        <h4>📜 Etymological Relatives:</h4>
                        <div className="related-word-list">
                          {analysisData.relatives.etymological_relatives.map((word, idx) => (
                            <span 
                              key={idx} 
                              className="related-word clickable-word"
                              onClick={(e) => handleWordClick(word, e)}
                            >
                              {word}{idx < analysisData.relatives.etymological_relatives.length - 1 ? ', ' : ''}
                            </span>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="related-subsection">
                        <h4>📜 Etymological Relatives:</h4>
                        <p>No etymological relatives found for this word.</p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <div className="container" style={{ margin: '0 auto', maxWidth: 1100, width: '100%' }}>
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
                  <button className="mode-button" onClick={() => setIsEditMode(!isEditMode)}>{isEditMode ? '📖 Read!' : '✏️ Edit Text'}</button>
                  <button className="clear-button" onClick={() => { setText(''); setAnalysisData({ morphemes: null, meaning: null, etymology: null, graphemes: null, relatives: null }); setError(null); setLeftOpen(false); setIsEditMode(true); }}>Clear Text</button>
                  {/* New: dots toggle + Finish Reading */}
                  <button className="clear-button" onClick={() => setShowHintDots(v => !v)} title="Toggle hint dots">{showHintDots ? '• Hide Dots' : '• Show Dots'}</button>
                  <button className="mode-button" onClick={() => setShowPractice(v => !v)} title="Open practice tray">Finish Reading ({clickedWords.length})</button>
                </>
              )}
            </div>
          </div>

          {/* Clickable words */}
          {!isEditMode && text ? (
            <div className="clickable-text">{renderTextWithClickableWords()}</div>
          ) : null}

          {/* Practice tray */}
          {showPractice && (
            <PracticePanel words={clickedWords} onClose={() => setShowPractice(false)} />
          )}
        </div>
      </div>
    </div>
  );
};

export default MorphemeHighlighter;