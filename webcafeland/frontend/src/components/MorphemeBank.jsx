import React from 'react';

export default function MorphemeBank({ tiles, placed, onPick, selectedTile, disabled }) {
  const placedIds = new Set(['prefix','root','suffix'].map(k => placed[k]?.id).filter(Boolean));
  const available = tiles.filter(t => !placedIds.has(t.id));

  return (
    <div className="swi-bank">
      {available.map(t => {
        const isSelected = selectedTile?.id === t.id;
        return (
          <button
            key={t.id}
            className={`swi-tile ${t.type} ${isSelected ? 'selected' : ''}`}
            disabled={disabled}
            onClick={() => onPick(t)}
            aria-pressed={isSelected}
            title={t.meaning || t.type}
          >
            {t.morpheme}
          </button>
        );
      })}
      {available.length === 0 && <div className="swi-bank-empty">All tiles placed.</div>}
    </div>
  );
}
