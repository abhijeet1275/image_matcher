import React, { useState } from 'react';
import axios from 'axios';
import ImageUploader from './components/ImageUploader';
import PromptInput from './components/PromptInput';
import Login from './components/Login';
import './App.css';

function App() {
    const [user, setUser] = useState(null);
    const [prompt, setPrompt] = useState('');
    const [images, setImages] = useState([]);
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [history, setHistory] = useState([]);
    const [showHistory, setShowHistory] = useState(false);

    const handleLogin = (userData) => {
        setUser(userData);
        loadHistory(userData.id);
    };

    const handleLogout = () => {
        setUser(null);
        setHistory([]);
        setResults([]);
    };

    const loadHistory = async (userId) => {
        try {
            const response = await axios.get(`http://localhost:5001/api/history/${userId}`);
            setHistory(response.data.matches);
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    };

    const deleteHistoryItem = async (matchId) => {
        try {
            await axios.delete(`http://localhost:5001/api/history/match/${matchId}`);
            loadHistory(user.id);
        } catch (err) {
            console.error('Failed to delete match:', err);
        }
    };

    const handlePromptChange = (newPrompt) => {
        setPrompt(newPrompt);
    };

    const handleImagesChange = (newImages) => {
        setImages(newImages);
        setResults([]);
        setError('');
    };

    const handleMatchImages = async () => {
        if (images.length === 0) {
            setError('Please upload at least one image.');
            return;
        }
        if (!prompt.trim()) {
            setError('Please enter a prompt.');
            return;
        }

        setError('');
        setLoading(true);
        setResults([]);

        try {
            const matchResults = await Promise.all(
                images.map(async (imageFile) => {
                    const formData = new FormData();
                    formData.append('image', imageFile);
                    formData.append('prompt', prompt);
                    if (user) {
                        formData.append('user_id', user.id);
                    }

                    try {
                        const response = await axios.post('http://localhost:5001/api/explain', formData, {
                            headers: {
                                'Content-Type': 'multipart/form-data',
                            },
                        });
                        return {
                            name: imageFile.name,
                            imageSrc: URL.createObjectURL(imageFile),
                            score: response.data.final_score,
                            explanation: response.data.explanation_text,
                            featureBreakdown: response.data.feature_breakdown,
                            status: 'success',
                            saved: response.data.saved,
                            matchId: response.data.match_id
                        };
                    } catch (err) {
                        console.error('API call failed for', imageFile.name, err);
                        return {
                            name: imageFile.name,
                            imageSrc: URL.createObjectURL(imageFile),
                            score: 'Error',
                            status: 'error',
                            errorMessage: err.response?.data?.error || 'Failed to process'
                        };
                    }
                })
            );

            setResults(matchResults);
            if (user) {
                loadHistory(user.id);
            }
        } catch (err) {
            setError('An unexpected error occurred while processing images.');
        } finally {
            setLoading(false);
        }
    };

    if (!user) {
        return (
            <div className="App">
                <div className="container">
                    <Login onLogin={handleLogin} />
                </div>
            </div>
        );
    }

    return (
        <div className="App">
            <div className="container">
                <div className="header-bar">
                    <h1>Image & Prompt Matcher</h1>
                    <div className="user-info">
                        <span>Welcome, {user.login_id}</span>
                        <button onClick={handleLogout} className="logout-btn">Logout</button>
                        <button onClick={() => setShowHistory(!showHistory)} className="history-btn">
                            {showHistory ? 'Hide History' : `Show History (${history.length})`}
                        </button>
                    </div>
                </div>

                <p className="subtitle">Upload multiple images and provide a text prompt to find the best matches.</p>

                {showHistory && (
                    <div className="history-panel">
                        <h3>Your Match History</h3>
                        <div className="history-list">
                            {history.length === 0 ? (
                                <p className="no-history">No match history yet. Start matching images!</p>
                            ) : (
                                history.map((item) => (
                                    <div key={item.id} className="history-item">
                                        <div className="history-content">
                                            <div className="history-image-wrapper">
                                                {item.stored_filename && (
                                                    <img
                                                        src={`http://localhost:5001/uploads/${item.stored_filename}`}
                                                        alt={item.image_filename}
                                                        className="history-thumbnail"
                                                        onError={(e) => {
                                                            e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"><rect fill="%23112240"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="%238892b0">No Image</text></svg>';
                                                        }}
                                                    />
                                                )}
                                            </div>
                                            <div className="history-details">
                                                <p className="history-filename">{item.image_filename}</p>
                                                <p className="history-prompt"><strong>Prompt:</strong> {item.prompt}</p>
                                                <p className="history-score">
                                                    <strong>Match Score:</strong>
                                                    <span className="score-badge">{item.match_score}%</span>
                                                </p>
                                                <p className="history-date">
                                                    {new Date(item.created_at).toLocaleString()}
                                                </p>

                                                <div className="history-explanation">
                                                    <button
                                                        className="view-explanation-btn"
                                                        onClick={() => {
                                                            const expDiv = document.getElementById(`hist-exp-${item.id}`);
                                                            expDiv.style.display = expDiv.style.display === 'none' ? 'block' : 'none';
                                                        }}
                                                    >
                                                        View Full Explanation
                                                    </button>
                                                    <div id={`hist-exp-${item.id}`} className="history-explanation-text" style={{ display: 'none' }}>
                                                        <pre>{item.explanation}</pre>
                                                        <div className="feature-breakdown">
                                                            <h4>Feature Breakdown:</h4>
                                                            {item.feature_breakdown.map((feature, idx) => (
                                                                <div key={idx} className={`feature-item ${feature.status}`}>
                                                                    <span className="feature-name">{feature.feature}</span>
                                                                    <span className="feature-score">{(feature.similarity * 100).toFixed(1)}%</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            className="delete-history-btn"
                                            onClick={() => {
                                                if (window.confirm('Delete this match history?')) {
                                                    deleteHistoryItem(item.id);
                                                }
                                            }}
                                        >
                                            🗑️ Delete
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                <PromptInput prompt={prompt} onPromptChange={handlePromptChange} />
                <ImageUploader onImagesChange={handleImagesChange} />

                {images.length > 0 && (
                    <p className="image-count">
                        {images.length} image{images.length !== 1 ? 's' : ''} selected
                    </p>
                )}

                <button onClick={handleMatchImages} disabled={loading}>
                    {loading ? `Matching ${images.length} image${images.length !== 1 ? 's' : ''}...` : 'Match Images'}
                </button>

                {error && <p className="error-message">{error}</p>}

                {results.length > 0 && (
                    <div className="results-section">
                        <h2>Results</h2>
                        <div className="results-grid">
                            {results.map((result, index) => (
                                <div key={index} className={`result-card ${result.status}`}>
                                    <img src={result.imageSrc} alt={result.name} />
                                    <p className="image-name">{result.name}</p>
                                    <p className="match-score">
                                        {result.status === 'success' ? (
                                            <>Match: <span className="score">{result.score}%</span></>
                                        ) : (
                                            <span className="error-text">Error: {result.errorMessage}</span>
                                        )}
                                    </p>
                                    {result.saved && <span className="saved-badge">✓ Saved to History</span>}

                                    {result.status === 'success' && result.explanation && (
                                        <div className="explanation-section">
                                            <button
                                                className="explain-btn"
                                                onClick={() => {
                                                    const card = document.getElementById(`explanation-${index}`);
                                                    card.style.display = card.style.display === 'none' ? 'block' : 'none';
                                                }}
                                            >
                                                View Explanation
                                            </button>
                                            <div id={`explanation-${index}`} className="explanation-text" style={{ display: 'none' }}>
                                                <pre>{result.explanation}</pre>

                                                {result.featureBreakdown && (
                                                    <div className="feature-breakdown">
                                                        <h4>Feature Breakdown:</h4>
                                                        {result.featureBreakdown.map((feature, fidx) => (
                                                            <div key={fidx} className={`feature-item ${feature.status}`}>
                                                                <span className="feature-name">{feature.feature}</span>
                                                                <span className="feature-score">{(feature.similarity * 100).toFixed(1)}%</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;