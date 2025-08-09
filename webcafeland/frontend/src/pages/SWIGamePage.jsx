import React, { useEffect, useMemo, useState } from 'react';
import { SEED_WORDS } from '../lib/gameData';
import { GAME_STATES, makeTrial, scoreTrial, shuffle } from '../lib/gameEngine';
import { saveSession, loadSession, clearSession } from '../lib/gameStore';
import { practiceStore } from '../lib/practiceStore';
import MorphemeSlots from '../components/MorphemeSlots';
import MorphemeBank from '../components/MorphemeBank';
import GameHUD from '../components/GameHUD';
import FeedbackCard from '../components/FeedbackCard';
import SummaryModal from '../components/SummaryModal';
import apiService from '../services/api';
import '../styles/swi-game.css';

export default function SWIGamePage() {
  // Selected words from setup (fallback: seed)
  const selectedWords = useMemo(() => practiceStore.getSelectedWords(), []);
  const [entries, setEntries] = useState([]);      // [{word, morphemes, families}]
  const [preparing, setPreparing] = useState(false);
  const [prepError, setPrepError] = useState(null);

  // Prefetch morphemes for selected words; fallback to seeds if none
  useEffect(() => {
    const words = (selectedWords && selectedWords.length) ? selectedWords : SEED_WORDS.map(e => e.word);
    let cancelled = false;

    const PREFIXES = ["un","re","in","im","dis","non","pre","mis","trans","sub","inter","over","under","anti","auto","con","dys"];
    const SUFFIXES = ["able","ible","tion","ation","ment","ness","less","ful","ive","ing","ed","ity","ly","al","ion","en","er","est","ous"];
    const heuristicSegments = (w) => {
      const lc = String(w || '').toLowerCase();
      const pref = [...PREFIXES].sort((a,b)=>b.length-a.length).find(p => lc.startsWith(p)) || '';
      const suff = [...SUFFIXES].sort((a,b)=>b.length-a.length).find(s => lc.endsWith(s) && lc.length > s.length) || '';
      const start = pref ? pref.length : 0;
      const end = suff ? lc.length - suff.length : lc.length;
      const core = w.slice(start, end);
      const segs = [];
      if (pref) segs.push({ morpheme: w.slice(0, start), type: 'prefix', meaning: '' });
      if (core) segs.push({ morpheme: core, type: 'root', meaning: '' });
      if (suff) segs.push({ morpheme: w.slice(end), type: 'suffix', meaning: '' });
      return segs;
    };

    const normalize = (res) => {
      if (!res) return [];
      if (Array.isArray(res)) return res;
      if (Array.isArray(res.morphemes)) return res.morphemes;
      return [];
    };

    const fetchAll = async () => {
      setPreparing(true);
      setPrepError(null);
      try {
        const results = await Promise.all(words.map(async (w) => {
          try {
            const res = await apiService.analyzeMorpheme(w, 'morphemes');
            let segs = normalize(res);
            if (!segs || segs.length < 2) {
              const h = heuristicSegments(w);
              if (h.length >= 2) segs = h;
            }
            if (!segs || segs.length === 0) {
              segs = [{ morpheme: w, type: 'root', meaning: '' }];
            }
            // Keep only one of each type if multiples exist
            const pick = (type) => segs.find(m => m.type === type);
            const compact = [pick('prefix'), pick('root'), pick('suffix')].filter(Boolean);
            return { word: w, morphemes: compact.length ? compact : segs, families: [] };
          } catch {
            const h = heuristicSegments(w);
            const segs = h.length ? h : [{ morpheme: w, type: 'root', meaning: '' }];
            return { word: w, morphemes: segs, families: [] };
          }
        }));
        if (!cancelled) setEntries(shuffle(results));
      } catch (e) {
        if (!cancelled) setPrepError('Failed to prepare words.');
      } finally {
        if (!cancelled) setPreparing(false);
      }
    };

    fetchAll();
    return () => { cancelled = true; };
  }, [selectedWords]);

  // Queue is entries (already shuffled)
  const queue = entries;

  const [idx, setIdx] = useState(0);
  const [gameState, setGameState] = useState(GAME_STATES.READY);
  const [trial, setTrial] = useState(null);
  const [selectedTile, setSelectedTile] = useState(null);
  const [score, setScore] = useState(0);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const saved = loadSession();
    if (saved && saved.queue && saved.idx < saved.queue.length) {
      setIdx(saved.idx);
      setScore(saved.score || 0);
      setEvents(saved.events || []);
    } else {
      clearSession();
      setIdx(0); setScore(0); setEvents([]);
    }
  }, []);

  useEffect(() => {
    if (trial) {
      saveSession({ queue, idx, trial, score, events, gameState });
    } else {
      clearSession();
    }
  }, [queue, idx, trial, score, events, gameState]);

  const goHome = () => (window.location.assign('/'));
  const startGame = () => {
    if (preparing || !queue.length) return;
    clearSession();
    setIdx(0);
    setScore(0);
    setEvents([]);
    setSelectedTile(null);
    setTrial(makeTrial(queue[0]));
    setGameState(GAME_STATES.IN_TRIAL);
  };

  const entry = queue[idx] || null;

  const onPick = (tile) => setSelectedTile(t => (t && t.id === tile.id ? null : tile));
  const onPlace = (slot, tile) => { setTrial(t => ({ ...t, placed: { ...t.placed, [slot]: tile } })); setSelectedTile(null); };
  const onRemove = (slot) => { setTrial(t => ({ ...t, placed: { ...t.placed, [slot]: null } })); };

  // Only require slots present in the gold entry
  const requiredMap = useMemo(() => {
    const m = { prefix: false, root: false, suffix: false };
    const e = entry || { morphemes: [] };
    e.morphemes?.forEach(x => { if (x?.type && m.hasOwnProperty(x.type)) m[x.type] = true; });
    return m;
  }, [entry]);

  const allFilled = Boolean(
    (!requiredMap.prefix || trial?.placed?.prefix) &&
    (!requiredMap.root   || trial?.placed?.root) &&
    (!requiredMap.suffix || trial?.placed?.suffix)
  );

  const onCheck = () => {
    if (!trial || !entry) return;
    const res = scoreTrial(trial);
    setScore(s => s + (res.correct ? 1 : 0));
    setEvents(ev => ev.concat([{
      trial: idx + 1,
      word: entry.word,
      placed: {
        prefix: trial.placed.prefix?.morpheme || null,
        root: trial.placed.root?.morpheme || null,
        suffix: trial.placed.suffix?.morpheme || null,
      },
      gold: {
        prefix: entry.morphemes.find(m => m.type === 'prefix')?.morpheme || null,
        root: entry.morphemes.find(m => m.type === 'root')?.morpheme || null,
        suffix: entry.morphemes.find(m => m.type === 'suffix')?.morpheme || null,
      },
      correct: res.correct,
      perSlot: res.perSlot,
      latencyMs: res.latencyMs,
      hintUsed: trial.hintUsed
    }]));
    setGameState(GAME_STATES.FEEDBACK);
  };

  const onNext = () => {
    const nextIdx = idx + 1;
    if (nextIdx >= queue.length) { setGameState(GAME_STATES.DONE); return; }
    setIdx(nextIdx);
    setTrial(makeTrial(queue[nextIdx]));
    setSelectedTile(null);
    setGameState(GAME_STATES.IN_TRIAL);
  };

  const onRestart = () => {
    clearSession();
    setIdx(0); setScore(0); setEvents([]);
    setTrial(null);
    setSelectedTile(null);
    setGameState(GAME_STATES.READY);
  };

  return (
    <div className="swi-game">
      <GameHUD index={idx} total={queue.length} score={score} onExit={goHome} />
      <div className="swi-card">
        {gameState === GAME_STATES.READY ? (
          <div className="swi-ready">
            <h2>SWI Morpheme Game</h2>
            <p>Drag or click tiles to fill Prefix, Root, and Suffix.</p>
            {prepError && <p style={{ color: '#dc2626' }}>{prepError}</p>}
            {preparing && <p>Preparing words…</p>}
            <div className="swi-ready-actions">
              <button className="swi-btn primary" onClick={startGame} disabled={preparing || !queue.length}>
                {preparing ? 'Loading…' : 'Start Game'}
              </button>
              <button className="swi-btn ghost" onClick={() => (window.location.assign('/practice'))}>Back to Setup</button>
              <button className="swi-btn ghost" onClick={goHome}>Exit</button>
            </div>
          </div>
        ) : entry && (
          <>
            <div className="swi-target-word">{entry.word}</div>
            <MorphemeSlots
              placed={trial.placed}
              onPlace={onPlace}
              onRemove={onRemove}
              selectedTile={selectedTile}
              requiredSlots={requiredMap}
            />
            {gameState === GAME_STATES.IN_TRIAL && (
              <>
                <MorphemeBank
                  tiles={trial.tiles}
                  placed={trial.placed}
                  onPick={onPick}
                  selectedTile={selectedTile}
                  disabled={false}
                />
                <div className="swi-controls">
                  <button className="swi-btn primary" disabled={!allFilled} onClick={onCheck}>Check</button>
                  <button className="swi-btn ghost" onClick={() => setSelectedTile(null)}>Clear Selection</button>
                </div>
              </>
            )}
            {gameState === GAME_STATES.FEEDBACK && (
              <FeedbackCard trial={trial} result={scoreTrial(trial)} entry={entry} onNext={onNext} />
            )}
            {gameState === GAME_STATES.DONE && (
              <SummaryModal events={events} onRestart={onRestart} onExport={() => {
                const header = ['trial','word','prefix','root','suffix','correct','latencyMs','hintUsed'];
                const rows = events.map(e => [
                  e.trial, e.word, e.placed.prefix || '', e.placed.root || '', e.placed.suffix || '',
                  e.correct ? '1' : '0', e.latencyMs || 0, e.hintUsed ? '1' : '0'
                ]);
                const csv = [header, ...rows].map(r => r.map(x => `"${String(x).replace(/"/g, '""')}"`).join(',')).join('\n');
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = 'swi-game-results.csv';
                a.click();
                URL.revokeObjectURL(a.href);
              }} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
