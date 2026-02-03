import { useState } from 'react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('text');
  const [inputText, setInputText] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  // Result and error tracking are handled as per-tab objects to allow persistence
  const [tabResults, setTabResults] = useState({
    text: null,
    image: null,
    video: null,
    file: null
  });
  const [tabErrors, setTabErrors] = useState({
    text: null,
    image: null,
    video: null,
    file: null
  });

  const [loading, setLoading] = useState(false);

  const API_BASE = import.meta.env.VITE_API_URL || "/api";

  const handleAnalyze = async () => {
    setLoading(true);

    // Clear previous result/error for THIS tab before starting
    setTabErrors(prev => ({ ...prev, [activeTab]: null }));
    setTabResults(prev => ({ ...prev, [activeTab]: null }));

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
      console.log(`DEBUG: Result for ${activeTab}`, data);
      setTabResults(prev => ({ ...prev, [activeTab]: data }));

    } catch (err) {
      setTabErrors(prev => ({ ...prev, [activeTab]: err.message }));
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score < 30) return "#4caf50"; // Green (Human/Real)
    if (score < 70) return "#ff9800"; // Orange (Uncertain)
    return "#f44336"; // Red (AI/Fake)
  };

  const currentResult = tabResults[activeTab];
  const currentError = tabErrors[activeTab];

  return (
    <div className="container">
      <header className="header">
        <h1>🔍 AI Content Detector</h1>
        <p>Analyze Text, Images, Videos, and Files for AI Generation</p>
      </header>

      <div className="tabs">
        <button
          className={activeTab === 'text' ? 'active' : ''}
          onClick={() => setActiveTab('text')}
        >
          📝 Text
        </button>
        <button
          className={activeTab === 'image' ? 'active' : ''}
          onClick={() => setActiveTab('image')}
        >
          🖼️ Image URL
        </button>
        <button
          className={activeTab === 'video' ? 'active' : ''}
          onClick={() => setActiveTab('video')}
        >
          🎥 Video URL
        </button>
        <button
          className={activeTab === 'file' ? 'active' : ''}
          onClick={() => setActiveTab('file')}
        >
          📁 File Upload
        </button>
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
            <div className="file-upload-container">
              <label htmlFor="file-input" className="file-upload-label">
                <div className="upload-icon">📁</div>
                <div className="upload-text">
                  <strong>Click to upload</strong> or drag and drop
                </div>
                <div className="upload-subtext">PDF, Image, Word, Excel, or Video (max 50MB)</div>
                <div className="browse-btn">Browse Files</div>
              </label>
              <input
                id="file-input"
                type="file"
                className="hidden-file-input"
                onChange={(e) => setSelectedFile(e.target.files[0])}
              />
              {selectedFile && (
                <div className="selected-file-badge">
                  <span className="file-name">📄 {selectedFile.name}</span>
                  <button className="clear-file" onClick={() => setSelectedFile(null)}>✕</button>
                </div>
              )}
            </div>
          )}

          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={loading || (activeTab === 'text' && !inputText) || (activeTab === 'image' && !imageUrl) || (activeTab === 'file' && !selectedFile)}
          >
            {loading ? "Analyzing..." : "Analyze Content"}
          </button>

          {currentError && <div className="error-msg">{currentError}</div>}
        </div>

        {currentResult && (
          <div className="result-section">
            <div className="verdict">
              <strong>Verdict:</strong> {currentResult.verdict}
            </div>

            <div className="score-card" style={{ borderColor: getScoreColor(currentResult.score) }}>
              <div className="score-value" style={{ color: getScoreColor(currentResult.score) }}>
                {currentResult.score.toFixed(1)}%
              </div>
              <div className="score-label">AI Generation Probability</div>
            </div>

            {currentResult.confidence_score !== undefined && (
              <div className="confidence-indicator-v2">
                <div className="conf-label">ALGORITHM CONFIDENCE</div>
                <div className="conf-score-bar">
                  <div
                    className="conf-fill"
                    style={{ width: `${currentResult.confidence_score}%` }}
                  ></div>
                </div>
                <div className="conf-value">{currentResult.confidence_score}%</div>
              </div>
            )}

            {(currentResult.key_phrases || []).length >= 0 && (
              <div className="key-phrases-section">
                <h4>AI Detection Signals:</h4>
                <div className="tags">
                  {(currentResult.key_phrases || []).length > 0 ? (
                    currentResult.key_phrases.map((phrase, idx) => (
                      <span key={idx} className="tag">{phrase}</span>
                    ))
                  ) : (
                    <span className="tag-muted">No specific linguistic signals detected</span>
                  )}
                  {activeTab !== 'text' && (currentResult.key_phrases || []).length === 0 && (
                    <span className="tag">High Frequency Scan</span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
