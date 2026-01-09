import React, { useState } from 'react';
import './App.css';
import TerminalComponent from './Terminal';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [logs, setLogs] = useState('');

  const submitRepo = async () => {
    if (!repoUrl.trim()) {
      setError('Please enter a GitHub repository URL');
      return;
    }

    setLoading(true);
    setError(null);
    setStatus(null);
    setLogs('');

    try {
      const response = await fetch(`${API_URL}/api/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo_url: repoUrl }),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit: ${response.statusText}`);
      }

      const data = await response.json();
      setTaskId(data.task_id);
      setStatus(data.status);

      // Poll for status
      pollStatus(data.task_id);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const pollStatus = async (id) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/status/${id}`);
        if (!response.ok) {
          throw new Error('Failed to get status');
        }

        const data = await response.json();
        setStatus(data.status);
        setLogs(data.logs || '');

        if (data.status === 'success') {
          clearInterval(pollInterval);
          setLoading(false);
          setSessionId(data.session_id);
        } else if (data.status === 'failed') {
          clearInterval(pollInterval);
          setLoading(false);
          setError('Build failed. Check logs for details.');
        }
      } catch (err) {
        clearInterval(pollInterval);
        setError(err.message);
        setLoading(false);
      }
    }, 2000);

    // Clear interval after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  const stopSession = async () => {
    if (!sessionId) return;

    try {
      await fetch(`${API_URL}/api/sessions/${sessionId}`, {
        method: 'DELETE',
      });
      
      setSessionId(null);
      setTaskId(null);
      setStatus(null);
      setLogs('');
      setRepoUrl('');
    } catch (err) {
      setError(`Failed to stop session: ${err.message}`);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>TestIt - Ephemeral Container Build System</h1>
        <p>Submit a GitHub repository to build and run it in an ephemeral container</p>
      </header>

      <div className="container">
        {!sessionId ? (
          <div className="submit-section">
            <div className="input-group">
              <input
                type="text"
                placeholder="https://github.com/username/repository"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && submitRepo()}
                disabled={loading}
              />
              <button onClick={submitRepo} disabled={loading}>
                {loading ? 'Processing...' : 'Submit Repository'}
              </button>
            </div>

            {error && (
              <div className="error-message">
                <strong>Error:</strong> {error}
              </div>
            )}

            {status && (
              <div className="status-section">
                <h3>Status: {status}</h3>
                {taskId && <p className="task-id">Task ID: {taskId}</p>}
                
                {logs && (
                  <div className="logs-section">
                    <h4>Build Logs:</h4>
                    <pre className="logs">{logs}</pre>
                  </div>
                )}
              </div>
            )}

            <div className="info-section">
              <h3>Supported Repositories:</h3>
              <ul>
                <li>Projects with a Dockerfile</li>
                <li>Python projects (requirements.txt)</li>
                <li>Node.js projects (package.json)</li>
              </ul>
              
              <h3>Features:</h3>
              <ul>
                <li>Automatic language detection</li>
                <li>Ephemeral containers (auto-destroyed after 60 minutes)</li>
                <li>Browser-based terminal access</li>
                <li>Resource limits: 2 CPU cores, 2GB RAM</li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="terminal-section">
            <div className="session-info">
              <h3>Session Active</h3>
              <p>Session ID: {sessionId}</p>
              <button onClick={stopSession} className="stop-button">
                Stop Session
              </button>
            </div>
            
            <TerminalComponent sessionId={sessionId} apiUrl={API_URL} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
