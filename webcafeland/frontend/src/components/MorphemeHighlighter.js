import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import './MorphemeHighlighter.css';
import apiService from '../services/api';

/**
 * @typedef {Object} Morpheme
 * @property {string} morpheme
 * @property {'prefix'|'root'|'suffix'} type
 * @property {string} [meaning]
 *
 * @typedef {Object} Analysis
 * @property {string} word
 * @property {Morpheme[]} morphemes
 */

// Cheap affix lists for hint heuristic
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

// Normalize morphemes from various shapes to an array of {morpheme,type,meaning}
function normalizeMorphemes(input) {
  // Already an array
  if (Array.isArray(input)) return input;
  // Shape: { morphemes: [...] }
  if (input && Array.isArray(input.morphemes)) return input.morphemes;
  // Shape: { prefix: {part, meaning}, root: {...}, suffix: {...} }
  if (input && (input.prefix || input.root || input.suffix)) {
    const out = [];
    if (input.prefix?.part) out.push({ morpheme: input.prefix.part, type: 'prefix', meaning: input.prefix.meaning || '' });
    if (input.root?.part) out.push({ morpheme: input.root.part, type: 'root', meaning: input.root.meaning || '' });
    if (input.suffix?.part) out.push({ morpheme: input.suffix.part, type: 'suffix', meaning: input.suffix.meaning || '' });
    return out;
  }
  // Unknown shape -> empty
  return [];
}

// Heuristic split using known affixes if AI returns 0–1 piece
function heuristicSplitSegments(word) {
  const lc = String(word || '').toLowerCase();
  let pref = '';
  for (const p of [...KNOWN_PREFIXES].sort((a,b)=>b.length-a.length)) {
    if (lc.startsWith(p)) { pref = p; break; }
  }
  let suff = '';
  for (const s of [...KNOWN_SUFFIXES].sort((a,b)=>b.length-a.length)) {
    if (lc.endsWith(s) && lc.length > s.length) { suff = s; break; }
  }
  const start = pref ? pref.length : 0;
  const end = suff ? lc.length - suff.length : lc.length;
  const core = word.slice(start, end);
  const segs = [];
  if (pref) segs.push({ text: word.slice(0, start), role: 'prefix', meaning: '' });
  if (core) segs.push({ text: core, role: 'root', meaning: '' });
  if (suff) segs.push({ text: word.slice(end), role: 'suffix', meaning: '' });
  return segs;
}

const MorphemeHighlighter = () => {
  const [text, setText] = useState('');
  // cache: Map<string, MorphemeAnalysis>
  const [analysisCache, setAnalysisCache] = useState(() => new Map());
  // overlays: Record<number, Seg[]>
  const [overlays, setOverlays] = useState({});
  const [lowClutter, setLowClutter] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('mh.lowClutter')) || false;
    } catch {
      return false;
    }
  });

  // Practice tray state: clicked words and visibility
  const [clickedWords, setClickedWords] = useState(() => {
    try {
      const v = JSON.parse(localStorage.getItem('mh.clickedWords'));
      return Array.isArray(v) ? v : [];
    } catch {
      return [];
    }
  });
  const [showPractice, setShowPractice] = useState(false);

  // Hint dots toggle (persist)
  const [showHintDots, setShowHintDots] = useState(() => {
    try {
      const v = localStorage.getItem('mh.hintDots');
      return v === null ? true : JSON.parse(v);
    } catch {
      return true;
    }
  });
  useEffect(() => {
    localStorage.setItem('mh.hintDots', JSON.stringify(showHintDots));
  }, [showHintDots]);

  // Save clicked word (dedupe by lowercase, keep display casing)
  const addClickedWord = (w) => {
    const s = String(w || '').trim();
    if (!s) return;
    setClickedWords(prev =>
      prev.some(p => p.toLowerCase() === s.toLowerCase()) ? prev : [...prev, s]
    );
  };

  // Heuristic helpers for hint dots
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

  // Ensure these exist (fix no-undef for isEditMode, setIsEditMode, liveRef, textAreaRef)
  const [isEditMode, setIsEditMode] = useState(true);
  const textAreaRef = useRef(null);
  const liveRef = useRef(null);

  // Announce helper (used by Escape handler)
  const announce = useCallback((msg) => {
    if (liveRef.current) {
      liveRef.current.textContent = msg;
      setTimeout(() => {
        if (liveRef.current) liveRef.current.textContent = '';
      }, 1200);
    }
  }, []);

  const tokens = useMemo(() => tokenize(text), [text]);

  // Inline overlay only
  function handleWordClickInline(word, idx) {
    if (!word || word.trim() === '') return;
    addClickedWord(word);
    if (overlays[idx]) return;

    // 1) Optimistic single block
    setOverlays(prev => ({ ...prev, [idx]: [{ text: word, role: 'root', meaning: 'root/base' }] }));

    // 2) Immediate heuristic split (visible even if network is slow)
    const heuristic = heuristicSplitSegments(word);
    if (heuristic.length >= 2) {
      setOverlays(prev => ({ ...prev, [idx]: heuristic }));
    }

    const key = word.toLowerCase();
    let data = analysisCache.get(key);

    (async () => {
      try {
        // 3) Fetch morphemes (cache first)
        if (!data?.morphemes) {
          const fetched = await apiService.analyzeMorpheme(word, 'morphemes');
          const next = new Map(analysisCache);
          const existing = next.get(key) || {};
          next.set(key, { ...existing, ...fetched });
          setAnalysisCache(next);
          data = next.get(key);
        }

        // 4) Segment using returned morphemes
        const morArr = normalizeMorphemes(data?.morphemes ?? data);
        let segs = segmentWord(word, morArr);

        // 5) Fallback to heuristic if still single block
        if (!segs || segs.length === 1) {
          const alt = heuristicSplitSegments(word);
          if (alt.length >= 2) segs = alt;
        }

        // 6) Upgrade overlay only if it adds more parts than current
        setOverlays(prev => {
          const cur = prev[idx] || [];
          const better = Array.isArray(segs) && segs.length > cur.length ? segs : cur;
          return { ...prev, [idx]: better.length ? better : [{ text: word, role: 'root', meaning: 'root/base' }] };
        });
      } catch (err) {
        console.error('Inline analyze error:', err);
        // keep current overlay
      }
    })();
  }

  const PracticePanel = ({ words, onClose }) => (
    <div className="practice-panel" onMouseDown={(e) => e.stopPropagation()}>
      <div className="practice-header">
        <span>Finish Reading</span>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      <div className="practice-body">
        {(!words || words.length === 0) ? (
          <p className="practice-empty">No saved words yet.</p>
        ) : (
          <ul style={{ paddingLeft: 16, margin: '8px 0' }}>
            {words.map((w, i) => (
              <li key={`${w}-${i}`} style={{ marginBottom: 6 }}>{w}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );

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
          onClick={() => handleWordClickInline(t.text, t.idx)}
          title={`Click to analyze: ${t.text}`}
          {...(dotted ? { 'aria-label': 'Likely morphologically complex' } : {})}
          role="button"
          tabIndex={0}
          aria-expanded={Boolean(overlays[t.idx])}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleWordClickInline(t.text, t.idx);
            } else if (e.key === 'Escape' && overlays[t.idx]) {
              e.preventDefault();
              setOverlays(prev => {
                const next = { ...prev };
                delete next[t.idx];
                return next;
              });
              announce(`Cleared breakdown for ${t.text}.`);
            }
          }}
        >
          {segs
            ? segs.map((s, k) => (
                <span
                  key={k}
                  className={`seg ${s.role} ${lowClutter ? 'low' : ''}`}
                  title={s.meaning || s.role}
                >
                  {s.text}
                </span>
              ))
            : t.text}
        </span>
      );
    });
  };

  const handleTextChange = useCallback((e) => {
    setText(e.target.value);
    setOverlays({});
  }, []);

  return (
    <div className="container">
      <div className="header">
        <h1>📚 Morpheme Highlighter</h1>
        <p>Highlight any word or section to break it down or summarize.</p>
      </div>

      {/* Screen reader announcements */}
      <div aria-live="polite" className="sr-only" ref={liveRef}></div>

      <div className="content">
        <div className="text-input-section">
          <label htmlFor="text-input" className="input-label">Paste or type your text here:</label>
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

          <div className="instructions">💡 Highlight a word to see its morphemes.</div>

          <div className="button-group">
            <button className="clear-button" onClick={() => setLowClutter(v => !v)} title="Toggle low-clutter mode">
              {lowClutter ? '🎨 Use Color' : '🫧 Low-Clutter'}
            </button>
            <button className="clear-button" onClick={() => setShowHintDots(v => !v)} title="Toggle hint dots">
              {showHintDots ? '• Hide Dots' : '• Show Dots'}
            </button>
            <button className="mode-button" onClick={() => setShowPractice(v => !v)} title="Open practice tray">
              Finish Reading ({clickedWords.length})
            </button>
            {text && (
              <>
                <button className="mode-button" onClick={() => setIsEditMode(!isEditMode)}>
                  {isEditMode ? '📖 Read!' : '✏️ Edit Text'}
                </button>
                <button
                  className="clear-button"
                  onClick={() => { setText(''); setOverlays({}); setIsEditMode(true); }}
                >
                  Clear Text
                </button>
              </>
            )}
          </div>
        </div>

        {showPractice && (
          <PracticePanel words={clickedWords} onClose={() => setShowPractice(false)} />
        )}
      </div>
    </div>
  );
};

export default MorphemeHighlighter;