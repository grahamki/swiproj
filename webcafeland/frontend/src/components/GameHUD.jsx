import React from 'react';

export default function GameHUD({ index, total, score, onExit }) {
  const accuracy = total ? Math.round((score / total) * 100) : 0;
  return (
    <div className="swi-hud">
      <div className="swi-hud-left">
        <strong>Progress:</strong> {index + 1}/{total}
        <span className="swi-dot">•</span>
        <strong>Accuracy:</strong> {accuracy}%
      </div>
      <div className="swi-hud-right">
        <button className="swi-btn ghost" onClick={onExit} title="Exit game">Exit</button>
      </div>
    </div>
  );
}
