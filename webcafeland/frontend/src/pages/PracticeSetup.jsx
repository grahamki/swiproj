import React, { useEffect, useMemo, useState } from 'react';
import { practiceStore } from '../lib/practiceStore';
import '../styles/swi-game.css';

export default function PracticeSetup() {
  const tray = useMemo(() => practiceStore.getTrayWords(), []);
  const [filter, setFilter] = useState('');
  const [sortBy, setSortBy] = useState('alpha'); // 'alpha' | 'length'
  const [selected, setSelected] = useState(() => new Set(practiceStore.getSelectedWords().map(w => w.toLowerCase())));

  const visible = useMemo(() => {
    let list = tray.slice();
    if (filter.trim()) {
      const f = filter.trim().toLowerCase();
      list = list.filter(w => w.toLowerCase().includes(f));
    }
    if (sortBy === 'alpha') list.sort((a, b) => a.localeCompare(b));
    if (sortBy === 'length') list.sort((a, b) => b.length - a.length);
    return list;
  }, [tray, filter, sortBy]);

  const allSelected = visible.length > 0 && visible.every(w => selected.has(w.toLowerCase()));

  const toggleOne = (word) => {
    const lc = word.toLowerCase();
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(lc)) next.delete(lc);
      else next.add(lc);
      return next;
    });
  };

  const selectAll = () => {
    setSelected(prev => {
      const next = new Set(prev);
      for (const w of visible) next.add(w.toLowerCase());
      return next;
    });
  };

  const deselectAll = () => {
    setSelected(prev => {
      const next = new Set(prev);
      for (const w of visible) next.delete(w.toLowerCase());
      return next;
    });
  };

  // Centralized navigation (supports BrowserRouter and HashRouter)
  const navigateTo = (path) => {
    const href = String(window.location.href || '');
    const target = path.startsWith('/') ? path : `/${path}`;
    if (href.includes('#')) {
      window.location.hash = target;
    } else {
      window.location.assign(target);
    }
  };

  const startGame = () => {
    const chosen = tray.filter(w => selected.has(w.toLowerCase()));
    if (chosen.length === 0) return;
    practiceStore.setSelectedWords(chosen);
    navigateTo('/practice/play');
  };

  useEffect(() => {
    const chosen = tray.filter(w => selected.has(w.toLowerCase()));
    practiceStore.setSelectedWords(chosen);
  }, [selected, tray]);

  if (!tray.length) {
    return (
      <div className="practice-setup">
        <h2>Practice</h2>
        <p>No words in your Finish Reading tray yet.</p>
        <p>Go back, click some words while reading, then return here.</p>
        <button className="swi-btn" onClick={() => navigateTo('/')}>Back to Home</button>
      </div>
    );
  }

  return (
    <div className="practice-setup">
      <header className="setup-header">
        <h2>Select words to practice</h2>
        <div className="controls">
          <input
            type="search"
            placeholder="Filter words…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            aria-label="Filter words"
          />
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} aria-label="Sort words">
            <option value="alpha">A → Z</option>
            <option value="length">By length</option>
          </select>
          <button onClick={allSelected ? deselectAll : selectAll}>
            {allSelected ? 'Deselect all (visible)' : 'Select all (visible)'}
          </button>
          <button
            className="swi-btn primary"
            disabled={[...selected].length === 0}
            onClick={startGame}
            title="Start the game with the selected words"
          >
            Start Game ({tray.filter(w => selected.has(w.toLowerCase())).length})
          </button>
          <button className="swi-btn ghost" onClick={() => navigateTo('/')}>Exit</button>
        </div>
      </header>

      <ul className="word-list" role="listbox" aria-label="Words to practice">
        {visible.map((w) => {
          const lc = w.toLowerCase();
          const isSel = selected.has(lc);
          return (
            <li key={w} className={`word-row ${isSel ? 'selected' : ''}`}>
              <label>
                <input
                  type="checkbox"
                  checked={isSel}
                  onChange={() => toggleOne(w)}
                  aria-label={`Select ${w}`}
                />
                <span className="word">{w}</span>
              </label>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
