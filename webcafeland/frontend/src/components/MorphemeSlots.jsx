import React from 'react';

export default function MorphemeSlots({ placed, onPlace, onRemove, selectedTile, requiredSlots }) {
  const Slot = ({ name }) => {
    const val = placed[name];
    const required = !!requiredSlots?.[name];

    return (
      <div
        className={`swi-slot ${val ? 'filled' : 'empty'}`}
        role="button"
        tabIndex={0}
        aria-label={`${name} slot ${required ? '' : '(not required) '} ${val ? `filled with ${val.morpheme}` : 'empty'}`}
        onClick={() => {
          if (val) onRemove(name);
          else if (selectedTile) onPlace(name, selectedTile);
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (val) onRemove(name);
            else if (selectedTile) onPlace(name, selectedTile);
          }
          if ((e.key === 'Backspace' || e.key === 'Delete') && val) {
            e.preventDefault();
            onRemove(name);
          }
        }}
      >
        <div className="swi-slot-label">
          {name[0].toUpperCase() + name.slice(1)} {!required && <span style={{ color: '#94a3b8' }}>(none)</span>}
        </div>
        <div className="swi-slot-body">
          {val ? (
            <span className={`swi-tile in-slot ${val.type}`}>{val.morpheme}</span>
          ) : (
            <span className="swi-slot-placeholder">
              {required ? 'Drop or click a tile' : 'No morpheme here'}
            </span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="swi-slots">
      <Slot name="prefix" />
      <Slot name="root" />
      <Slot name="suffix" />
    </div>
  );
}
