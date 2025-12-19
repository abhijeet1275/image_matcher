import React, { useState } from 'react';

function Login({ onLogin }) {
    const [loginId, setLoginId] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!loginId.trim()) {
            setError('Please enter a login ID');
            return;
        }

        try {
            const response = await fetch('http://localhost:5001/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ login_id: loginId }),
            });

            const data = await response.json();

            if (response.ok) {
                onLogin(data.user);
            } else {
                setError(data.error || 'Login failed');
            }
        } catch (err) {
            setError('Failed to connect to server');
        }
    };

    return (
        <div className="login-container">
            <h2>Login to Image Matcher</h2>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={loginId}
                    onChange={(e) => setLoginId(e.target.value)}
                    placeholder="Enter your login ID"
                    className="login-input"
                />
                <button type="submit" className="login-button">
                    Login / Register
                </button>
                {error && <p className="error-message">{error}</p>}
            </form>
        </div>
    );
}

export default Login;