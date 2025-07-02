import React from 'react';
import FileSystem from './components/FileSystem';

function App() {
  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-indigo-900 via-slate-900 to-indigo-800 flex items-center justify-center">
      <div className="w-full max-w-4xl flex flex-col bg-white/10 backdrop-blur-md rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
        <div className="flex-1 min-h-0 flex flex-col overflow-y-auto">
          <FileSystem />
        </div>
        <div className="absolute bottom-2 left-0 right-0 text-center text-slate-400 text-xs">
          <span></span>
        </div>
      </div>
    </div>
  );
}

export default App;