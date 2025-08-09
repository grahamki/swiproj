import React, { useEffect, useState } from 'react';
import './App.css';
import MorphemeHighlighter from './components/MorphemeHighlighter';
import PracticeSetup from './pages/PracticeSetup';
import SWIGamePage from './pages/SWIGamePage';

// Resolve current route from pathname or hash
const resolveRoute = () => {
  try {
    const { pathname, hash } = window.location;
    const h = (hash || '').replace(/^#/, '');
    const full = h || pathname;
    if (full === '/practice') return 'setup';
    if (full === '/practice/play') return 'play';
  } catch {}
  return 'home';
};

function App() {
  const [route, setRoute] = useState(resolveRoute);

  useEffect(() => {
    const onChange = () => setRoute(resolveRoute());
    window.addEventListener('hashchange', onChange);
    window.addEventListener('popstate', onChange);
    return () => {
      window.removeEventListener('hashchange', onChange);
      window.removeEventListener('popstate', onChange);
    };
  }, []);

  return (
    <div className="App">
      {route === 'setup' ? (
        <PracticeSetup />
      ) : route === 'play' ? (
        <SWIGamePage />
      ) : (
        <MorphemeHighlighter />
      )}
    </div>
  );
}

export default App;
