import React from 'react';

/**
 * Electron currently hosts the proven renderer in ../public through the local UI server.
 * This component is the React migration seam for the final packaged desktop build.
 */
export default function App() {
  return <main style={{ padding: 32, background: '#09111d', color: '#f4f7fb', minHeight: '100vh', fontFamily: 'system-ui' }}>Drishti AI renderer bootstrap</main>;
}
