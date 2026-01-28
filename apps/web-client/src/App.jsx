import { useState } from 'react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('text');
  const [inputText, setInputText] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE = "http://localhost:8000";

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let endpoint = "";
      let payload = {};
      let headers = { "Content-Type": "application/json" };
      let body = null;

      if (activeTab === 'text') {
        endpoint = "/detect/text";
        payload = { text: inputText };
        body = JSON.stringify(payload);
      } else if (activeTab === 'image') {
        endpoint = "/detect/image";
        payload = { image_url: imageUrl };
        body = JSON.stringify(payload);
      } else if (activeTab === 'video') {
        endpoint = "/detect/video";
        payload = { video_url: videoUrl };
        body = JSON.stringify(payload);
      } else if (activeTab === 'file') {
        endpoint = "/detect/file";
        const formData = new FormData();
        formData.append("file", selectedFile);
        headers = {}; // Let browser set boundary
        body = formData;
      }

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: headers,
        body: body,
      });

      if (!response.ok) {
        throw new Error(`Server Error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score < 30) return "#4caf50"; // Green (Human/Real)
    if (score < 70) return "#ff9800"; // Orange (Uncertain)
    return "#f44336"; // Red (AI/Fake)
  };

  return (
    <div className="container">
      <header className="header">
        <h1>🔍 AI Content Detector</h1>
        <p>Analyze Text, Images, Videos, and Files for AI Generation</p>
      </header>

      <div className="tabs">
        <button className={activeTab === 'text' ? 'active' : ''} onClick={() => setActiveTab('text')}>📝 Text</button>
        <button className={activeTab === 'image' ? 'active' : ''} onClick={() => setActiveTab('image')}>🖼️ Image URL</button>
        <button className={activeTab === 'video' ? 'active' : ''} onClick={() => setActiveTab('video')}>🎥 Video URL</button>
        <button className={activeTab === 'file' ? 'active' : ''} onClick={() => setActiveTab('file')}>📁 File Upload</button>
      </div>

      <main className="main-content">
        <div className="input-section">
          {activeTab === 'text' && (
            <textarea
              placeholder="Paste text here to analyze..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows={8}
            />
          )}

          {activeTab === 'image' && (
            <input
              type="text"
              placeholder="Paste Image URL..."
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
            />
          )}

          {activeTab === 'video' && (
            <input
              type="text"
              placeholder="Paste Video URL (MP4/WebM)..."
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
            />
          )}

          {activeTab === 'file' && (
            <div className="file-upload">
              <input
                type="file"
                onChange={(e) => setSelectedFile(e.target.files[0])}
              />
              {selectedFile && <p>Selected: {selectedFile.name}</p>}
            </div>
          )}

          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={loading || (activeTab === 'text' && !inputText) || (activeTab === 'image' && !imageUrl) || (activeTab === 'file' && !selectedFile)}
          >
            {loading ? "Analyzing..." : "Analyze Content"}
          </button>

          {error && <div className="error-msg">{error}</div>}
        </div>

        {result && (
          <div className="result-section">
            <h2>Analysis Result</h2>

            <div className="score-card" style={{ borderColor: getScoreColor(result.score) }}>
              <div className="score-value" style={{ color: getScoreColor(result.score) }}>
                {result.score.toFixed(1)}%
              </div>
              <div className="score-label">AI Generation Probability</div>
            </div>

            <div className="verdict">
              <strong>Verdict:</strong> {result.verdict}
            </div>

            {result.details && (
              <div className="details">
                <h3>Details</h3>
                <pre>{JSON.stringify(result.details, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
