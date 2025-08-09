import React from 'react';

export default function FeedbackCard({ trial, result, entry, onNext }) {
  const icon = result.correct ? '✅' : '❌';
  return (
    <div className="swi-feedback">
      <div className="swi-feedback-header">
        <span className="big">{icon}</span>
        <div>
          <div className="word">{entry.word}</div>
          <div className="explain">{result.correct ? 'Great job!' : 'Review the correct split:'}</div>
        </div>
      </div>
      {!result.correct && (
        <div className="swi-correct-split">
          {entry.morphemes.map((m, i) => (
            <span key={i} className={`swi-tile ${m.type}`}>{m.morpheme}</span>
          ))}
        </div>
      )}
      <div className="swi-meanings">
        {entry.morphemes.map((m, i) => (
          <div key={i} className="meaning-row">
            <span className={`swi-chip ${m.type}`}>{m.morpheme}</span>
            <span className="meaning">{m.meaning}</span>
          </div>
        ))}
      </div>
      {entry.families?.length ? (
        <div className="swi-families">
          <div className="label">Family:</div>
          <div className="list">{entry.families.slice(0, 4).join(', ')}</div>
        </div>
      ) : null}
      <div className="swi-actions">
        <button className="swi-btn primary" onClick={onNext}>Next</button>
      </div>
    </div>
  );
}
