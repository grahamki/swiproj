import React from 'react';

export default function SummaryModal({ events, onRestart, onExport }) {
  const total = events.length;
  const correct = events.filter(e => e.correct).length;
  const avgMs = Math.round(events.reduce((a, e) => a + (e.latencyMs || 0), 0) / (total || 1));
  const acc = total ? Math.round((correct / total) * 100) : 0;

  return (
    <div className="swi-summary">
      <h2>Session Summary</h2>
      <div className="swi-summary-grid">
        <div><strong>Items:</strong> {total}</div>
        <div><strong>Accuracy:</strong> {acc}%</div>
        <div><strong>Avg time:</strong> {avgMs} ms</div>
      </div>
      <div className="swi-summary-actions">
        <button className="swi-btn" onClick={onRestart}>Play Again</button>
        <button className="swi-btn primary" onClick={onExport}>Export CSV</button>
      </div>
      <div className="swi-summary-list">
        {events.map((e, i) => (
          <div key={i} className={`swi-summary-row ${e.correct ? 'ok' : 'no'}`}>
            <div className="word">{e.word}</div>
            <div className="placed">
              {['prefix','root','suffix'].map(k => (
                <span key={k} className="pair">
                  <span className="k">{k[0].toUpperCase()+k.slice(1)}:</span> {e.placed[k] || '—'}
                </span>
              ))}
            </div>
            <div className="lat">{e.latencyMs} ms</div>
          </div>
        ))}
      </div>
    </div>
  );
}
