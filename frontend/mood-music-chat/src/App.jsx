import React from 'react';
import Chat from './Chat';

function App() {
  return (
    <>
      <style>{`
        body, html, #root {
          margin: 0;
          padding: 0;
          height: 100%;
          width: 100%;
          background-color: #2e2e2e;
        }
      `}</style>

      <div
        style={{
          height: '100vh',
          width: '100vw',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Chat />
      </div>
    </>
  );
}

export default App;
