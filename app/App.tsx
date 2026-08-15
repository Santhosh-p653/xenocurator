import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';

interface ArtifactReport {
  artifact_name: string;
  artifact_id: string;
  estimated_era: string;
  civilization: string;
  perceived_original_function: string;
  archaeological_significance: string;
  historical_context: string;
  condition: string;
  curator_note: string;
}

export default function App() {
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [futureYear, setFutureYear] = useState<string>('3026');
  const [description, setDescription] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [report, setReport] = useState<ArtifactReport | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImage(file);
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!image) return;

    setLoading(true);
    setReport(null);

    const formData = new FormData();
    formData.append('image', image);
    formData.append('future_year', futureYear);
    formData.append('description', description);

    try {
      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Analysis request failed');

      const data: ArtifactReport = await res.json();
      setReport(data);
    } catch (err) {
      alert('Error analyzing artifact. Check backend connection and AWS credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>INTERNET ARCHAEOLOGIST</h1>
        <p className="tagline">Deep-time speculative analysis of 21st-century artifacts</p>
      </header>

      <main className="grid-layout">
        {/* Form Controls */}
        <section className="control-panel">
          <form onSubmit={handleAnalyze} className="upload-form">
            <div className="input-group">
              <label>Select Artifact Image</label>
              <input type="file" accept="image/*" onChange={handleImageChange} required />
              {preview && <img src={preview} alt="Preview" className="image-preview" />}
            </div>

            <div className="input-group">
              <label>Target Future Year</label>
              <input
                type="number"
                value={futureYear}
                onChange={(e) => setFutureYear(e.target.value)}
                required
              />
            </div>

            <div className="input-group">
              <label>Field Notes / Fragmentary Context (Optional)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Found near an ancient caffeine consumption node..."
                rows={3}
              />
            </div>

            <button type="submit" className="btn-primary" disabled={loading || !image}>
              {loading ? 'Decrypting Relic...' : 'Analyze Artifact'}
            </button>
          </form>
        </section>

        {/* Display Card / Display Stand */}
        <section className="display-panel">
          {loading && (
            <div className="loader">
              <div className="spinner"></div>
              <p>Scanning molecular structure with Amazon Nova...</p>
            </div>
          )}

          {!loading && !report && (
            <div className="empty-state">
              <p>Upload a modern object and specify an era to generate a museum catalog entry.</p>
            </div>
          )}

          {report && (
            <article className="museum-card">
              <div className="card-header">
                <span className="disclaimer-badge">FICTIONAL SPECULATION</span>
                <span className="artifact-id">{report.artifact_id}</span>
              </div>

              <h2>{report.artifact_name}</h2>

              <div className="meta-grid">
                <div><strong>Estimated Era:</strong> {report.estimated_era}</div>
                <div><strong>Civilization:</strong> {report.civilization}</div>
                <div><strong>Condition:</strong> {report.condition}</div>
              </div>

              <hr />

              <div className="section">
                <h3>Perceived Function</h3>
                <p>{report.perceived_original_function}</p>
              </div>

              <div className="section">
                <h3>Archaeological Significance</h3>
                <p>{report.archaeological_significance}</p>
              </div>

              <div className="section">
                <h3>Historical Context</h3>
                <p>{report.historical_context}</p>
              </div>

              <blockquote className="curator-note">
                <strong>Curator's Note:</strong> "{report.curator_note}"
              </blockquote>

              <button onClick={handleAnalyze} className="btn-secondary">
                Regenerate Interpretation
              </button>
            </article>
          )}
        </section>
      </main>
    </div>
  );
}

// Ensure Mount Logic exists so Vite loads the component into index.html
const rootElement = document.getElementById('root');
if (rootElement && !rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
