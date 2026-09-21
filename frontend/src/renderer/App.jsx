import React from 'react';

/**
 * The packaged shell uses the same canonical browser workspace as development.
 * Keeping this wrapper real prevents a second, divergent desktop UI from
 * becoming a placeholder product surface.
 */
export default function App() {
  const url = window.__DRISHTI_UI_URL__ || 'http://127.0.0.1:4173';
  return <iframe title="Drishti AI security workspace" src={url} style={{ border: 0, width: '100%', height: '100vh', background: '#09111d' }} />;
}
