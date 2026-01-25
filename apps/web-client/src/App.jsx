import { useState } from 'react';
import './App.css';

function App() {
  const [inputText, setInputText] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState(null);

  const handleScan = async () => {
    if (!inputText.trim()) return;

    setIsScanning(true);
    setResult(null);

    // Call the backend API
    try {
      const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputText }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();

      setResult({
        score: data.score,
        verdict: data.verdict
      });
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to connect to the analysis server. Make sure the backend is running.');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="app-container">
      <div className="glass-card">
        <header className="header">
          <h1>Fake News <span className="gradient-text">Detector</span></h1>
          <p>Analyze text for potential AI generation with advanced models.</p>
        </header>

        <main className="main-content">
          <textarea
            className="text-input"
            placeholder="Paste your text here to analyze..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            rows={8}
          />

          <button
            className={`scan-button ${isScanning ? 'scanning' : ''}`}
            onClick={handleScan}
            disabled={isScanning || !inputText.trim()}
          >
            {isScanning ? 'Scanning...' : 'Scan Text'}
          </button>

          {result && (
            <div className="result-area fade-in">
              <div className="result-card">
                <h3>Analysis Result</h3>
                <div className="score-display">
                  <span className="score-label">AI Probability:</span>
                  <span className={`score-value ${result.score > 50 ? 'high' : 'low'}`}>
                    {result.score}%
                  </span>
                </div>
                <p className="verdict">{result.verdict}</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
