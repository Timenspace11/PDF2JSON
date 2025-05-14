// src/App.tsx
import React from "react";
import "./App.css";
import UploadForm from "./UploadForm";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>PDF to JSON Converter</h1>
      </header>
      <main>
        <UploadForm />
      </main>
    </div>
  );
}

export default App;
